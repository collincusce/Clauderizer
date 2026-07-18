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
import os
import shutil
import sys
from pathlib import Path
from typing import Callable

from .markdown.writer import refuse_if_symlink

# The runtime-home path suffix, under each platform's app-data root.
DAIMON_SUFFIX = ("kimi-desktop", "daimon-share", "daimon", "runtime", "kimi-code", "home")
MCP_JSON = "mcp.json"

WSL_USERS_DIR = Path("/mnt/c/Users")


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


def detect_config(*, home: Path | None = None, platform: str | None = None,
                  environ: dict | None = None, in_wsl: bool | None = None,
                  users_dir: Path = WSL_USERS_DIR) -> Path | None:
    """The daimon runtime-home ``mcp.json`` if the app is installed (its ``home/``
    dir already exists), else ``None`` — detected-only, never creating anything.
    Returns ``None`` when ``CLAUDERIZER_NO_KIMI_DESKTOP`` is set in ``environ``."""
    home = home or Path.home()
    platform = platform or sys.platform
    environ = environ if environ is not None else os.environ
    if environ.get(DISABLE_ENV):
        return None
    if in_wsl is None:
        in_wsl = bool(environ.get("WSL_DISTRO_NAME"))
    for cfg in candidate_configs(home=home, platform=platform, environ=environ,
                                 in_wsl=in_wsl, users_dir=users_dir):
        if cfg.parent.is_dir():                       # the daimon 'home/' dir exists
            return cfg
    return None


def _is_windows_side(cfg: Path, users_dir: Path) -> bool:
    """Is ``cfg`` a Windows-mounted config seen from WSL (under /mnt/.../Users)?"""
    try:
        return cfg.is_relative_to(users_dir)
    except ValueError:
        return False


_ARGS = ["--from", "clauderizer[mcp]", "clauderizer-mcp"]

# The Windows-native console script the daimon runtime must launch. kimi-desktop
# bundles uv.exe but NOT uvx.exe (verified 2026-07-17), so a bare ``uvx`` can never
# spawn on Windows — the absolute path to this .exe is the verified-good command
# (MCP initialize returns serverInfo clauderizer). D-055.
_WIN_EXE = "clauderizer-mcp.exe"

# Per-user roots under the Windows profile that hold clauderizer-mcp.exe, in
# priority order. ``.local\\bin`` doubles as uv's tool-bin dir (uv installs tool
# launchers there on every platform), so these two cover pipx AND uv tool installs.
_WIN_EXE_SUBPATHS = (
    ("pipx", "venvs", "clauderizer", "Scripts"),
    (".local", "bin"),
)


def _windows_profile_from_cfg(cfg: Path, users_dir: Path) -> tuple[Path, str] | None:
    """From a WSL-mounted Windows config path, derive ``(mnt_base, win_base)``:
    the ``/mnt/<drive>/Users/<user>`` directory THIS WSL host can stat, and the
    ``<DRIVE>:\\Users\\<user>`` spelling Windows will actually launch. ``None`` when
    ``cfg`` is not under the mounted Users dir."""
    try:
        rel = cfg.relative_to(users_dir)          # <user>/AppData/Roaming/...
    except ValueError:
        return None
    if not rel.parts:
        return None
    user = rel.parts[0]
    mnt_base = users_dir / user                   # /mnt/c/Users/<user>
    # users_dir ends in .../<drive>/Users → the drive is the segment before 'Users'
    drive = users_dir.parts[-2] if len(users_dir.parts) >= 2 else "c"
    win_base = f"{drive.upper()}:\\Users\\{user}"
    return mnt_base, win_base


def _win_exe_candidates(*, cfg: Path, platform: str, home: Path,
                        users_dir: Path) -> list[tuple[Path, str]]:
    """``(stat_path, command_str)`` candidates for a Windows-native
    clauderizer-mcp.exe, in priority order. ``stat_path`` is what the CURRENT host
    can check (a ``/mnt/c`` mirror from WSL, or a native Windows path); ``command_str``
    is the Windows-spelled absolute path to register."""
    out: list[tuple[Path, str]] = []
    if platform == "win32":                       # native Windows: stat == command
        for sub in _WIN_EXE_SUBPATHS:
            p = home.joinpath(*sub, _WIN_EXE)
            out.append((p, str(p)))
        return out
    prof = _windows_profile_from_cfg(cfg, users_dir)   # WSL → Windows-side config
    if prof is None:
        return out
    mnt_base, win_base = prof
    for sub in _WIN_EXE_SUBPATHS:
        stat_path = mnt_base.joinpath(*sub, _WIN_EXE)
        command = win_base + "\\" + "\\".join(sub) + "\\" + _WIN_EXE
        out.append((stat_path, command))
    return out


def server_entry(cfg: Path, *, in_wsl: bool, windows_side: bool | None = None,
                 platform: str | None = None, home: Path | None = None,
                 users_dir: Path = WSL_USERS_DIR,
                 exists: Callable[[Path], bool] | None = None,
                 which: Callable[[str], str | None] = shutil.which,
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
        for stat_path, command in _win_exe_candidates(
                cfg=cfg, platform=platform, home=home, users_dir=users_dir):
            if exists(stat_path):
                return ({"command": command, "args": []}, [])
        if platform == "win32":                   # last resort: PATH / uv tool dir
            found = which(_WIN_EXE) or which("clauderizer-mcp")
            if found:
                return ({"command": found, "args": []}, [])
        return (None,
                [f"no {_WIN_EXE} found for the Windows desktop (probed pipx venv "
                 "Scripts, .local\\bin / uv tool dir) — install clauderizer on Windows "
                 "(e.g. `pipx install \"clauderizer[mcp]\"`), then re-run `clauderize init`. "
                 "Wrote the setup guide instead of a command that cannot spawn"])
    uvx = which("uvx")
    if uvx is None:
        return ({"command": "uvx", "args": list(_ARGS)},
                ["uvx is not on PATH — wrote a bare 'uvx'; install uv so the server launches"])
    return ({"command": uvx, "args": list(_ARGS)}, [])


def _atomic_write_json(path: Path, data: dict) -> None:
    refuse_if_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)                             # atomic on POSIX and Windows


def merge_entry(cfg: Path, entry: dict) -> tuple[Path, bool]:
    """Non-destructively add/replace only the ``clauderizer`` server in ``cfg``,
    preserving every other server and top-level key. Atomic write, and idempotent:
    returns ``(cfg, changed)`` and skips the write when already current."""
    data: dict = {}
    if cfg.exists():
        try:
            loaded = json.loads(cfg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except json.JSONDecodeError:
            data = {}
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = data["mcpServers"] = {}
    if servers.get("clauderizer") == entry:
        return cfg, False                             # already current — no write
    servers["clauderizer"] = entry
    _atomic_write_json(cfg, data)
    return cfg, True


def remove_entry(cfg: Path) -> bool:
    """Uninstall: remove ONLY the ``clauderizer`` server from ``cfg``. Returns True
    if something was removed."""
    if not cfg.exists():
        return False
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or "clauderizer" not in servers:
        return False
    del servers["clauderizer"]
    _atomic_write_json(cfg, data)
    return True


def wire(*, home: Path | None = None, platform: str | None = None,
         environ: dict | None = None, in_wsl: bool | None = None,
         users_dir: Path = WSL_USERS_DIR,
         exists: Callable[[Path], bool] | None = None,
         which: Callable[[str], str | None] = shutil.which) -> dict:
    """Detect the daimon host and, if present, auto-write the clauderizer server
    (repo-agnostic). Returns ``{"status": "wired"|"not_detected"|"unregistrable"|
    "failed", "path", "entry", "changed", "windows_side", "warnings"}``. Never raises
    on a detected-but-unwritable config — reports it as a warning so doctor/init
    surface it loudly, not die. ``unregistrable`` = the app is installed but no
    launchable command could be composed (e.g. Windows host with no
    clauderizer-mcp.exe); the caller drops the setup guide instead of a dead entry."""
    environ = environ if environ is not None else os.environ
    if in_wsl is None:
        in_wsl = bool(environ.get("WSL_DISTRO_NAME"))
    cfg = detect_config(home=home, platform=platform, environ=environ,
                        in_wsl=in_wsl, users_dir=users_dir)
    if cfg is None:
        return {"status": "not_detected", "path": None, "entry": None, "warnings": []}
    windows_side = in_wsl and _is_windows_side(cfg, users_dir)
    entry, warnings = server_entry(cfg, in_wsl=in_wsl, windows_side=windows_side,
                                   platform=platform, home=home, users_dir=users_dir,
                                   exists=exists, which=which)
    if entry is None:
        return {"status": "unregistrable", "path": cfg, "entry": None,
                "windows_side": windows_side, "warnings": warnings}
    try:
        _, changed = merge_entry(cfg, entry)
    except OSError as exc:
        return {"status": "failed", "path": cfg, "entry": entry, "windows_side": windows_side,
                "warnings": warnings + [f"could not write {cfg}: {exc}"]}
    return {"status": "wired", "path": cfg, "entry": entry, "changed": changed,
            "windows_side": windows_side, "warnings": warnings}


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
not probe). Add the `clauderizer` server to the runtime-home `mcp.json`:

- **Windows:** `%APPDATA%\\{suffix.replace('/', chr(92))}`
- **macOS:** `~/Library/Application Support/{suffix}`
- **Linux:** `~/.config/{suffix}`
- **Repo in WSL, app on Windows:** the file is under
  `/mnt/c/Users/<you>/AppData/Roaming/{suffix}` — and the command must run the
  server back inside WSL (see the wsl.exe form below).

```json
{{
  "mcpServers": {{
    "clauderizer": {{ "command": "uvx", "args": ["--from", "clauderizer[mcp]", "clauderizer-mcp"] }}
  }}
}}
```

This entry is **repo-agnostic** — the server serves whichever repo you open in the
app (it reads the app's working directory), so one entry covers every repo. If
`uvx` is not on the desktop runtime's PATH, use its absolute path as `command`.
You can override `CLAUDERIZER_NO_KIMI_DESKTOP=1` to skip this auto-registration.

MCP servers load at **session start** — restart the desktop app (or open a new
session) after editing. Preserve any other servers already in the file.

## If your shell and MCP tools are failing (repo in WSL, app on Windows)

**This is for the agent reading this file.** If you are running in the Kimi Work
desktop app, every shell command fails with `spawn …bash.exe ENOENT`, and the
`cz_*` MCP tools never appear — the cause is **not** a missing shell. Your repo
lives in WSL, so the app sees it as a `\\\\wsl.localhost\\...` **UNC path**, and
**Windows cannot start a process with a UNC working directory** (`cmd.exe` itself
says *"UNC paths are not supported"*). So both the shell and the `uvx` MCP server
fail to spawn. A wsl.exe-wrapped command does **not** help — it dies on the same
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

(The underlying limitation is the desktop app spawning Windows processes with a UNC
cwd; the real fix is for it to execute via `wsl.exe` inside the distro.)
"""
