"""agent-autonomy Phase 3 (D4): the cold-start breadcrumb hook wrapper.

H-01's residue: the harness injects only a hook's STDOUT into session
context, so a hook whose engine cannot spawn used to die silently (error on
stderr only — verified live before building). The wrapper is the layer below
the engine: these tests execute it for real on its host shell, prove the
breadcrumb lands on stdout verbatim with exit 0, and pin init's
registration/dedup/regeneration plus doctor's wrapper messaging.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from clauderizer import cli, hosts
from clauderizer.scaffold.init import init

posix_only = pytest.mark.skipif(sys.platform == "win32",
                                reason="executes the POSIX wrapper shell")


def _run_sh(script_path, *args):
    return subprocess.run(["/bin/sh", str(script_path), *args],
                          capture_output=True, stdin=subprocess.DEVNULL, timeout=60)


def _hook_cmds(repo):
    settings = json.loads(
        (repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    return [h["command"] for g in settings["hooks"]["SessionStart"]
            for h in g["hooks"]]


# --- template rendering --------------------------------------------------------


def test_render_sh_bakes_engine_and_forwards_args():
    text = hosts.render_hook_wrapper(["/v/bin/clauderizer-hook"])
    assert text.startswith("#!/bin/sh")
    assert "# engine-hook: /v/bin/clauderizer-hook" in text
    assert '"$@"' in text  # transparent to --version probes
    assert hosts.BREADCRUMB_PREFIX in text
    assert "clauderize doctor" in text
    assert text.rstrip().endswith("exit 0")  # a hook must never block a session


def test_render_cmd_variant():
    text = hosts.render_hook_wrapper(["C:\\v\\clauderizer-hook.exe"], windows=True)
    assert text.startswith("@echo off")
    assert "rem engine-hook: C:\\v\\clauderizer-hook.exe" in text
    assert hosts.BREADCRUMB_PREFIX in text
    assert "%*" in text and "exit /b 0" in text


def test_engine_line_round_trips():
    argv = ["uvx", "--from", "clauderizer", "clauderizer-hook"]
    assert hosts.wrapper_engine_argv(hosts.render_hook_wrapper(argv)) == argv
    assert hosts.wrapper_engine_argv(
        hosts.render_hook_wrapper(argv, windows=True)) == argv
    assert hosts.wrapper_engine_argv("#!/bin/sh\necho hi\n") is None


def test_hook_wrapper_invocation_matrix(monkeypatch, tmp_path):
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    sh_path = (tmp_path / ".clauderizer" / "hook.sh").as_posix()
    assert hosts.hook_wrapper_invocation(tmp_path, "native") == ["/bin/sh", sh_path]
    assert hosts.hook_wrapper_invocation(tmp_path, "windows-wsl:ubuntu") == [
        "wsl.exe", "-d", "ubuntu", "/bin/sh", sh_path]
    monkeypatch.setattr(hosts.sys, "platform", "win32")
    argv = hosts.hook_wrapper_invocation(tmp_path, "native")
    assert argv[:2] == ["cmd", "/c"] and argv[2].endswith("hook.cmd")


# --- real execution on the host shell (the exit-criterion behavior) -------------


@posix_only
def test_dead_engine_emits_breadcrumb_on_stdout(tmp_path):
    w = tmp_path / "hook.sh"
    w.write_text(
        hosts.render_hook_wrapper([str(tmp_path / "gone" / "clauderizer-hook")]),
        encoding="utf-8")
    r = _run_sh(w)
    assert r.returncode == 0  # never block the session
    out = r.stdout.decode()
    assert out.startswith(hosts.BREADCRUMB_PREFIX)  # verbatim marker, on stdout
    assert "clauderize doctor" in out
    assert r.stderr == b""  # everything routed where the session can see it


@posix_only
def test_healthy_engine_passes_digest_through(tmp_path):
    fake = tmp_path / "engine"
    fake.write_text("#!/bin/sh\necho 'digest line'\n", encoding="utf-8")
    fake.chmod(0o755)
    w = tmp_path / "hook.sh"
    w.write_text(hosts.render_hook_wrapper([str(fake)]), encoding="utf-8")
    r = _run_sh(w)
    assert r.returncode == 0
    assert r.stdout.decode().strip() == "digest line"
    assert hosts.BREADCRUMB_PREFIX not in r.stdout.decode()


@posix_only
def test_wrapper_forwards_args_to_real_engine(tmp_path):
    engine = Path(sys.executable).parent / "clauderizer-hook"
    if not engine.exists():
        pytest.skip("venv console script not present")
    w = tmp_path / "hook.sh"
    w.write_text(hosts.render_hook_wrapper([str(engine)]), encoding="utf-8")
    r = _run_sh(w, "--version")
    assert r.returncode == 0
    assert r.stdout.decode().startswith("clauderizer ")


# --- init: registration matrix, upgrade dedup, regeneration ---------------------


def test_init_native_registers_sh_wrapper(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    wrapper = empty_python_repo / ".clauderizer" / "hook.sh"
    assert wrapper.is_file()
    baked = hosts.wrapper_engine_argv(wrapper.read_text(encoding="utf-8"))
    assert baked and baked[-1].endswith("clauderizer-hook")
    expected = f"/bin/sh {(empty_python_repo / '.clauderizer' / 'hook.sh').as_posix()}"
    assert _hook_cmds(empty_python_repo) == [expected]


def test_init_windows_wsl_registers_shimmed_wrapper(empty_python_repo):
    init(empty_python_repo, session_host="windows-wsl:ubuntu", spawn_test=False)
    sh_path = (empty_python_repo / ".clauderizer" / "hook.sh").as_posix()
    assert _hook_cmds(empty_python_repo) == [f"wsl.exe -d ubuntu /bin/sh {sh_path}"]
    # the wrapper bakes the UNSHIMMED engine command — it executes engine-side
    baked = hosts.wrapper_engine_argv(
        (empty_python_repo / ".clauderizer" / "hook.sh").read_text(encoding="utf-8"))
    assert baked and baked[0] != "wsl.exe"


def test_init_upgrades_direct_wiring_to_wrapper(empty_python_repo):
    # pre-wrapper installs registered the engine directly; re-init must REPLACE
    # that entry via the shared matcher, not append a duplicate
    settings_file = empty_python_repo / ".claude" / "settings.json"
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text(json.dumps({"hooks": {"SessionStart": [
        {"hooks": [{"type": "command",
                    "command": "wsl.exe -d ubuntu /old/clauderizer-hook"}]}]}}),
        encoding="utf-8")
    init(empty_python_repo, spawn_test=False)
    ours = [c for c in _hook_cmds(empty_python_repo) if hosts.is_hook_command(c)]
    assert len(ours) == 1
    assert ".clauderizer/hook.sh" in ours[0]


def test_init_regenerates_wrapper_when_engine_moves(empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    wrapper = empty_python_repo / ".clauderizer" / "hook.sh"
    wrapper.write_text(hosts.render_hook_wrapper(["/moved/away/clauderizer-hook"]),
                       encoding="utf-8")
    init(empty_python_repo, spawn_test=False)  # engine-owned: refreshed to current
    baked = hosts.wrapper_engine_argv(wrapper.read_text(encoding="utf-8"))
    assert baked != ["/moved/away/clauderizer-hook"]


@posix_only
def test_init_wrapper_spawn_tested_and_idempotent(empty_python_repo):
    report = init(empty_python_repo)  # real probes, incl. the registered wrapper
    assert report.warnings == []
    report2 = init(empty_python_repo)
    assert report2.changed == []


# --- doctor: wrapper presence / freshness / nudge --------------------------------


def _doctor(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    rc = cli.main(["doctor"])
    return rc, capsys.readouterr().out


def test_doctor_wrapper_present_and_fresh_green(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "✓ hook wrapper present" in out
    assert "✓ hook wrapper freshness" in out
    assert rc == 0


def test_doctor_missing_wrapper_is_drift(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    (empty_python_repo / ".clauderizer" / "hook.sh").unlink()
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "✗ hook wrapper present" in out
    assert rc == 2


def test_doctor_stale_wrapper_warns(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    (empty_python_repo / ".clauderizer" / "hook.sh").write_text(
        hosts.render_hook_wrapper(["/moved/clauderizer-hook"]), encoding="utf-8")
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "? hook wrapper freshness" in out
    assert rc == 3


def test_doctor_nudges_direct_wiring(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, spawn_test=False)
    sf = empty_python_repo / ".claude" / "settings.json"
    data = json.loads(sf.read_text(encoding="utf-8"))
    data["hooks"]["SessionStart"] = [{"hooks": [{
        "type": "command",
        "command": str(Path(sys.executable).parent / "clauderizer-hook")}]}]
    sf.write_text(json.dumps(data), encoding="utf-8")
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "? hook wrapper — not installed" in out
    assert rc == 3