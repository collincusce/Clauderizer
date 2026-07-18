"""Windows/WSL command composition primitives (winhost, D-056) — extracted from the
kimi-desktop wiring so any bespoke Windows host reuses them. Pure/injectable, exercised
against temp trees (L-29)."""

from pathlib import Path

from clauderizer import winhost as wh


def test_win_path_to_wsl_translates_drive():
    assert wh.win_path_to_wsl(r"C:\Users\me\x.exe") == Path("/mnt/c/Users/me/x.exe")
    assert wh.win_path_to_wsl(r"D:\a\b") == Path("/mnt/d/a/b")
    assert wh.win_path_to_wsl("/already/posix") is None          # not a Windows path
    assert wh.win_path_to_wsl("clauderizer-mcp") is None


def test_win_path_to_wsl_honors_mnt_root(tmp_path):
    got = wh.win_path_to_wsl(r"C:\x\y.exe", mnt_root=tmp_path / "mnt")
    assert got == tmp_path / "mnt" / "c" / "x" / "y.exe"


def test_windows_profile_from_cfg_derives_user_and_drive(tmp_path):
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = users / "rafaj" / "AppData" / "Roaming" / "app" / "mcp.json"
    mnt_base, win_base = wh.windows_profile_from_cfg(cfg, users)
    assert mnt_base == users / "rafaj"
    assert win_base == r"C:\Users\rafaj"


def test_windows_profile_from_cfg_none_when_outside_users(tmp_path):
    users = tmp_path / "mnt" / "c" / "Users"
    outside = tmp_path / "elsewhere" / "mcp.json"
    assert wh.windows_profile_from_cfg(outside, users) is None


def test_win_exe_candidates_native_win32(tmp_path):
    home = tmp_path / "winhome"
    cands = wh.win_exe_candidates(cfg=tmp_path / "unused", platform="win32",
                                  home=home, users_dir=tmp_path / "mnt" / "c" / "Users")
    # native: stat path == command path, pipx Scripts before .local\bin
    assert cands[0][0] == home / "pipx" / "venvs" / "clauderizer" / "Scripts" / wh.WIN_EXE
    assert cands[0][0] == Path(cands[0][1])
    assert cands[1][0] == home / ".local" / "bin" / wh.WIN_EXE


def test_win_exe_candidates_wsl_translates_to_windows_command(tmp_path):
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = users / "rafaj" / "AppData" / "Roaming" / "app" / "mcp.json"
    cands = wh.win_exe_candidates(cfg=cfg, platform="linux",
                                  home=tmp_path / "linuxhome", users_dir=users)
    stat0, cmd0 = cands[0]
    assert stat0 == users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / wh.WIN_EXE
    assert cmd0 == r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe"


def test_win_exe_candidates_wsl_empty_when_cfg_outside_users(tmp_path):
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = tmp_path / "not-under-users" / "mcp.json"
    assert wh.win_exe_candidates(cfg=cfg, platform="linux",
                                 home=tmp_path, users_dir=users) == []
