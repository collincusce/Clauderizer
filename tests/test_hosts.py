"""agent-autonomy Phase 2 (D3): session-host-of-record.

H-04's regression suite: the session-host vocabulary, the wiring-adoption
heuristic, the composition matrix (native / windows-wsl), the spawn-test
guard that refuses mis-composed wiring BEFORE anything is written, and
doctor's host-aware three-state messaging (pass / fail / unverifiable —
never a false green).
"""

import json
import sys

import pytest

from clauderizer import cli, hosts
from clauderizer.config import Config
from clauderizer.scaffold.init import WiringRefused, init

# --- parse: the session-host vocabulary -----------------------------------------


def test_parse_native_and_default():
    assert hosts.parse("native") == ("native", None)
    assert hosts.parse(None) == ("native", None)
    assert hosts.parse("") == ("native", None)


def test_parse_windows_wsl():
    assert hosts.parse("windows-wsl:ubuntu") == ("windows-wsl", "ubuntu")


@pytest.mark.parametrize("bad", ["windows-wsl", "windows-wsl:", "windows-wsl:two words", "mac-vm:x"])
def test_parse_rejects_with_guidance(bad):
    with pytest.raises(hosts.SessionHostError):
        hosts.parse(bad)


# --- detection: adopt the host the existing wiring already serves ----------------


def test_detect_adopts_wsl_shimmed_wiring():
    wired = ["wsl.exe", "-d", "ubuntu", "/x/.venv/bin/clauderizer-mcp"]
    assert hosts.detect(wired) == "windows-wsl:ubuntu"


def test_detect_defaults_native():
    assert hosts.detect(None) == "native"
    assert hosts.detect(["/x/.venv/bin/clauderizer-mcp"]) == "native"


def test_detect_wsl_wiring_without_distro_uses_env(monkeypatch):
    monkeypatch.setenv("WSL_DISTRO_NAME", "Debian")
    assert hosts.detect(["wsl.exe", "/x/clauderizer-mcp"]) == "windows-wsl:Debian"
    monkeypatch.delenv("WSL_DISTRO_NAME")
    assert hosts.detect(["wsl.exe", "/x/clauderizer-mcp"]) == "native"  # cannot name a distro


# --- composition matrix ----------------------------------------------------------


def test_compose_native_passthrough():
    argv = ["/v/bin/clauderizer-mcp"]
    assert hosts.compose(argv, "native") == argv


def test_compose_wsl_shim():
    assert hosts.compose(["/v/bin/clauderizer-mcp"], "windows-wsl:ubuntu") == [
        "wsl.exe", "-d", "ubuntu", "/v/bin/clauderizer-mcp",
    ]


def test_compose_never_double_wraps():
    shim = ["wsl.exe", "-d", "ubuntu", "/v/bin/clauderizer-mcp"]
    assert hosts.compose(shim, "windows-wsl:ubuntu") == shim


# --- config round-trip -------------------------------------------------------------


def test_config_roundtrips_session_host(tmp_path):
    cfg = Config.for_size("standard", host_profile="python")
    assert cfg.session_host is None
    assert "session_host" not in cfg.to_toml()  # absent until an init records it
    cfg.session_host = "windows-wsl:ubuntu"
    f = tmp_path / "config.toml"
    f.write_text(cfg.to_toml(), encoding="utf-8")
    assert Config.load(f).session_host == "windows-wsl:ubuntu"
    f.write_text(Config.load(f).to_toml(), encoding="utf-8")  # apply-twice == apply-once
    assert Config.load(f).session_host == "windows-wsl:ubuntu"


# --- spawn probe (real spawns — the H-04 guard itself) ------------------------------


def test_spawn_probe_ok_on_real_command():
    p = hosts.spawn_probe([sys.executable, "-m", "clauderizer.cli"])
    assert p.status == "ok" and "clauderizer" in p.detail


def test_spawn_probe_fails_on_h04_shape():
    # The exact H-04 mis-composition: an entry-point name appended to a run-cmd
    # that already names the subcommand CLI -> `clauderize clauderizer-mcp`,
    # an invalid argparse subcommand (exit 2). The probe must fail it.
    p = hosts.spawn_probe([sys.executable, "-m", "clauderizer.cli", "clauderizer-mcp"])
    assert p.status == "fail" and "exit 2" in p.detail


def test_spawn_probe_fails_on_missing_binary():
    p = hosts.spawn_probe(["definitely-not-a-real-binary-xyz123"])
    assert p.status == "fail" and "not found" in p.detail


def test_spawn_probe_unverifiable_without_interop(monkeypatch):
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    p = hosts.spawn_probe(["wsl.exe", "-d", "ubuntu", "/x/clauderizer-mcp"])
    assert p.status == "unverifiable" and "wsl.exe" in p.detail


# --- verify_wiring: doctor's three-state verdict -------------------------------------


def test_verify_wiring_windows_host_rejects_unshimmed_command():
    p = hosts.verify_wiring(["/v/bin/clauderizer-mcp"], "windows-wsl:ubuntu")
    assert p.status == "fail" and "clauderize init" in p.detail


def test_verify_wiring_invalid_session_host_fails_loud():
    p = hosts.verify_wiring(["x"], "windows-wsl:")
    assert p.status == "fail" and "distro" in p.detail


def test_verify_wiring_unverifiable_without_interop(monkeypatch):
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", "/x/clauderizer-mcp"],
                            "windows-wsl:ubuntu")
    assert p.status == "unverifiable"


def test_verify_wiring_dead_engine_target_fails_inside_matching_distro(monkeypatch, tmp_path):
    # doctor runs inside the recorded distro: a dead engine-side target is a
    # hard fail even when the wsl.exe round-trip is unavailable. Distro names
    # match case-insensitively (WSL_DISTRO_NAME says Ubuntu; wiring says ubuntu).
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    dead = tmp_path / "gone" / "clauderizer-mcp"
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", str(dead)], "windows-wsl:ubuntu")
    assert p.status == "fail" and "engine-side" in p.detail


def test_verify_wiring_round_trip_certifies(monkeypatch):
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: hosts.Probe("ok", f"clauderizer {hosts.__version__}"))
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", "/x/clauderizer-mcp"],
                            "windows-wsl:ubuntu")
    assert p.ok and "end-to-end" in p.detail and hosts.__version__ in p.detail


# --- verify_wiring: identity, not just launchability (D5, stale-engine proof) --------
# Until Phase 4 this fixture said Probe("ok", "clauderizer 9.9.9") and verify_wiring
# certified it against a non-9.9.9 engine — the exact false green D5 exists to kill.


def test_verify_wiring_round_trip_fails_on_version_skew(monkeypatch):
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: hosts.Probe("ok", "clauderizer 9.9.9"))
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", "/x/clauderizer-mcp"],
                            "windows-wsl:ubuntu")
    assert p.status == "fail"
    assert "9.9.9" in p.detail and hosts.__version__ in p.detail
    assert "stale" in p.detail


def test_verify_wiring_round_trip_fails_without_identity(monkeypatch):
    # The lesson-#4 accident: a pre-0.6.0 clauderizer-mcp exits 0 on EOF and
    # prints nothing — exit code alone would certify a stale pinned engine.
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: hosts.Probe(
                            "ok", "`wsl.exe -d ubuntu uvx clauderizer-mcp --version` exit 0"))
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", "/x/clauderizer-mcp"],
                            "windows-wsl:ubuntu")
    assert p.status == "fail"
    assert "did not identify" in p.detail and hosts.__version__ in p.detail


def test_verify_wiring_round_trip_fails_on_wrapper_breadcrumb(monkeypatch):
    # The D4 wrapper always exits 0 and converts a dead engine into a stdout
    # breadcrumb — without the identity check that read as a GREEN hook verdict.
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    crumb = (f"{hosts.BREADCRUMB_PREFIX} exit 127 from /x/clauderizer-hook "
             f"— run `clauderize doctor`")
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: hosts.Probe("ok", crumb))
    p = hosts.verify_wiring(["wsl.exe", "-d", "ubuntu", "/bin/sh", "/x/.clauderizer/hook.sh"],
                            "windows-wsl:ubuntu")
    assert p.status == "fail"
    assert hosts.BREADCRUMB_PREFIX in p.detail  # the breadcrumb surfaces in doctor output


# --- init: composition, record, and the H-04 refusal ----------------------------------


def test_init_records_native_by_default(empty_python_repo):
    report = init(empty_python_repo, spawn_test=False)
    assert report.session_host == "native"
    cfg = Config.load(empty_python_repo / ".clauderizer" / "config.toml")
    assert cfg.session_host == "native"
    data = json.loads((empty_python_repo / ".mcp.json").read_text(encoding="utf-8"))
    assert data["mcpServers"]["clauderizer"]["command"] != "wsl.exe"


def test_init_adopts_existing_wsl_wiring(empty_python_repo):
    mcp = empty_python_repo / ".mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {"clauderizer": {
        "command": "wsl.exe", "args": ["-d", "ubuntu", "/old/clauderizer-mcp"]}}}),
        encoding="utf-8")
    report = init(empty_python_repo, spawn_test=False)
    assert report.session_host == "windows-wsl:ubuntu"
    entry = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["command"] == "wsl.exe"
    assert entry["args"][:2] == ["-d", "ubuntu"]
    assert entry["args"][-1].endswith("clauderizer-mcp")
    # the hook goes through the same shim as ONE command string — since D4 the
    # registered target is the breadcrumb wrapper, not the engine directly
    settings = json.loads(
        (empty_python_repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for g in settings["hooks"]["SessionStart"] for h in g["hooks"]]
    assert any(c.startswith("wsl.exe -d ubuntu /bin/sh ")
               and c.endswith(".clauderizer/hook.sh") for c in cmds)


def test_init_explicit_flag_wins_and_persists(empty_python_repo):
    init(empty_python_repo, session_host="windows-wsl:debian", spawn_test=False)
    cfg = Config.load(empty_python_repo / ".clauderizer" / "config.toml")
    assert cfg.session_host == "windows-wsl:debian"
    report2 = init(empty_python_repo, spawn_test=False)  # no flag: record wins
    assert report2.session_host == "windows-wsl:debian"


def test_init_shimmed_rerun_is_idempotent(empty_python_repo):
    init(empty_python_repo, session_host="windows-wsl:ubuntu", spawn_test=False)
    snap = {p: p.read_text(encoding="utf-8")
            for p in sorted(empty_python_repo.rglob("*")) if p.is_file()}
    report2 = init(empty_python_repo, spawn_test=False)
    assert report2.changed == []
    for p, before in snap.items():
        assert p.read_text(encoding="utf-8") == before, p


def test_init_invalid_session_host_writes_nothing(empty_python_repo):
    with pytest.raises(hosts.SessionHostError):
        init(empty_python_repo, session_host="windows-wsl:", spawn_test=False)
    assert not (empty_python_repo / ".clauderizer").exists()


def test_init_refuses_h04_miscomposition(empty_python_repo):
    # `--run-cmd` ending in the subcommand CLI composes `clauderize
    # clauderizer-mcp` (exit 2). init must refuse — and write NOTHING.
    with pytest.raises(WiringRefused) as ei:
        init(empty_python_repo, run_cmd=[sys.executable, "-m", "clauderizer.cli"])
    msg = str(ei.value)
    assert "nothing was written" in msg.lower()
    assert "clauderizer-mcp" in msg
    assert not (empty_python_repo / ".mcp.json").exists()
    assert not (empty_python_repo / ".clauderizer").exists()
    assert not (empty_python_repo / "CLAUDE.md").exists()


def test_init_spawn_test_passes_on_real_console_scripts(empty_python_repo):
    # Default spawn_test=True, end to end: the installed console scripts answer
    # --version (added this phase), so a plain init probes for real and proceeds.
    report = init(empty_python_repo)
    assert report.warnings == []
    assert (empty_python_repo / ".mcp.json").exists()


def test_init_unverifiable_warns_but_writes(empty_python_repo, monkeypatch):
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    report = init(empty_python_repo, session_host="windows-wsl:ubuntu")
    assert report.warnings and "unverifiable" in report.warnings[0]
    entry = json.loads((empty_python_repo / ".mcp.json").read_text(
        encoding="utf-8"))["mcpServers"]["clauderizer"]
    assert entry["command"] == "wsl.exe"


# --- doctor: host-aware messaging ---------------------------------------------------


def _doctor(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    rc = cli.main(["doctor"])
    return rc, capsys.readouterr().out


def test_doctor_native_repo_stays_green(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert rc == 0
    assert "session host of record: native" in out
    assert "\nOK" in out


def test_doctor_reports_unverifiable_never_green(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, session_host="windows-wsl:ubuntu", spawn_test=False)
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)  # no interop round-trip
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert rc == 3  # nothing failed, but "OK" alone would be a false green
    assert "✓ session host of record: windows-wsl:ubuntu" in out
    assert "? MCP server launchable for session host — unverifiable from this host" in out
    assert "? SessionStart hook launchable for session host — unverifiable from this host" in out
    assert "✓ MCP server launchable" not in out
    assert "unverifiable from this host" in out.splitlines()[-1] or "certify" in out


def test_doctor_nudges_unrecorded_shimmed_wiring(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, session_host="windows-wsl:ubuntu", spawn_test=False)
    cfg_file = empty_python_repo / ".clauderizer" / "config.toml"
    cfg = Config.load(cfg_file)
    cfg.session_host = None  # simulate a pre-phase-2 config
    cfg_file.write_text(cfg.to_toml(), encoding="utf-8")
    monkeypatch.setattr(hosts.shutil, "which", lambda n: None)
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "? session host of record — not recorded" in out
    assert "re-run `clauderize init`" in out
    # with native rules and no interop the shim is honestly unlaunchable -> drift
    assert rc == 2
