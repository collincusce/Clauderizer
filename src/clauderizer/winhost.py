"""Windows/WSL command composition — host-agnostic primitives (D-056).

Extracted from the kimi-desktop wiring (D-055) so any bespoke auto-write host that
must launch a **Windows-native** clauderizer server can reuse it. Two jobs:

- **compose** the absolute path to a Windows-native ``clauderizer-mcp.exe`` for a
  daimon/desktop host that runs on Windows (the app may bundle ``uv.exe`` but not
  ``uvx.exe``, so a bare ``uvx`` can never spawn there — the ``.exe`` is the verified
  command), probing the per-user install locations;
- **translate** between the ``C:\\`` spelling Windows launches and the ``/mnt/<drive>``
  path a WSL vantage can stat/spawn (WSL interop), so ``init`` composing from WSL and
  ``doctor`` verifying from WSL both work.

Every function is pure and injectable (``platform``/``home``/``users_dir``) so tests
exercise it against a temp tree, never a real profile (L-29).
"""

from __future__ import annotations

import re
from pathlib import Path

# The Windows-native console script a Windows daimon/desktop host must launch. All
# clauderizer bespoke hosts serve the same MCP server, so this name is constant.
WIN_EXE = "clauderizer-mcp.exe"

# Per-user roots under the Windows profile that hold clauderizer-mcp.exe, in priority
# order. ``.local\\bin`` doubles as uv's tool-bin dir (uv installs tool launchers there
# on every platform), so these two cover pipx AND uv tool installs.
WIN_EXE_SUBPATHS = (
    ("pipx", "venvs", "clauderizer", "Scripts"),
    (".local", "bin"),
)


def win_path_to_wsl(win_path: str, *, mnt_root: Path = Path("/mnt")) -> Path | None:
    """``C:\\Users\\me\\x.exe`` → ``/mnt/c/Users/me/x.exe`` (WSL interop), else None."""
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", win_path)
    if not m:
        return None
    drive, rest = m.group(1).lower(), m.group(2).replace("\\", "/")
    return mnt_root / drive / rest


def windows_profile_from_cfg(cfg: Path, users_dir: Path) -> tuple[Path, str] | None:
    """From a WSL-mounted Windows config path, derive ``(mnt_base, win_base)``: the
    ``/mnt/<drive>/Users/<user>`` directory THIS WSL host can stat, and the
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


def win_exe_candidates(*, cfg: Path, platform: str, home: Path,
                       users_dir: Path) -> list[tuple[Path, str]]:
    """``(stat_path, command_str)`` candidates for a Windows-native
    clauderizer-mcp.exe, in priority order. ``stat_path`` is what the CURRENT host can
    check (a ``/mnt/c`` mirror from WSL, or a native Windows path); ``command_str`` is
    the Windows-spelled absolute path to register."""
    out: list[tuple[Path, str]] = []
    if platform == "win32":                       # native Windows: stat == command
        for sub in WIN_EXE_SUBPATHS:
            p = home.joinpath(*sub, WIN_EXE)
            out.append((p, str(p)))
        return out
    prof = windows_profile_from_cfg(cfg, users_dir)   # WSL → Windows-side config
    if prof is None:
        return out
    mnt_base, win_base = prof
    for sub in WIN_EXE_SUBPATHS:
        stat_path = mnt_base.joinpath(*sub, WIN_EXE)
        command = win_base + "\\" + "\\".join(sub) + "\\" + WIN_EXE
        out.append((stat_path, command))
    return out
