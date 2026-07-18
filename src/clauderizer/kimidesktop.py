"""kimi-desktop (daimon runtime) host — the one deliberate D-031 exception (D-053).

The Kimi Work desktop app embeds kimi-code via a "daimon" runtime and loads MCP
servers ONLY from its per-user runtime-home ``mcp.json`` — never the project
``.mcp.json`` or ``.kimi-code/mcp.json`` — and exposes no hook surface, so the MCP
server is the *only* orientation lane on that host. Clauderizer therefore
AUTO-WRITES that per-user config: the single sanctioned exception to
"global config → guide-only" (D-031), justified purely by UX.

The exception is kept narrow by three mitigations:

- **detected-only** — write only when the daimon runtime-home directory already
  exists (the app is installed); never create the app's dirs or a bogus config;
- **non-destructive + atomic** — merge only the ``clauderizer`` server, preserving
  every other entry, via temp-write + ``os.replace`` (never a half-written file);
- **robust, repo-agnostic command** — ``uvx --from clauderizer[mcp] clauderizer-mcp``
  (``uvx`` resolved to an absolute path when a thin desktop PATH would miss it). It
  is repo-agnostic on purpose — one per-user file serves every repo the app opens
  (C-01) — so it is never pinned to a repo with a ``cd`` wrapper. For a WSL-side repo
  the command runs on Windows, so a bare ``uvx`` is written (a WSL path would be
  wrong); note that a repo living only in WSL cannot actually be served from the
  Windows desktop app at all (UNC-cwd spawn limit, D-054 — the guide says so).

Because this config is machine-local (never committed), a machine-specific
``uvx`` path is fine here — the no-machine-paths rule (D-031) guards only
*committed* portable configs (L-48).

Everything that constructs a path or a command is a pure, injectable function so
tests exercise it against a temp home and never a real ``~/.config``/``%APPDATA%``
(L-29).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Callable

from . import bespoke_hosts, winhost
from .bespoke_hosts import BespokeHost

# The runtime-home path suffix, under each platform's app-data root.
DAIMON_SUFFIX = ("kimi-desktop", "daimon-share", "daimon", "runtime", "kimi-code", "home")
MCP_JSON = "mcp.json"

# Single-sourced from the framework (generic to any WSL vantage on a Windows host).
WSL_USERS_DIR = bespoke_hosts.WSL_USERS_DIR


def app_data_roots(home: Path, platform: str, environ: dict) -> list[Path]:
    """Per-OS app-data roots that may contain the daimon runtime home."""
    if platform == "win32":
        appdata = environ.get("APPDATA")
        return [Path(appdata)] if appdata else [home / "AppData" / "Roaming"]
    if platform == "darwin":
        return [home / "Library" / "Application Support"]
    # linux & friends: XDG config first, then the share dir
    xdg = environ.get("XDG_CONFIG_HOME")
    roots = [Path(xdg)] if xdg else [home / ".config"]
    roots.append(home / ".local" / "share")
    return roots


def wsl_windows_roots(users_dir: Path = WSL_USERS_DIR) -> list[Path]:
    """From inside WSL, the Windows desktop config lives under
    ``/mnt/c/Users/<user>/AppData/Roaming`` — return each existing candidate."""
    if not users_dir.is_dir():
        return []
    return [u / "AppData" / "Roaming" for u in sorted(users_dir.iterdir())
            if (u / "AppData" / "Roaming").is_dir()]


def candidate_configs(*, home: Path, platform: str, environ: dict, in_wsl: bool,
                      users_dir: Path = WSL_USERS_DIR) -> list[Path]:
    """Ordered candidate ``mcp.json`` paths (pure path construction, no FS reads
    except the WSL user enumeration). WSL→Windows candidates come first when in
    WSL, since that host takes precedence over any Linux-native daimon."""
    roots: list[Path] = []
    if in_wsl:
        roots += wsl_windows_roots(users_dir)
    roots += app_data_roots(home, platform, environ)
    return [r.joinpath(*DAIMON_SUFFIX, MCP_JSON) for r in roots]


# Opt-out env var: skip desktop detection/auto-write entirely. A real escape hatch
# for the one D-031 exception, and the guard the test suite sets so no test ever
# writes a real per-user daimon config (L-29).
DISABLE_ENV = "CLAUDERIZER_NO_KIMI_DESKTOP"


def detect_config(**kw) -> Path | None:
    """The daimon runtime-home ``mcp.json`` if the app is installed (its ``home/``
    dir already exists), else ``None`` — detected-only, never creating anything.
    Delegates to the framework host (``KimiDesktopHost``); kept as a module function
    for the existing callers/tests. Honors ``CLAUDERIZER_NO_KIMI_DESKTOP``."""
    return _HOST.detect_config(**kw)


def _is_windows_side(cfg: Path, users_dir: Path) -> bool:
    """Is ``cfg`` a Windows-mounted config seen from WSL (under /mnt/.../Users)?"""
    try:
        return cfg.is_relative_to(users_dir)
    except ValueError:
        return False


_ARGS = ["--from", "clauderizer[mcp]", "clauderizer-mcp"]

# Windows-native command composition (Windows/WSL path translation + clauderizer-mcp.exe
# probing) is the host-agnostic winhost primitive (D-056), reused by any bespoke host.


def server_entry(cfg: Path, *, in_wsl: bool, windows_side: bool | None = None,
                 platform: str | None = None, home: Path | None = None,
                 users_dir: Path = WSL_USERS_DIR,
                 exists: Callable[[Path], bool] | None = None,
                 which: Callable[[str], str | None] = shutil.which,
                 pin: str | None = None,
                 ) -> tuple[dict | None, list[str]]:
    """The ``mcpServers['clauderizer']`` entry (or ``None``) + any warnings.

    The entry is **repo-agnostic** on purpose (L-58): the daimon config is one
    per-user file shared by every repo the desktop app opens, so the server must
    discover the *open* repo from the app's working directory — never a ``cd <repo>``
    wrapper. Composition is host-topology-aware (D-055):

    - **Windows host** (init on win32, or WSL init detecting a ``/mnt/c`` Windows-side
      config): the command runs on Windows, where a bare ``uvx`` can never spawn
      (uv.exe is bundled, uvx.exe is not). Probe for a Windows-native
      ``clauderizer-mcp.exe`` (pipx Scripts, ``.local\\bin`` / uv tool dir) and register
      its **absolute** path with ``args: []``. From WSL, probe the ``/mnt/c`` mirror
      and register the translated ``C:\\`` spelling. If none is found, return
      ``(None, warning)`` — the caller drops the setup guide; we NEVER write a bare
      ``uvx`` for Windows.
    - **same-OS macOS/Linux**: resolve ``uvx`` to an absolute path when possible
      (a desktop runtime's PATH is often thin), else a bare ``uvx``.
    """
    platform = platform or sys.platform
    home = home or Path.home()
    exists = exists or (lambda p: Path(p).is_file())
    if windows_side is None:
        windows_side = _is_windows_side(cfg, users_dir)
    windows_host = platform == "win32" or (in_wsl and windows_side)
    if windows_host:
        exe: str | None = None
        for stat_path, command in winhost.win_exe_candidates(
                cfg=cfg, platform=platform, home=home, users_dir=users_dir):
            if exists(stat_path):
                exe = command
                break
        if exe is None and platform == "win32":   # last resort: PATH / uv tool dir
            exe = which(winhost.WIN_EXE) or which("clauderizer-mcp")
        if exe is None:
            return (None,
                    [f"no {winhost.WIN_EXE} found for the Windows desktop (probed pipx venv "
                     "Scripts, .local\\bin / uv tool dir) — install clauderizer on Windows "
                     "(e.g. `pipx install \"clauderizer[mcp]\"`), then re-run `clauderize init`. "
                     "Wrote the setup guide instead of a command that cannot spawn"])
        if pin:
            # Opt-in WSL-serving pin (D-057): spawn the exe from a Windows-safe cwd and
            # serve the pinned UNC repo via --repo (file I/O over UNC works; only the
            # process cwd may not be UNC). A single-repo pin in the per-user file.
            cwd = winhost.windows_safe_cwd(cfg, platform=platform, home=home, users_dir=users_dir)
            entry = {"command": exe, "args": ["--repo", pin]}
            if cwd:
                entry["cwd"] = cwd
            return (entry, [])
        return ({"command": exe, "args": []}, [])
    uvx = which("uvx")
    if uvx is None:
        return ({"command": "uvx", "args": list(_ARGS)},
                ["uvx is not on PATH — wrote a bare 'uvx'; install uv so the server launches"])
    return ({"command": uvx, "args": list(_ARGS)}, [])


# The guidance surfaced when the app is detected but can't serve THIS repo: a WSL repo
# opened on the Windows desktop, where the app spawns with a \\wsl.localhost UNC cwd it
# cannot use (D-054). The .exe entry still serves Windows-hosted repos; only this repo
# is unservable. Single-sourced here so init/doctor speak with one voice.
UNC_GUIDANCE = (
    "THIS repo is in WSL but the desktop app runs on Windows — the app spawns with a "
    "UNC (\\\\wsl.localhost) cwd it cannot use, so the shell and the MCP server fail to "
    "launch FOR THIS REPO (the registered entry still serves Windows-hosted repos). "
    "Clone the repo onto the Windows filesystem, or use Kimi Code CLI in WSL. "
    "See .clauderizer/kimi-desktop-mcp-setup.md")


def _existing_repo_pin(cfg: Path, servers_key: str) -> str | None:
    """The ``--repo <X>`` value in the current daimon entry, if it is pinned (D-057) —
    a same-session fallback so self-heal preserves a hand-applied pin. Not durable across
    the app's regenerate-to-{} wipe (C-01); that is what the sidecar below is for."""
    entry = bespoke_hosts.read_entry(cfg, servers_key=servers_key)
    args = (entry or {}).get("args") or []
    for i, a in enumerate(args):
        if a == "--repo" and i + 1 < len(args):
            return args[i + 1]
        if isinstance(a, str) and a.startswith("--repo="):
            return a[len("--repo="):]
    return None


# The opt-in WSL-serving pin is recorded in a per-user SIDECAR beside the daimon mcp.json
# (D-057, C-01). The app regenerates mcp.json on project switch but leaves this file, so
# self-heal re-composes the pin after a wipe — durability the entry itself can't provide.
SERVE_PIN_FILE = "clauderizer-serve.json"


def serve_pin_path(cfg: Path) -> Path:
    return cfg.parent / SERVE_PIN_FILE


def read_serve_pin(cfg: Path) -> str | None:
    """The pinned repo (a UNC path) recorded in the sidecar, or ``None``."""
    p = serve_pin_path(cfg)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    repo = data.get("repo") if isinstance(data, dict) else None
    return repo if isinstance(repo, str) and repo else None


def write_serve_pin(cfg: Path, repo_unc: str) -> Path:
    """Record the opt-in WSL-serving pin in the sidecar (atomic)."""
    bespoke_hosts._atomic_write_json(serve_pin_path(cfg), {"repo": repo_unc})
    return serve_pin_path(cfg)


def clear_serve_pin(cfg: Path) -> bool:
    """Remove the pin sidecar (unpin). True if it existed."""
    p = serve_pin_path(cfg)
    if p.exists():
        p.unlink()
        return True
    return False


class KimiDesktopHost(BespokeHost):
    """The first bespoke auto-write host (D-053/D-056): the Kimi Work desktop's daimon
    runtime, whose per-user ``mcp.json`` clauderizer auto-writes. Supplies only the
    variable parts; the detect/merge/self-heal lifecycle is inherited from BespokeHost."""

    id = "kimi-desktop"
    opt_out_env = DISABLE_ENV
    servers_key = "mcpServers"

    def candidate_configs(self, *, home, platform, environ, in_wsl, users_dir):
        return candidate_configs(home=home, platform=platform, environ=environ,
                                 in_wsl=in_wsl, users_dir=users_dir)

    def compose_entry(self, cfg, *, in_wsl, platform, home, users_dir, exists, which):
        windows_side = in_wsl and _is_windows_side(cfg, users_dir)
        # A deliberate WSL-serving pin (D-057) sourced from the durable sidecar (survives
        # the app's mcp.json wipe — C-01), falling back to an existing --repo in the entry
        # (a hand-applied pin, same-session). Either way self-heal recomposes it keeping
        # the repo but re-probing a fresh exe + cwd. No pin → the repo-agnostic path.
        pin = read_serve_pin(cfg) or _existing_repo_pin(cfg, self.servers_key)
        return server_entry(cfg, in_wsl=in_wsl, windows_side=windows_side, platform=platform,
                            home=home, users_dir=users_dir, exists=exists, which=which, pin=pin)

    def pinned_repo(self, cfg):
        # An opt-in WSL-serving pin (D-057) sourced from the sidecar (durable) or the
        # current entry's --repo (same-session).
        return read_serve_pin(cfg) or _existing_repo_pin(cfg, self.servers_key)

    def clear_pin(self, cfg):
        return clear_serve_pin(cfg)

    def unservable_reason(self, cfg, *, in_wsl, users_dir):
        # When pinned (D-057), the desktop serves the pinned repo — the UNC 'unservable'
        # guidance no longer applies (doctor reports which repo the pin serves instead).
        if self.pinned_repo(cfg):
            return None
        # A ``/mnt/.../Users`` config is a Windows-side daimon seen from WSL — only
        # possible under WSL, so ``_is_windows_side`` alone is the signal (the repo is
        # WSL-hosted, the app is on Windows, UNC-cwd spawn limit applies — D-054).
        return UNC_GUIDANCE if _is_windows_side(cfg, users_dir) else None

    def setup_guide(self):
        return setup_guide()


# The registered singleton. init/doctor/status/uninstall reach every bespoke host via
# bespoke_hosts.BESPOKE_HOSTS; these module functions stay for the existing callers/tests.
_HOST = bespoke_hosts.register(KimiDesktopHost())


def _compat(result: dict) -> dict:
    """Back-compat: expose the generic ``unservable`` reason as the legacy boolean
    ``windows_side`` key that init/doctor read on a detected daimon result."""
    if result.get("path") is not None:
        return {**result, "windows_side": result.get("unservable") is not None}
    return result


def merge_entry(cfg: Path, entry: dict) -> tuple[Path, bool]:
    """Non-destructively add/replace only the ``clauderizer`` server in ``cfg`` (the
    shared, atomic, idempotent merge). Delegates to the framework."""
    return bespoke_hosts.merge_entry(cfg, entry, servers_key="mcpServers")


def remove_entry(cfg: Path) -> bool:
    """Uninstall: remove ONLY the ``clauderizer`` server from ``cfg``. Delegates."""
    return bespoke_hosts.remove_entry(cfg, servers_key="mcpServers")


def wire(**kw) -> dict:
    """Detect the daimon host and, if present, auto-write the clauderizer server
    (repo-agnostic). ``{"status": "wired"|"not_detected"|"unregistrable"|"failed",
    "path", "entry", "changed", "windows_side", "warnings"}``. Never raises on a
    detected-but-unwritable config. Delegates to ``KimiDesktopHost``."""
    return _compat(_HOST.wire(**kw))


def self_heal(**kw) -> dict:
    """Best-effort re-apply of the daimon registration for the write-permitted CLI
    entry points (init/doctor/status) — the app regenerates its ``mcp.json`` on project
    switch (O-01). Idempotent, opt-out-aware, never raises. NOT from a hook (INVARIANT-06)
    or the MCP read path (L-03). Delegates to ``KimiDesktopHost``."""
    return _compat(_HOST.self_heal(**kw))


def setup_guide() -> str:
    """The fallback guide (kimi-desktop-mcp-setup.md) when the daimon runtime home
    is not detected — names the per-user path per OS and the manual entry."""
    suffix = "/".join(DAIMON_SUFFIX) + "/" + MCP_JSON
    return f"""# Clauderizer × Kimi Work desktop (daimon runtime) setup

The Kimi Work **desktop app** is a distinct host from the Kimi Code CLI: it loads
MCP servers only from its own per-user runtime-home config and reads **neither**
this repo's `.mcp.json` nor `.kimi-code/mcp.json`, and it has **no hook surface** —
so the MCP server is the *only* way it gets the Clauderizer tools and status.

`clauderize init` auto-registers the server there when it can detect the app; this
guide is for when it could not (the app wasn't installed yet, or on a path we did
not probe). The runtime-home `mcp.json` lives at:

- **Windows:** `%APPDATA%\\{suffix.replace('/', chr(92))}`
- **macOS:** `~/Library/Application Support/{suffix}`
- **Linux:** `~/.config/{suffix}`
- **Repo in WSL, app on Windows:** `/mnt/c/Users/<you>/AppData/Roaming/{suffix}`
  (the app runs on Windows, so the command must be a **Windows-native** one).

### The command is host-topology-specific

The entry is **repo-agnostic** — the server discovers whichever repo you open from
the app's working directory, so one entry covers every repo (never a `cd <repo>`
wrapper). What the `command` must be depends on where the app runs:

- **Windows-hosted repo (app on Windows).** The app bundles `uv.exe` but **not**
  `uvx.exe`, so a bare `uvx` can never spawn. Use the **absolute path** to a
  Windows-native `clauderizer-mcp.exe` (install with `pipx install "clauderizer[mcp]"`
  or `uv tool install "clauderizer[mcp]"`):

  ```json
  {{
    "mcpServers": {{
      "clauderizer": {{
        "command": "C:\\\\Users\\\\<you>\\\\pipx\\\\venvs\\\\clauderizer\\\\Scripts\\\\clauderizer-mcp.exe",
        "args": []
      }}
    }}
  }}
  ```

- **macOS / Linux (app and repo on the same OS).** Use the absolute path to `uvx`
  (a desktop runtime's PATH is often thin), or to `clauderizer-mcp`:

  ```json
  {{
    "mcpServers": {{
      "clauderizer": {{ "command": "/usr/bin/uvx", "args": ["--from", "clauderizer[mcp]", "clauderizer-mcp"] }}
    }}
  }}
  ```

- **WSL-hosted repo, app on Windows.** The desktop can serve any *Windows-hosted*
  repo via the `.exe` entry above, but it **cannot** serve a repo that lives only in
  WSL — see the UNC section below. Do not register a WSL/`wsl.exe` command here.

You can set `CLAUDERIZER_NO_KIMI_DESKTOP=1` to skip this auto-registration entirely.

### Persistence: the app regenerates this file

The desktop app **regenerates its runtime `mcp.json` on project/session switch** and
merges from **no** persistent user-level source (verified: neither `daimon-share/
config.toml` nor `daimon/config.json` carry MCP keys). So a hand-edit — or a one-shot
`clauderize init` — is **temporary**; the app can wipe it (leaving an `mcp.json.bak-*`)
when you open a different project. Clauderizer works around this by **self-healing**:
every `clauderize init`, `doctor`, and `status` re-applies the entry (idempotent — a
no-op when already current). So the durable fix is to run one of those from a WSL/OS
shell on the machine, and clauderizer re-applies the registration for the next
desktop session. `clauderize doctor` also **smoke-tests** the entry end-to-end (spawns
it and completes an MCP `initialize` handshake, asserting `serverInfo.name` is
`clauderizer`) — so a broken command fails loudly instead of looking registered.

MCP servers load at **session start** — restart the desktop app (or open a new
session) after editing. Preserve any other servers already in the file.

## If your shell and MCP tools are failing (repo in WSL, app on Windows)

**This is for the agent reading this file.** If you are running in the Kimi Work
desktop app, every shell command fails with `spawn …bash.exe ENOENT`, and the
`cz_*` MCP tools never appear — the cause is **not** a missing shell. Your repo
lives in WSL, so the app sees it as a `\\\\wsl.localhost\\...` **UNC path**, and
**Windows cannot start a process with a UNC working directory** (`cmd.exe` itself
says *"UNC paths are not supported"*). So both the shell and the MCP server (even the
Windows-native `clauderizer-mcp.exe`) fail to spawn — the cwd, not the command, is
what's rejected. A wsl.exe-wrapped command does **not** help — it dies on the same
UNC cwd. The bundled bash is fine; only process *spawning* is blocked.

**How to keep working right now** (file access still works over UNC):
- Read Clauderizer's memory directly — `docs/` is the source of truth (plain
  Markdown): `docs/VISION.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `INVARIANTS.md`,
  `LESSONS.md`, and `docs/gameplans/<id>/` for status/handoffs. Use your file
  (Read/Glob/Grep) tools with `\\\\wsl.localhost\\...` paths — those work.
- Do **not** rely on the `clauderize` CLI or any `bash`/build/test command — they
  cannot spawn this session. You can read and reason; you cannot execute or make
  tracked `cz_*` writes here.

**How to fix it for good** (pick one):
1. **Put the repo on the Windows filesystem** — e.g. clone it under
   `C:\\Users\\<you>\\Documents\\kimi\\workspace\\<repo>` (the app's own workspace). Then
   every spawn gets a normal Windows cwd, so the shell works and the `uvx` MCP
   server launches. WSL can still reach it at `/mnt/c/Users/<you>/…`.
2. **Use Kimi Code CLI *inside* WSL** for a WSL-hosted repo — no UNC anywhere, and
   the K3 model is available there too. This is the setup with zero of these issues.

**The forward path (not yet automatic).** `clauderizer-mcp` accepts `--repo <path>`
(or `$CLAUDERIZER_REPO`) to serve a repo other than its process cwd. So a desktop
that spawned the server from a **Windows-safe cwd** while passing
`--repo \\\\wsl.localhost\\<distro>\\home\\<you>\\<repo>` could serve a WSL-hosted repo
over UNC (file I/O over UNC works; only the process *cwd* may not be UNC). The daimon
entry is one repo-agnostic file shared by every repo the app opens, so clauderizer
can't bake a per-repo `--repo` there automatically — until the app exposes a
Windows-safe spawn cwd, use one of the two fixes above.

(The underlying limitation is the desktop app spawning Windows processes with a UNC
cwd; the real fix is for it to execute via `wsl.exe` inside the distro, or to spawn
from a Windows-safe cwd and pass `--repo` for the UNC repo.)
"""
