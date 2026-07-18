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


# --- D-055 Phase 1: Windows-native command composition (clauderizer-mcp.exe) -----
# A Windows desktop host (native win32, or WSL init detecting a /mnt/c Windows-side
# config) must register the ABSOLUTE path to a Windows-native clauderizer-mcp.exe —
# never a bare 'uvx' (uvx.exe is not bundled and can never spawn there).

def test_wsl_windows_side_registers_translated_exe(tmp_path):
    # repo in WSL, app on Windows: probe the /mnt/c mirror for the exe, register the
    # translated C:\ spelling (repo-agnostic, no cd). Never a WSL path, never bare uvx.
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(users, cfg)
    exe = users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")                        # the /mnt/c mirror of the exe
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users,
                  which=lambda n: "/home/me/.local/bin/uvx")     # WSL uvx must NOT be used
    assert res["status"] == "wired" and res["windows_side"] is True
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe",
                     "args": []}


def test_wsl_windows_side_unregistrable_without_exe(tmp_path):
    # No clauderizer-mcp.exe on the Windows side → unregistrable (caller drops the
    # guide); the config is NOT touched, and NO bare uvx is ever written.
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(users, cfg)
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users,
                  which=lambda n: "/home/me/.local/bin/uvx")
    assert res["status"] == "unregistrable" and res["entry"] is None
    assert res["windows_side"] is True
    assert "clauderizer" not in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert any("clauderizer-mcp.exe" in w for w in res["warnings"])
    assert not any("uvx" in w for w in res["warnings"])         # never suggests bare uvx for Windows


def test_win32_native_registers_exe(tmp_path):
    home = tmp_path / "winhome"
    cfg = (home / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    exe = home / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    res = kd.wire(home=home, platform="win32",
                  environ={"APPDATA": str(home / "AppData" / "Roaming")},
                  in_wsl=False, which=lambda n: None)
    assert res["status"] == "wired"
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": str(exe), "args": []}           # native: stat path == command


def test_win32_native_falls_back_to_which(tmp_path):
    # No exe in the probed per-user dirs, but one is on PATH / in the uv tool dir.
    home = tmp_path / "winhome"
    cfg = (home / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    res = kd.wire(home=home, platform="win32",
                  environ={"APPDATA": str(home / "AppData" / "Roaming")}, in_wsl=False,
                  which=lambda n: r"C:\tools\clauderizer-mcp.exe" if "clauderizer-mcp" in n else None)
    assert res["status"] == "wired"
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": r"C:\tools\clauderizer-mcp.exe", "args": []}


def test_server_entry_pinned_wsl_serving(tmp_path):
    # D-057: with a pin (UNC), compose {command: exe, args:[--repo, UNC], cwd: win_base}.
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    exe = users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    unc = r"\\wsl.localhost\Ubuntu\home\ccusce\clauderizer-site"
    entry, warns = kd.server_entry(cfg, in_wsl=True, windows_side=True, platform="linux",
                                   home=tmp_path / "linuxhome", users_dir=users, pin=unc)
    assert entry == {
        "command": r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe",
        "args": ["--repo", unc], "cwd": r"C:\Users\rafaj"}
    assert warns == []


def test_server_entry_unpinned_byte_identical(tmp_path):
    # No pin → the repo-agnostic entry is unchanged (no cwd, args:[]) — L-41/D-055 intact.
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    exe = users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    entry, _ = kd.server_entry(cfg, in_wsl=True, windows_side=True, platform="linux",
                               home=tmp_path / "linuxhome", users_dir=users)
    assert entry == {"command": r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe",
                     "args": []}
    assert "cwd" not in entry


def test_server_entry_pin_win32_native(tmp_path):
    home = tmp_path / "winhome"
    cfg = (home / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    exe = home / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    unc = r"\\wsl.localhost\Ubuntu\home\me\p"
    entry, _ = kd.server_entry(cfg, in_wsl=False, windows_side=False, platform="win32",
                               home=home, users_dir=tmp_path / "mnt" / "c" / "Users", pin=unc)
    assert entry == {"command": str(exe), "args": ["--repo", unc], "cwd": str(home)}


def test_server_entry_pin_ignored_on_non_windows(tmp_path):
    # A pin on a macOS/Linux daimon host is ignored (that host uses uvx, no UNC problem).
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    entry, _ = kd.server_entry(cfg, in_wsl=False, platform="linux",
                               which=lambda n: "/usr/bin/uvx", pin=r"\\wsl.localhost\U\x")
    assert entry == {"command": "/usr/bin/uvx",
                     "args": ["--from", "clauderizer[mcp]", "clauderizer-mcp"]}


def _pin_setup(tmp_path):
    """A detected WSL/windows-side daimon cfg + a fresh exe on the /mnt mirror."""
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    cfg.parent.mkdir(parents=True)
    exe = users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    return users, cfg


_UNC = r"\\wsl.localhost\Ubuntu\home\ccusce\clauderizer-site"
_FRESH_EXE = r"C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe"


def test_self_heal_preserves_existing_pin(tmp_path):
    # D-057 Phase 1: a pinned entry survives self-heal (never clobbered to args:[]).
    users, cfg = _pin_setup(tmp_path)
    cfg.write_text(json.dumps({"mcpServers": {"clauderizer": {
        "command": _FRESH_EXE, "args": ["--repo", _UNC], "cwd": r"C:\Users\rafaj"}}}),
        encoding="utf-8")
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users)
    assert res["status"] == "wired" and res["changed"] is False        # already current → no-op
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["args"] == ["--repo", _UNC] and entry["cwd"] == r"C:\Users\rafaj"


def test_self_heal_refreshes_stale_pin_exe_but_keeps_repo(tmp_path):
    # A pin whose exe path went stale (pipx reinstall) is refreshed to the current exe,
    # while the --repo pin is preserved.
    users, cfg = _pin_setup(tmp_path)
    cfg.write_text(json.dumps({"mcpServers": {"clauderizer": {
        "command": r"C:\Users\rafaj\OLD\clauderizer-mcp.exe",
        "args": ["--repo", _UNC], "cwd": r"C:\Users\rafaj"}}}), encoding="utf-8")
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users)
    assert res["status"] == "wired" and res["changed"] is True         # exe refreshed → wrote
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["command"] == _FRESH_EXE                              # fresh exe
    assert entry["args"] == ["--repo", _UNC]                           # pin PRESERVED


def test_self_heal_leaves_unpinned_entry_repo_agnostic(tmp_path):
    # No --repo and no sidecar → self-heal composes the repo-agnostic entry, unchanged.
    users, cfg = _pin_setup(tmp_path)
    cfg.write_text('{"mcpServers": {"clauderizer": {"command": "stale", "args": []}}}',
                   encoding="utf-8")
    kd.wire(home=tmp_path / "linuxhome", platform="linux",
            environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users)
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": _FRESH_EXE, "args": []} and "cwd" not in entry


def test_serve_pin_sidecar_roundtrip(tmp_path):
    _, cfg = _pin_setup(tmp_path)
    assert kd.read_serve_pin(cfg) is None
    assert kd.serve_pin_path(cfg).name == "clauderizer-serve.json"
    kd.write_serve_pin(cfg, _UNC)
    assert kd.read_serve_pin(cfg) == _UNC
    assert kd.clear_serve_pin(cfg) is True
    assert kd.read_serve_pin(cfg) is None
    assert kd.clear_serve_pin(cfg) is False                            # idempotent


def test_self_heal_composes_pin_from_sidecar_after_app_wipe(tmp_path):
    # C-01: the app wiped mcp.json to {} — the durable sidecar makes self-heal re-compose
    # the pin (the entry alone couldn't, since there's no --repo left to read).
    users, cfg = _pin_setup(tmp_path)
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")             # app-regenerated (wiped)
    kd.write_serve_pin(cfg, _UNC)                                      # durable pin sidecar
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users)
    assert res["status"] == "wired" and res["changed"] is True
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry == {"command": _FRESH_EXE, "args": ["--repo", _UNC], "cwd": r"C:\Users\rafaj"}


def test_win32_native_unregistrable_without_exe(tmp_path):
    home = tmp_path / "winhome"
    cfg = (home / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    res = kd.wire(home=home, platform="win32",
                  environ={"APPDATA": str(home / "AppData" / "Roaming")},
                  in_wsl=False, which=lambda n: None)
    assert res["status"] == "unregistrable" and res["entry"] is None
    assert "clauderizer" not in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert any("clauderizer-mcp.exe" in w for w in res["warnings"])


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
    entry, _ = kd.server_entry(cfg, in_wsl=False, platform="linux",
                               which=lambda n: "/usr/bin/uvx")
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
    # Patch the registered host's lifecycle methods (the framework routes through them,
    # D-056): force detection to this cfg, and pin composition to a deterministic entry
    # regardless of the CI host OS (per-platform composition is unit-tested separately),
    # so these init/doctor/uninstall plumbing tests stay green on the Windows CI leg
    # (L-23) where no clauderizer-mcp.exe exists.
    monkeypatch.setattr(kd._HOST, "detect_config", lambda **kw: cfg)
    monkeypatch.setattr(kd._HOST, "compose_entry",
                        lambda *a, **k: ({"command": "clauderizer-mcp", "args": []}, []))
    # doctor now handshakes any registered host; default it to a benign ok so these
    # plumbing tests don't spawn a real process (the handshake tests override this).
    from clauderizer import mcp_probe
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "ok", "server_name": "clauderizer", "server_version": None})


def test_init_autowrites_desktop_when_detected(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]


def test_init_is_silent_noop_when_desktop_absent(empty_python_repo, monkeypatch):
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd._HOST, "detect_config", lambda **kw: None)
    init(empty_python_repo, spawn_test=False)                    # no crash
    # no guide littered into a repo whose user doesn't have the app
    assert not (empty_python_repo / ".clauderizer" / "kimi-desktop-mcp-setup.md").exists()


def test_init_drops_guide_on_unregistrable(empty_python_repo, monkeypatch):
    # App detected on a Windows host but no clauderizer-mcp.exe → init drops the
    # setup guide (agent can read its way out) instead of a dead/bare-uvx entry.
    # init iterates BESPOKE_HOSTS and calls host.wire() (D-056), so patch _HOST.wire.
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd._HOST, "wire", lambda **kw: {
        "status": "unregistrable",
        "path": "/mnt/c/Users/rafaj/AppData/Roaming/.../mcp.json",
        "entry": None, "unservable": None,
        "warnings": ["no clauderizer-mcp.exe found for the Windows desktop"]})
    init(empty_python_repo, spawn_test=False)
    guide = empty_python_repo / ".clauderizer" / "kimi-desktop-mcp-setup.md"
    assert guide.is_file()


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


# --- D-055 Phase 2: self-healing registration on every write-permitted entry -----
# The app regenerates its mcp.json on project switch and merges from no persistent
# source (O-01), so the entry must be re-applied whenever clauderizer runs.

def test_self_heal_reapplies_wiped_entry(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    kw = dict(home=home, platform="linux", environ={}, in_wsl=False,
              which=lambda n: "/usr/bin/uvx")
    assert kd.self_heal(**kw)["changed"] is True                 # first apply
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")        # app wipes it on switch
    r2 = kd.self_heal(**kw)
    assert r2["status"] == "wired" and r2["changed"] is True      # re-applied
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert kd.self_heal(**kw)["changed"] is False                 # now current → no-op


def test_self_heal_respects_opt_out(tmp_path):
    home = tmp_path / "home"
    cfg = (home / ".config").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(home, cfg)
    r = kd.self_heal(home=home, platform="linux",
                     environ={kd.DISABLE_ENV: "1"}, in_wsl=False)
    assert r["status"] == "not_detected"
    assert json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"] == {}   # untouched


def test_self_heal_never_raises(monkeypatch, tmp_path):
    def boom(**kw):
        raise RuntimeError("disk gone")
    monkeypatch.setattr(kd._HOST, "wire", boom)                  # framework routes here
    r = kd.self_heal(home=tmp_path)                               # must not propagate
    assert r["status"] == "failed" and "disk gone" in r["warnings"][0]


def test_cmd_status_self_heals_wiped_entry(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer import cli
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")        # app regenerated the file
    monkeypatch.chdir(empty_python_repo)
    cli.main(["status"])
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]


def test_cmd_doctor_self_heals_and_reports(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    assert "clauderizer" in json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]
    assert "re-applied" in capsys.readouterr().out               # surfaced the heal


# --- D-055/D-056: doctor wires the MCP handshake into the kimi-desktop check -------
# The handshake primitive itself lives in mcp_probe (tests/test_mcp_probe.py); here we
# assert doctor's INTEGRATION of it (fail→drift, ok→green, version-skew→advisory). The
# probe is patched on clauderizer.mcp_probe, which cmd_doctor imports.

def test_doctor_fails_when_handshake_fails(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli, mcp_probe
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "fail", "detail": "dead engine behind the entry",
        "server_name": None, "server_version": None})
    monkeypatch.chdir(empty_python_repo)
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "initialize handshake" in out and "dead engine" in out
    assert rc == 2                                               # a failed handshake is drift


def test_doctor_passes_when_handshake_ok(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli, mcp_probe
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "initialize → serverInfo clauderizer 1.10.0",
        "server_name": "clauderizer", "server_version": "1.10.0"})
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    assert "✓ kimi-desktop MCP initialize handshake" in capsys.readouterr().out


def test_doctor_flags_version_skew_as_advisory(empty_python_repo, monkeypatch, tmp_path, capsys):
    # A green handshake against a DIFFERENT-version desktop install is advisory
    # (the exe is a separate Windows pipx install), not drift — so warn, don't fail.
    from clauderizer import cli, mcp_probe
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "initialize → serverInfo clauderizer 0.0.1",
        "server_name": "clauderizer", "server_version": "0.0.1"})
    monkeypatch.chdir(empty_python_repo)
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "kimi-desktop MCP version" in out and "0.0.1" in out
    assert rc != 2                                              # advisory, not drift


# --- D-057 Phase 2: init --serve-wsl-here + pinned doctor/uninstall --------------

def test_init_serve_wsl_here_writes_pin_sidecar(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer import winhost
    from clauderizer.scaffold.init import init
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(kd._HOST, "detect_config", lambda **kw: cfg)
    monkeypatch.setattr(kd, "detect_config", lambda **kw: cfg)     # module fn in init's pin block
    monkeypatch.setattr(kd, "_is_windows_side", lambda *a, **k: True)
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    init(empty_python_repo, spawn_test=False, serve_wsl_here=True)
    assert kd.read_serve_pin(cfg) == winhost.wsl_repo_to_unc(empty_python_repo, "Ubuntu")


def test_init_serve_wsl_here_noop_off_combo(empty_python_repo, monkeypatch):
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd, "detect_config", lambda **kw: None)     # app not detected
    monkeypatch.setattr(kd._HOST, "detect_config", lambda **kw: None)
    rep = init(empty_python_repo, spawn_test=False, serve_wsl_here=True)
    assert any("had no effect" in w for w in rep.warnings)


def test_doctor_reports_pinned_repo(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli, mcp_probe
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    kd.write_serve_pin(cfg, r"\\wsl.localhost\Ubuntu\home\ccusce\clauderizer-site")
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "ok", "server_name": "clauderizer", "server_version": None})
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "PINNED to serve" in out and "clauderizer-site" in out
    assert "EVERY project" in out                                  # the tradeoff, surfaced


def test_uninstall_clears_serve_pin(empty_python_repo, monkeypatch, tmp_path):
    from clauderizer.scaffold.init import init
    from clauderizer.scaffold.uninstall import uninstall
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    kd.write_serve_pin(cfg, r"\\wsl.localhost\Ubuntu\home\me\p")
    assert kd.read_serve_pin(cfg) is not None
    uninstall(empty_python_repo)
    assert kd.read_serve_pin(cfg) is None                          # sidecar cleared


# --- 1.9.1: the WSL/UNC agent-recovery playbook (D-054) --------------------------

def test_setup_guide_carries_recovery_playbook():
    g = kd.setup_guide()
    assert "UNC" in g and "wsl.localhost" in g                  # names the real cause
    assert "docs/" in g                                          # read memory directly (file tools work)
    assert "Windows filesystem" in g and "Kimi Code CLI" in g   # both permanent fixes


def test_setup_guide_carries_persistence_and_topology():
    # D-055 Phase 5: the guide documents the persistence finding, the per-topology
    # compositions, and the doctor smoke-test (a doc claim needs a test — L-55).
    g = kd.setup_guide()
    assert "regenerates its runtime" in g                # persistence finding
    assert "clauderizer-mcp.exe" in g                    # Windows-hosted composition
    assert "self-heal" in g.lower()                      # the durable workaround
    assert "initialize" in g and "serverInfo" in g       # doctor end-to-end smoke-test
    assert "uv.exe" in g and "not" in g                  # why bare uvx can't spawn on Windows


def test_setup_guide_references_repo_forward_path():
    # D-055 Phase 4: the guide names --repo / CLAUDERIZER_REPO as the forward path to
    # serving a UNC repo from a Windows-safe cwd.
    g = kd.setup_guide()
    assert "--repo" in g and "CLAUDERIZER_REPO" in g
    assert "Windows-safe cwd" in g


def test_wsl_combo_registration_is_not_dead(tmp_path):
    # D-055 Phase 4: for the WSL-repo + Windows-host combo, the repo-agnostic entry
    # is the working Windows .exe (serves Windows-hosted repos) — NOT a dead/bare-uvx
    # command — AND windows_side is flagged so the caller emits the UNC guidance.
    users = tmp_path / "mnt" / "c" / "Users"
    cfg = (users / "rafaj" / "AppData" / "Roaming").joinpath(*kd.DAIMON_SUFFIX, kd.MCP_JSON)
    _make_home(users, cfg)
    exe = users / "rafaj" / "pipx" / "venvs" / "clauderizer" / "Scripts" / "clauderizer-mcp.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    res = kd.wire(home=tmp_path / "linuxhome", platform="linux",
                  environ={"WSL_DISTRO_NAME": "Ubuntu"}, in_wsl=True, users_dir=users)
    assert res["status"] == "wired" and res["windows_side"] is True   # guidance path fires
    entry = json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["command"].endswith("clauderizer-mcp.exe") and entry["command"] != "uvx"


def test_doctor_wsl_combo_clarifies_registration_stands(empty_python_repo, monkeypatch, tmp_path, capsys):
    from clauderizer import cli, mcp_probe
    from clauderizer.scaffold.init import init
    cfg = tmp_path / "daimon" / "home" / "mcp.json"
    _detected(monkeypatch, cfg)
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(kd, "_is_windows_side", lambda *a, **k: True)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: {
        "status": "ok", "detail": "ok", "server_name": "clauderizer", "server_version": None})
    monkeypatch.chdir(empty_python_repo)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "UNC" in out and "still serves Windows-hosted repos" in out   # not "dead registration"


def test_init_emits_playbook_guide_on_wsl_combo(empty_python_repo, monkeypatch):
    # A wired-but-unservable host (WSL repo + Windows desktop) → init drops the guide.
    # init iterates BESPOKE_HOSTS and calls host.wire() (D-056), so patch _HOST.wire.
    from clauderizer.scaffold.init import init
    monkeypatch.setattr(kd._HOST, "wire", lambda **kw: {
        "status": "wired", "path": "/mnt/c/u/me/AppData/Roaming/.../mcp.json",
        "changed": True, "unservable": kd.UNC_GUIDANCE, "warnings": []})   # WSL cross-boundary
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
