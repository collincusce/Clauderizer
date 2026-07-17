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
- **robust command** — ``uvx --from clauderizer[mcp] clauderizer-mcp`` with ``uvx``
  resolved to an absolute path when a thin desktop PATH would miss it, and wrapped
  in ``wsl.exe -d <distro> -e bash -lc 'cd <repo> && …'`` when init runs inside WSL
  against a Windows-side config (the common desktop-on-Windows + repo-in-WSL setup).

Because this config is machine-local (never committed), a machine-specific /
wsl.exe command is correct here — the no-machine-paths rule (D-031) guards only
*committed* portable configs (L-48).

Everything that constructs a path or a command is a pure, injectable function so
tests exercise it against a temp home and never a real ``~/.config``/``%APPDATA%``
(L-29).
"""

from __future__ import annotations

import json
import os
import shlex
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


def detect_config(*, home: Path | None = None, platform: str | None = None,
                  environ: dict | None = None, in_wsl: bool | None = None,
                  users_dir: Path = WSL_USERS_DIR) -> Path | None:
    """The daimon runtime-home ``mcp.json`` if the app is installed (its ``home/``
    dir already exists), else ``None`` — detected-only, never creating anything."""
    home = home or Path.home()
    platform = platform or sys.platform
    environ = environ if environ is not None else os.environ
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


def server_entry(repo_root: Path, cfg: Path, *, in_wsl: bool, distro: str | None,
                 windows_side: bool | None = None,
                 which: Callable[[str], str | None] = shutil.which) -> dict:
    """The ``mcpServers['clauderizer']`` entry for the daimon config.

    Windows/macOS/Linux native: ``uvx --from clauderizer[mcp] clauderizer-mcp``
    (uvx absolute when resolvable — a desktop runtime's PATH is often thin).
    WSL-in + Windows-side config: ``wsl.exe -d <distro> -e bash -lc 'cd <repo> &&
    uvx …'`` so the Windows-spawned server runs where uvx and the repo live.

    ``windows_side`` says whether ``cfg`` is a Windows-mounted config; when unset it
    falls back to a ``/mnt/`` prefix heuristic for direct callers.
    """
    if windows_side is None:
        windows_side = str(cfg).startswith("/mnt/")
    if in_wsl and windows_side and distro:
        inner = (f"cd {shlex.quote(repo_root.as_posix())} && "
                 "uvx --from 'clauderizer[mcp]' clauderizer-mcp")
        return {"command": "wsl.exe",
                "args": ["-d", distro, "-e", "bash", "-lc", inner]}
    uvx = which("uvx") or "uvx"
    return {"command": uvx, "args": ["--from", "clauderizer[mcp]", "clauderizer-mcp"]}


def _atomic_write_json(path: Path, data: dict) -> None:
    refuse_if_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)                             # atomic on POSIX and Windows


def merge_entry(cfg: Path, entry: dict) -> Path:
    """Non-destructively add/replace only the ``clauderizer`` server in ``cfg``,
    preserving every other server and top-level key. Atomic write."""
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
    servers["clauderizer"] = entry
    _atomic_write_json(cfg, data)
    return cfg


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


def wire(repo_root: Path, *, home: Path | None = None, platform: str | None = None,
         environ: dict | None = None, in_wsl: bool | None = None,
         distro: str | None = None, users_dir: Path = WSL_USERS_DIR,
         which: Callable[[str], str | None] = shutil.which) -> dict:
    """Detect the daimon host and, if present, auto-write the clauderizer server.

    Returns ``{"status": "wired"|"not_detected"|"failed", "path", "entry",
    "warnings"}``. Never raises on a detected-but-unwritable config — reports it as
    a warning so doctor/init can surface it loudly instead of dying (D-053)."""
    environ = environ if environ is not None else os.environ
    if in_wsl is None:
        in_wsl = bool(environ.get("WSL_DISTRO_NAME"))
    if distro is None:
        distro = environ.get("WSL_DISTRO_NAME")
    warnings: list[str] = []
    cfg = detect_config(home=home, platform=platform, environ=environ,
                        in_wsl=in_wsl, users_dir=users_dir)
    if cfg is None:
        return {"status": "not_detected", "path": None, "entry": None, "warnings": []}
    windows_side = in_wsl and _is_windows_side(cfg, users_dir)
    entry = server_entry(repo_root, cfg, in_wsl=in_wsl, distro=distro,
                         windows_side=windows_side, which=which)
    if entry["command"] == "uvx" and which("uvx") is None:
        warnings.append(
            "uvx is not on PATH — wrote a bare 'uvx' command; install uv or put uvx "
            "on the Kimi desktop runtime's PATH, or the server will not launch")
    if in_wsl and windows_side and not distro:
        warnings.append(
            "running in WSL against a Windows-side config but no WSL distro is known "
            "(WSL_DISTRO_NAME unset) — the command may not launch; re-run inside the distro")
    try:
        merge_entry(cfg, entry)
    except OSError as exc:
        return {"status": "failed", "path": cfg, "entry": entry,
                "warnings": warnings + [f"could not write {cfg}: {exc}"]}
    return {"status": "wired", "path": cfg, "entry": entry, "warnings": warnings}


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

If `uvx` is not on the desktop runtime's PATH, use its absolute path as `command`.
For a repo inside WSL, use instead:

```json
{{ "command": "wsl.exe",
   "args": ["-d", "<distro>", "-e", "bash", "-lc", "cd /path/to/repo && uvx --from 'clauderizer[mcp]' clauderizer-mcp"] }}
```

MCP servers load at **session start** — restart the desktop app (or open a new
session) after editing. Preserve any other servers already in the file.
"""
