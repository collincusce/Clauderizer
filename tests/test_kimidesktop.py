"""kimi-desktop (daimon runtime) auto-write host (D-053) — the one deliberate
D-031 exception. Every path/command is exercised against an INJECTED temp home,
never a real ~/.config or %APPDATA% (L-29). The write is proven non-destructive
and detected-only in both directions (L-25)."""

import json

from clauderizer import kimidesktop as kd


def _make_home(base, cfg_path):
    """Create the daimon 'home/' dir (and an empty mcp.json) under a candidate."""
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text('{"mcpServers": {}}', encoding="utf-8")


def test_candidate_paths_per_platform(tmp_path):
    home = tmp_path / "home"
    suffix = "/".join(kd.DAIMON_SUFFIX) + "/" + kd.MCP_JSON
    win = kd.candidate_configs(home=home, platform="win32",
                               environ={"APPDATA": str(home / "AppData" / "Roaming")}, in_wsl=False)
    mac = kd.candidate_configs(home=home, platform="darwin", environ={}, in_wsl=False)
    lin = kd.candidate_configs(home=home, platform="linux", environ={}, in_wsl=False)
    assert str(win[0]).endswith(("AppData/Roaming/" + suffix).replace("/", __import__("os").sep))
    assert (home / "Library" / "Application Support").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON) == mac[0]
    assert (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON) == lin[0]


def test_detect_only_when_home_dir_exists(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    # nothing on disk yet -> not detected (never creates the app dir)
    assert kd.detect_config(home=home, platform="linux", environ={}, in_wsl=False) is None
    _make_home(home, cfg)
    assert kd.detect_config(home=home, platform="linux", environ={}, in_wsl=False) == cfg


def test_wire_autowrites_non_destructively(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    res = kd.wire(tmp_path / "repo", home=home, platform="linux", environ={},
                  in_wsl=False, which=lambda n: "/usr/bin/uvx")
    assert res["status"] == "wired" and res["path"] == cfg
    servers = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert servers["other"] == {"command": "x"}                 # preserved
    assert servers["clauderizer"]["command"] == "/usr/bin/uvx"  # absolute uvx
    assert servers["clauderizer"]["args"] == ["--from", "clauderizer[mcp]", "clauderizer-mcp"]


def test_wire_not_detected_when_app_absent(tmp_path):
    res = kd.wire(tmp_path / "repo", home=tmp_path / "home", platform="linux",
                  environ={}, in_wsl=False)
    assert res["status"] == "not_detected" and res["path"] is None


def test_wsl_windows_side_emits_wslexe_wrapper(tmp_path):
    users = tmp_path / "mnt-c-Users"
    cfg = (users / "me" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(users, cfg)
    res = kd.wire(tmp_path / "repo", home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, distro="Ubuntu",
                  users_dir=users)
    assert res["status"] == "wired" and res["path"] == cfg      # picked the Windows-side config
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["command"] == "wsl.exe"
    assert entry["args"][:3] == ["-d", "Ubuntu", "-e"]
    assert "clauderizer[mcp]" in entry["args"][-1] and "/repo" in entry["args"][-1]


def test_wire_warns_when_uvx_missing(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    res = kd.wire(tmp_path / "repo", home=home, platform="linux", environ={},
                  in_wsl=False, which=lambda n: None)            # uvx not on PATH
    assert res["status"] == "wired"
    assert any("uvx is not on PATH" in w for w in res["warnings"])   # loud, not silent


def test_remove_entry_is_surgical(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    kd.wire(tmp_path / "repo", home=home, platform="linux", environ={}, in_wsl=False)
    data = json.loads(cfg.read_text(encoding="utf-8")); data["mcpServers"]["keep"] = {"command": "y"}
    cfg.write_text(json.dumps(data), encoding="utf-8")
    assert kd.remove_entry(cfg) is True
    servers = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert "clauderizer" not in servers and servers["keep"] == {"command": "y"}
    assert kd.remove_entry(cfg) is False                         # idempotent


def test_atomic_write_leaves_no_tmp(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    kd.wire(tmp_path / "repo", home=home, platform="linux", environ={}, in_wsl=False)
    assert not (cfg.parent / (cfg.name + ".tmp")).exists()       # temp file renamed away
