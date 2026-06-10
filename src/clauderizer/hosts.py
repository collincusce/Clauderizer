"""Session-host-of-record: compose and verify wiring for the host that
actually spawns Claude Code sessions (gameplan agent-autonomy, D3).

H-04's root cause: wiring composed inside WSL was launched from Windows, and
the consuming host was recorded nowhere — so ``init`` could mis-compose a
shimmed command into an invalid subcommand and ``doctor`` stayed green for a
setup the real session host could not launch. This module closes the gap:

- ``parse``/``detect``: the session host vocabulary (``native`` |
  ``windows-wsl:<distro>``) and the adoption heuristic for existing wiring.
- ``compose``: wrap an engine-host argv in the ``wsl.exe`` shim when sessions
  spawn from Windows; pass through untouched for ``native``.
- ``spawn_probe``: actually execute a composed command with ``--version``
  before it is written anywhere. From inside WSL a ``wsl.exe`` command
  round-trips through Windows interop — the same binary the session host
  uses — so success is genuine cross-host proof, and "unverifiable" is
  reserved for hosts that truly cannot speak for the session host.
- ``verify_wiring``: doctor's launchability verdict for the recorded session
  host — pass, fail, or an honest ``unverifiable``, never a false green.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__

NATIVE = "native"
WSL_KIND = "windows-wsl"

# Generous: probes may round-trip through wsl.exe (~1-2s) or hit a cold uvx
# resolve (package download). A command that can't answer --version in a
# minute is not launchable wiring in any useful sense.
PROBE_TIMEOUT = 60.0


class SessionHostError(ValueError):
    """An invalid session-host value, with guidance. Raised by :func:`parse`."""


def parse(value: str | None) -> tuple[str, str | None]:
    """Validate a session-host string → ``(kind, distro)``.

    ``native``            → ("native", None)
    ``windows-wsl:ubuntu`` → ("windows-wsl", "ubuntu")
    """
    v = (value or NATIVE).strip()
    if v == NATIVE:
        return (NATIVE, None)
    if v == WSL_KIND or v.startswith(WSL_KIND + ":"):
        distro = v[len(WSL_KIND):].lstrip(":")
        if not distro:
            raise SessionHostError(
                f"session host '{v}' is missing the distro — use {WSL_KIND}:<distro> "
                f"(e.g. {WSL_KIND}:ubuntu)"
            )
        if any(c.isspace() for c in distro):
            raise SessionHostError(
                f"session host distro '{distro}' contains whitespace, which cannot survive "
                f"the hook's single-command-string wiring — use the distro's short name"
            )
        return (WSL_KIND, distro)
    raise SessionHostError(
        f"unknown session host '{v}' — expected '{NATIVE}' or '{WSL_KIND}:<distro>'"
    )


def running_inside_wsl() -> bool:
    return bool(os.environ.get("WSL_DISTRO_NAME"))


def current_distro() -> str | None:
    return os.environ.get("WSL_DISTRO_NAME")


def _is_wsl_exe(token: str) -> bool:
    return Path(token).name.lower() == "wsl.exe"


def is_wsl_shim(argv: list[str] | None) -> bool:
    """Does this wiring launch through the wsl.exe shim (a Windows session host)?"""
    return bool(argv) and bool(argv[0]) and _is_wsl_exe(argv[0])


def _distro_arg(argv: list[str]) -> str | None:
    """The ``-d``/``--distribution`` value in a wsl.exe argv, if present."""
    for i, tok in enumerate(argv[:-1]):
        if tok in ("-d", "--distribution"):
            return argv[i + 1]
    return None


def detect(existing_wiring: list[str] | None) -> str:
    """Heuristic session host when neither the init flag nor config says.

    Adopt the host the existing wiring already serves: a ``wsl.exe``-shimmed
    command was written for a Windows session host, and its ``-d`` argument
    names the distro of record (falling back to ``WSL_DISTRO_NAME``).
    Otherwise default to ``native`` — the explicit ``--session-host`` flag
    covers fresh split-host setups.
    """
    if existing_wiring and _is_wsl_exe(existing_wiring[0]):
        distro = _distro_arg(existing_wiring) or current_distro()
        if distro:
            return f"{WSL_KIND}:{distro}"
    return NATIVE


def read_wiring(mcp_json: Path) -> list[str] | None:
    """The clauderizer entry of ``.mcp.json`` as a full argv, if registered."""
    if not mcp_json.exists():
        return None
    import json

    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    entry = data.get("mcpServers", {}).get("clauderizer")
    if not entry:
        return None
    return [entry.get("command", ""), *entry.get("args", [])]


def compose(engine_argv: list[str], session_host: str) -> list[str]:
    """Wrap an engine-host launch argv for the session host of record.

    ``native`` passes through. ``windows-wsl:<distro>`` prepends the
    ``wsl.exe -d <distro>`` shim — unless the argv already begins with
    ``wsl.exe`` (an explicit ``--run-cmd`` shim), which is respected verbatim
    rather than double-wrapped.
    """
    kind, distro = parse(session_host)
    if kind == NATIVE or _is_wsl_exe(engine_argv[0]):
        return list(engine_argv)
    return ["wsl.exe", "-d", str(distro), *engine_argv]


# --- probing --------------------------------------------------------------------


@dataclass
class Probe:
    status: str  # "ok" | "fail" | "unverifiable"
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _decode(raw: bytes) -> str:
    """wsl.exe emits UTF-16LE diagnostics; everything else is UTF-8-ish."""
    if b"\x00" in raw:
        try:
            return raw.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def spawn_probe(argv: list[str] | None, *, timeout: float = PROBE_TIMEOUT,
                probe_arg: str = "--version") -> Probe:
    """Execute the composed command with a benign argument and judge the exit.

    This is the H-04 guard: a mis-composed invocation (e.g. ``clauderize
    clauderizer-mcp``) exits non-zero on ``--version`` and must never be
    written into wiring. ``wsl.exe`` commands probed from inside WSL
    round-trip through Windows interop — real cross-host evidence; without
    interop the verdict is honestly ``unverifiable``.
    """
    if not argv or not argv[0]:
        return Probe("fail", "no command registered")
    if _is_wsl_exe(argv[0]) and sys.platform != "win32":
        if shutil.which("wsl.exe") is None:
            return Probe(
                "unverifiable",
                "wsl.exe is not reachable from this host (no Windows interop) — "
                f"verify from the session host: `{' '.join([*argv, probe_arg])}`",
            )
    cmd = [*argv, probe_arg] if probe_arg else list(argv)
    shown = " ".join(cmd)
    try:
        r = subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL,
                           timeout=timeout)
    except FileNotFoundError:
        return Probe("fail", f"'{argv[0]}' not found on PATH or not executable")
    except subprocess.TimeoutExpired:
        return Probe("fail", f"spawn probe timed out after {timeout:.0f}s: `{shown}`")
    except OSError as exc:
        return Probe("fail", f"spawn failed for `{shown}`: {exc}")
    if r.returncode != 0:
        tail = _decode(r.stderr or r.stdout).strip()[-300:]
        return Probe("fail", f"exit {r.returncode} from `{shown}`"
                             + (f" — {tail}" if tail else ""))
    out = _decode(r.stdout).strip().splitlines()
    return Probe("ok", out[0] if out else f"`{shown}` exit 0")


# Both console entry points answer ``--version`` with exactly this shape
# (cli argparse, mcp_server.main, hook.sessionstart.main) — the round-trip
# probe's output is therefore an identity claim, not just an exit code.
_SERVED_VERSION_RE = re.compile(r"\bclauderizer (\d[^\s)]*)")


def served_version(probe_detail: str) -> str | None:
    """The engine version a probe's output claims, if it identifies itself.

    ``None`` for engines that predate the deterministic ``--version`` surface
    (pre-0.6.0 ``clauderizer-mcp`` exits 0 on EOF printing *nothing* — the
    lesson-#4 accident) and for wrapper breadcrumbs (a dead engine behind the
    D4 hook wrapper still exits 0, with the breadcrumb on stdout).
    """
    m = _SERVED_VERSION_RE.search(probe_detail)
    return m.group(1) if m else None


def _inner_target(argv: list[str]) -> str | None:
    """The engine-side executable inside a wsl.exe shim argv, if extractable."""
    rest = argv[1:]
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok in ("-d", "--distribution", "-u", "--user", "--cd"):
            i += 2
            continue
        if tok in ("-e", "--exec", "--"):
            i += 1
            continue
        return tok
    return None


def verify_wiring(argv: list[str] | None, session_host: str | None,
                  *, timeout: float = PROBE_TIMEOUT) -> Probe:
    """Doctor's launchability verdict for the recorded session host.

    ``native``: the probing host IS the host of record, so presence +
    executability suffices (the 0.5.0 standard). ``windows-wsl``: check the
    engine-side target path where possible, then certify end-to-end via the
    interop round-trip — or report ``unverifiable`` instead of guessing.
    """
    try:
        kind, distro = parse(session_host)
    except SessionHostError as exc:
        return Probe("fail", str(exc))
    if not argv or not argv[0]:
        return Probe("fail", "no clauderizer command registered")
    if kind == NATIVE:
        exe = argv[0]
        if shutil.which(exe):
            return Probe("ok", exe)
        p = Path(exe)
        if p.is_file() and os.access(p, os.X_OK):
            return Probe("ok", str(p))
        return Probe("fail", f"'{exe}' not found on PATH or not executable")
    # windows-wsl:<distro> — the wiring must launch via the wsl.exe shim.
    if not _is_wsl_exe(argv[0]):
        return Probe(
            "fail",
            f"session host of record is {session_host} but the command launches "
            f"'{argv[0]}' directly — Windows cannot spawn it; re-run `clauderize init`",
        )
    target = _inner_target(argv)
    here = current_distro()
    if target and here and distro and here.lower() == distro.lower():
        tp = Path(target)
        if not (tp.is_file() and os.access(tp, os.X_OK)):
            return Probe("fail", f"engine-side target '{target}' does not exist or is "
                                 f"not executable in this distro")
    probe = spawn_probe(argv, timeout=timeout)
    if probe.status == "ok":
        # Identity, not just launchability (D5, D9): exit 0 alone certified a
        # pinned-stale engine (pre-0.6.0 servers exit 0 on EOF) and even a DEAD
        # engine behind the D4 wrapper (breadcrumb on stdout, always exit 0).
        # The round-trip must claim the same version as the engine answering
        # this doctor, or the green verdict speaks for a different build than
        # sessions actually get.
        served = served_version(probe.detail)
        if served is None:
            return Probe(
                "fail",
                f"round-trip succeeded but the wiring did not identify its engine "
                f"(expected 'clauderizer {__version__}', got: {probe.detail or '<no output>'!r}) "
                f"— stale pre-0.6.0 pin or dead engine behind the hook wrapper; "
                f"update the pin or re-run `clauderize init`",
            )
        if served != __version__:
            return Probe(
                "fail",
                f"wiring serves clauderizer {served} but this doctor is {__version__} — "
                f"sessions on this repo run {served} (stale pin or cached build); "
                f"update the pin, clear the uvx cache, or re-run `clauderize init`",
            )
        return Probe("ok", f"verified end-to-end via wsl.exe round-trip ({probe.detail})")
    if probe.status == "unverifiable":
        detail = probe.detail
        if target and here and distro and here.lower() == distro.lower():
            detail = f"engine-side target OK; {detail}"
        return Probe("unverifiable", detail)
    return probe


# --- SessionStart hook wrapper (D4, H-01 residue) ---------------------------------
#
# The harness injects only a hook's STDOUT into session context; a hook whose
# command cannot spawn prints nothing there (verified live: a dead console
# script puts "not found" on stderr, stdout empty). The wrapper is the layer
# below the engine: it always spawns (only /bin/sh — or wsl.exe itself — can
# kill it, the documented boundary) and converts any engine failure into a
# stdout breadcrumb naming `clauderize doctor`.

BREADCRUMB_PREFIX = "[Clauderizer] engine unreachable:"
_ENGINE_LINE_SH = "# engine-hook: "
_ENGINE_LINE_CMD = "rem engine-hook: "

HOOK_WRAPPER_SH = "hook.sh"
HOOK_WRAPPER_CMD = "hook.cmd"


def is_hook_command(cmd: str) -> bool:
    """Is this registered SessionStart command ours — direct engine hook or
    wrapper? (init dedup and doctor share this matcher so they cannot drift.)"""
    return ("clauderizer-hook" in cmd
            or ".clauderizer/hook." in cmd
            or ".clauderizer\\hook." in cmd)


def wrapper_filename(session_host: str) -> str:
    """Which wrapper file serves this session host (cmd only for native win32)."""
    kind, _ = parse(session_host)
    if kind == NATIVE and sys.platform == "win32":
        return HOOK_WRAPPER_CMD
    return HOOK_WRAPPER_SH


def render_hook_wrapper(engine_hook_argv: list[str], *, windows: bool = False) -> str:
    """The wrapper script text, with the engine hook command baked in.

    Tokens are joined plainly — the same space-free constraint the one-string
    hook registration already imposes (documented boundary). "$@" forwarding
    keeps the wrapper transparent to --version probes.
    """
    joined = " ".join(engine_hook_argv)
    if windows:
        return (
            "@echo off\r\n"
            "rem [Clauderizer] SessionStart wrapper - regenerated by `clauderize init`; do not edit.\r\n"
            "rem A session whose engine cannot launch must still learn why (H-01).\r\n"
            f"{_ENGINE_LINE_CMD}{joined}\r\n"
            f"{joined} %*\r\n"
            f"if errorlevel 1 echo {BREADCRUMB_PREFIX} exit %errorlevel% "
            f"from {engine_hook_argv[0]} - run clauderize doctor\r\n"
            "exit /b 0\r\n"
        )
    return (
        "#!/bin/sh\n"
        "# [Clauderizer] SessionStart wrapper — regenerated by `clauderize init`; do not edit.\n"
        "# A session whose engine cannot launch must still learn why (H-01): any\n"
        "# engine failure becomes a breadcrumb on STDOUT (the session context).\n"
        f"{_ENGINE_LINE_SH}{joined}\n"
        f'out=$({joined} "$@" 2>&1)\n'
        "status=$?\n"
        'if [ "$status" -eq 0 ]; then\n'
        "  [ -n \"$out\" ] && printf '%s\\n' \"$out\"\n"
        "else\n"
        f"  printf '{BREADCRUMB_PREFIX} exit %s from %s — run `clauderize doctor`\\n%s\\n' \\\n"
        f'    "$status" "{engine_hook_argv[0]}" "$out"\n'
        "fi\n"
        "exit 0\n"
    )


def wrapper_engine_argv(wrapper_text: str) -> list[str] | None:
    """The engine hook argv baked into a wrapper — doctor's freshness anchor."""
    for line in wrapper_text.splitlines():
        for prefix in (_ENGINE_LINE_SH, _ENGINE_LINE_CMD):
            if line.startswith(prefix):
                rest = line[len(prefix):].strip()
                return rest.split() if rest else None
    return None


def hook_wrapper_invocation(root: Path, session_host: str) -> list[str]:
    """The command to REGISTER as the SessionStart hook: spawn the wrapper.

    native posix     -> /bin/sh <repo>/.clauderizer/hook.sh
    native win32     -> cmd /c <repo>\\.clauderizer\\hook.cmd
    windows-wsl:<d>  -> wsl.exe -d <d> /bin/sh <repo>/.clauderizer/hook.sh
                        (the wrapper runs engine-side: a Windows cmd wrapper
                        started in a \\\\wsl.localhost UNC cwd would warn into
                        every healthy session and resets cwd — strictly worse)
    """
    kind, _ = parse(session_host)
    if kind == NATIVE and sys.platform == "win32":
        return ["cmd", "/c", str(root / ".clauderizer" / HOOK_WRAPPER_CMD)]
    inner = ["/bin/sh", (root / ".clauderizer" / HOOK_WRAPPER_SH).as_posix()]
    return compose(inner, session_host)
