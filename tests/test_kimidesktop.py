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
    res = kd.wire(home=home, platform="linux", environ={},
                  in_wsl=False, which=lambda n: "/usr/bin/uvx")
    assert res["status"] == "wired" and res["path"] == cfg
    servers = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert servers["other"] == {"command": "x"}                 # preserved
    assert servers["clauderizer"]["command"] == "/usr/bin/uvx"  # absolute uvx
    assert servers["clauderizer"]["args"] == ["--from", "clauderizer[mcp]", "clauderizer-mcp"]


def test_wire_not_detected_when_app_absent(tmp_path):
    res = kd.wire(home=tmp_path / "home", platform="linux",
                  environ={}, in_wsl=False)
    assert res["status"] == "not_detected" and res["path"] is None


def test_wsl_windows_side_writes_bare_uvx_repo_agnostic(tmp_path):
    # repo in WSL, app on Windows: the command runs on Windows, so a WSL-absolute
    # path would be wrong — write a bare 'uvx' (repo-agnostic, no cd) + a loud warning.
    users = tmp_path / "mnt-c-Users"
    cfg = (users / "me" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(users, cfg)
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users,
                  which=lambda n: "/home/me/.local/bin/uvx")   # WSL uvx — must NOT be used
    assert res["status"] == "wired" and res["path"] == cfg      # picked the Windows-side config
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": "uvx", "args": ["--from", "clauderizer[mcp]", "clauderizer-mcp"]}
    assert any("Windows PATH" in w for w in res["warnings"])


def test_wire_warns_when_uvx_missing(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    res = kd.wire(home=home, platform="linux", environ={},
                  in_wsl=False, which=lambda n: None)            # uvx not on PATH
    assert res["status"] == "wired"
    assert any("uvx is not on PATH" in w for w in res["warnings"])   # loud, not silent


def test_remove_entry_is_surgical(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    kd.wire(home=home, platform="linux", environ={}, in_wsl=False)
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
    kd.wire(home=home, platform="linux", environ={}, in_wsl=False)
    assert not (cfg.parent / (cfg.name + ".tmp")).exists()       # temp file renamed away


def test_merge_is_idempotent(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    entry, _ = kd.server_entry(cfg, in_wsl=False, which=lambda n: "/usr/bin/uvx")
    _, first = kd.merge_entry(cfg, entry)
    _, second = kd.merge_entry(cfg, entry)
    assert first is True and second is False                     # second run = no write


def test_disable_env_guard_skips_detection(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    # present, but the opt-out env var makes it invisible (also the test-suite guard, L-29)
    assert kd.detect_config(home=home, platform="linux",
                            environ={kd.DISABLE_ENV: "1"}, in_wsl=False) is None


# --- Phase 2: init / doctor / uninstall integration -----------------------------

def _detected(monkeypatch, cfg):
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(kd, "detect_config", lambda **kw: cfg)


def test_init_autowrites_desktop_when_detected(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]


def test_init_is_silent_noop_when_desktop_absent(empty_python_repo, monkeypatch):
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd, "detect_config", lambda **kw: None)
    init(empty_python_repo, spawn_test=False)                    # no crash
    # no guide littered into a repo whose user doesn't have the app
    assert not (empty_python_repo / ".clauderizer" / "kimi-desktop-mcp-setup.md").exists()


def test_uninstall_removes_desktop_registration(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer.scaffold.init import init
    from clauderizer.scaffold.uninstall import uninstall
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    uninstall(empty_python_repo)
    assert "clauderizer" not in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]


def test_doctor_reports_desktop_host(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    assert "kimi-desktop" in capsys.readouterr().out            # surfaced in doctor


# --- 1.9.1: the WSL/UNC agent-recovery playbook (D-054) --------------------------

def test_setup_guide_carries_recovery_playbook():
    g = kd.setup_guide()
    assert "UNC" in g and "wsl.localhost" in g                  # names the real cause
    assert "docs/" in g                                          # read memory directly (file tools work)
    assert "Windows filesystem" in g and "Kimi Code CLI" in g   # both permanent fixes


def test_init_emits_playbook_guide_on_wsl_combo(empty_python_repo, monkeypatch):
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd, "wire", lambda **kw: {
        "status": "wired", "path": "/mnt/c/u/me/AppData/Roaming/.../mcp.json",
        "changed": True, "windows_side": True, "warnings": []})   # WSL cross-boundary
    init(empty_python_repo, spawn_test=False)
    guide = empty_python_repo / ".clauderizer" / "kimi-desktop-mcp-setup.md"
    assert guide.is_file() and "UNC" in guide.read_text(encoding="utf-8")   # agent can read its way out


def test_doctor_warns_on_wsl_combo(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(kd, "_is_windows_side", lambda *a, **k: True)   # force the WSL combo
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "UNC" in out and "Windows filesystem" in out         # loud, actionable
