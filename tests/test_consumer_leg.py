"""harness-truth-and-release-ritual Phase 2 (D-010): probes traverse the consumer leg.

H-08's epitaph: doctor certified the SessionStart hook "end-to-end" while every
real session got silence, because the probe spawned the argv array directly —
but the harness executes the registered STRING through Git Bash (MSYS2 argv
conversion) from a cwd that is not the project (H-09). These tests pin the
upgraded verdict: traverse Git Bash from a non-repo cwd and judge in-band
evidence (identity AND digest), report honest unverifiability when the
executor is unreachable, and — lesson #4 — prove the guard FIRES on the old
wiring shape through the real leg (live, skip-guarded on interop presence).
"""

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from clauderizer import cli, hosts
from clauderizer.scaffold.init import init

V = hosts.__version__
WSL_HOST = "windows-wsl:ubuntu"


def _ok(detail):
    return hosts.Probe("ok", detail)


# --- harness_executor / non_repo_cwd ---------------------------------------------


def test_harness_executor_resolves_per_platform(monkeypatch, tmp_path):
    fake = tmp_path / "bash.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setattr(hosts.sys, "platform", "linux")
    monkeypatch.setattr(hosts, "GIT_BASH_INTEROP", fake)
    assert hosts.harness_executor() == fake
    monkeypatch.setattr(hosts, "GIT_BASH_INTEROP", tmp_path / "gone.exe")
    assert hosts.harness_executor() is None
    monkeypatch.setattr(hosts.sys, "platform", "win32")
    monkeypatch.setattr(hosts, "GIT_BASH_WIN32", fake)
    assert hosts.harness_executor() == fake


def test_non_repo_cwd_is_a_real_unclauderized_dir():
    p = Path(hosts.non_repo_cwd())
    assert p.is_dir()
    assert not (p / ".clauderizer").exists()


# --- hook_digest_probe: in-band judgment ------------------------------------------


def test_digest_probe_accepts_in_band_digest(monkeypatch):
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: _ok("[Clauderizer] Gameplan x: phase 1/1."))
    p = hosts.hook_digest_probe(["/bin/sh", "/x/hook.sh"])
    assert p.ok and p.detail.startswith("[Clauderizer]")


def test_digest_probe_fails_engine_breadcrumb(monkeypatch):
    crumb = f"{hosts.BREADCRUMB_PREFIX} exit 127 from /x — run `clauderize doctor`"
    monkeypatch.setattr(hosts, "spawn_probe", lambda argv, **kw: _ok(crumb))
    p = hosts.hook_digest_probe(["/bin/sh", "/x/hook.sh"])
    assert p.status == "fail" and hosts.BREADCRUMB_PREFIX in p.detail


def test_digest_probe_fails_repo_breadcrumb(monkeypatch):
    crumb = f"{hosts.REPO_BREADCRUMB_PREFIX} /gone — run `clauderize doctor`"
    monkeypatch.setattr(hosts, "spawn_probe", lambda argv, **kw: _ok(crumb))
    p = hosts.hook_digest_probe(["/bin/sh", "/x/hook.sh"])
    assert p.status == "fail" and hosts.REPO_BREADCRUMB_PREFIX in p.detail


def test_digest_probe_fails_h09_silence(monkeypatch):
    # spawn_probe's empty-stdout detail shape: exit 0 with nothing in-band —
    # exactly what an un-anchored wrapper produces from a non-repo cwd.
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: _ok("`/bin/sh /x/hook.sh` exit 0"))
    p = hosts.hook_digest_probe(["/bin/sh", "/x/hook.sh"])
    assert p.status == "fail"
    assert "H-09" in p.detail and "clauderize init" in p.detail


def test_digest_probe_passes_through_non_ok(monkeypatch):
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: hosts.Probe("unverifiable", "no interop"))
    p = hosts.hook_digest_probe(["wsl.exe", "-d", "u", "//bin/sh", "//x/hook.sh"])
    assert p.status == "unverifiable"


def test_digest_probe_spawns_no_args_from_given_cwd(monkeypatch, tmp_path):
    seen = {}

    def fake(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw
        return _ok("[Clauderizer] ok")

    monkeypatch.setattr(hosts, "spawn_probe", fake)
    hosts.hook_digest_probe(["/bin/sh", "/x/hook.sh"], cwd=str(tmp_path))
    assert seen["kw"]["probe_arg"] == ""        # the digest path, not --version
    assert seen["kw"]["cwd"] == str(tmp_path)   # hostile cwd honored


# --- verify_hook_wiring: composition matrix (hermetic) -----------------------------


ARGV = ["wsl.exe", "-d", "ubuntu", "//bin/sh", "//x/.clauderizer/hook.sh"]
BASE_OK = _ok(f"verified end-to-end via wsl.exe round-trip (clauderizer {V})")


def _wire(monkeypatch, *, base, executor, spawn=None):
    monkeypatch.setattr(hosts, "verify_wiring", lambda a, s, **kw: base)
    monkeypatch.setattr(hosts, "harness_executor", lambda: executor)
    if spawn is not None:
        monkeypatch.setattr(hosts, "spawn_probe", spawn)


def _spawn_router(identity_probe, digest_probe, calls=None):
    def fake(argv, **kw):
        if calls is not None:
            calls.append((argv, kw))
        if argv[-1].endswith(" --version"):
            return identity_probe
        return digest_probe

    return fake


def test_native_delegates_to_verify_wiring(monkeypatch):
    sentinel = _ok("native presence")
    monkeypatch.setattr(hosts, "verify_wiring", lambda a, s, **kw: sentinel)
    assert hosts.verify_hook_wiring(["/bin/sh", "/x/hook.sh"], "native") is sentinel


def test_invalid_session_host_fails_loud():
    p = hosts.verify_hook_wiring(ARGV, "windows-wsl:")
    assert p.status == "fail" and "distro" in p.detail


def test_base_failure_surfaces_first(monkeypatch):
    _wire(monkeypatch, base=hosts.Probe("fail", "engine-side target gone"),
          executor=Path("/x/bash.exe"))
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "fail" and "engine-side" in p.detail


def test_no_executor_downgrades_green_to_unverifiable(monkeypatch):
    _wire(monkeypatch, base=BASE_OK, executor=None)
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "unverifiable"
    assert "Git Bash" in p.detail and "cold start" in p.detail
    assert f"identity clauderizer {V}" in p.detail
    # D-010: no end-to-end claim may survive for a leg nothing traversed
    assert "end-to-end" not in p.detail


def test_no_executor_keeps_unverifiable_unverifiable(monkeypatch):
    _wire(monkeypatch, base=hosts.Probe("unverifiable", "wsl.exe is not reachable"),
          executor=None)
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "unverifiable" and "Git Bash" in p.detail


def test_executor_leg_all_green_names_the_leg(monkeypatch):
    calls = []
    executor = Path("/mnt/c/git/bash.exe")  # str() differs per OS — compare via str()
    _wire(monkeypatch, base=BASE_OK, executor=executor,
          spawn=_spawn_router(_ok(f"clauderizer {V}"),
                              _ok("[Clauderizer] Gameplan x."), calls))
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.ok
    assert "git-bash" in p.detail and "end-to-end" in p.detail
    assert "non-repo cwd" in p.detail and f"clauderizer {V}" in p.detail
    # the leg is the registered STRING through bash -c, identity then digest,
    # both from the hostile cwd
    id_argv, id_kw = calls[0]
    dg_argv, dg_kw = calls[1]
    assert id_argv == [str(executor), "-c", " ".join(ARGV) + " --version"]
    assert dg_argv == [str(executor), "-c", " ".join(ARGV)]
    assert id_kw["cwd"] == hosts.non_repo_cwd()
    assert dg_kw["cwd"] == hosts.non_repo_cwd()


def test_executor_leg_msys_mangling_fails_loud(monkeypatch):
    err = hosts.Probe(
        "fail",
        "exit 127 from `bash.exe -c ...` — /bin/bash: line 1: "
        "C:/Program Files/Git/usr/bin/sh: No such file or directory")
    _wire(monkeypatch, base=BASE_OK, executor=Path("/x/bash.exe"),
          spawn=_spawn_router(err, _ok("[Clauderizer] never reached")))
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "fail"
    assert "git-bash" in p.detail and "H-08" in p.detail
    assert "wiring_matrix" in p.detail  # points at the evidence artifact


def test_executor_leg_stale_engine_fails(monkeypatch):
    _wire(monkeypatch, base=BASE_OK, executor=Path("/x/bash.exe"),
          spawn=_spawn_router(_ok("clauderizer 9.9.9"), _ok("[Clauderizer] x")))
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "fail"
    assert "9.9.9" in p.detail and V in p.detail and "stale" in p.detail


def test_executor_leg_silent_digest_fails_h09(monkeypatch):
    _wire(monkeypatch, base=BASE_OK, executor=Path("/x/bash.exe"),
          spawn=_spawn_router(_ok(f"clauderizer {V}"), _ok("`bash -c ...` exit 0")))
    p = hosts.verify_hook_wiring(ARGV, WSL_HOST)
    assert p.status == "fail"
    assert "non-repo cwd" in p.detail and "H-09" in p.detail


# --- live: the real leg (skip-guarded; the phase's guard-fires exit criteria) ------

_DISTRO = os.environ.get("WSL_DISTRO_NAME")
_LIVE = (sys.platform != "win32"
         and hosts.GIT_BASH_INTEROP.is_file()
         and shutil.which("wsl.exe") is not None
         and bool(_DISTRO))
live = pytest.mark.skipif(
    not _LIVE, reason="needs Git Bash via WSL interop (the harness's real leg)")


def _hook_argv(repo):
    settings = json.loads(
        (repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    for g in settings["hooks"]["SessionStart"]:
        for h in g["hooks"]:
            if hosts.is_hook_command(h["command"]):
                return h["command"].split()
    raise AssertionError("no clauderizer hook registered")


def _set_hook(repo, cmd):
    sf = repo / ".claude" / "settings.json"
    data = json.loads(sf.read_text(encoding="utf-8"))
    data["hooks"]["SessionStart"] = [{"hooks": [{"type": "command", "command": cmd}]}]
    sf.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


@live
def test_live_shape_c_verifies_end_to_end(empty_python_repo):
    host = f"windows-wsl:{_DISTRO}"
    init(empty_python_repo, session_host=host, spawn_test=False)
    p = hosts.verify_hook_wiring(_hook_argv(empty_python_repo), host)
    assert p.ok, p.detail
    assert "git-bash" in p.detail and "end-to-end" in p.detail


@live
def test_live_old_shape_guard_fires_where_direct_probe_stays_green(empty_python_repo):
    # Lesson #4 / D-010: the pre-Phase-1 shape (bare /-paths) must FAIL through
    # the executor leg — while the direct argv probe still passes it, which is
    # exactly the false green this phase retires.
    host = f"windows-wsl:{_DISTRO}"
    init(empty_python_repo, session_host=host, spawn_test=False)
    new_cmd = " ".join(_hook_argv(empty_python_repo))
    old_cmd = new_cmd.replace("//bin/sh //", "/bin/sh /")
    assert old_cmd != new_cmd
    _set_hook(empty_python_repo, old_cmd)
    old_argv = old_cmd.split()
    assert hosts.verify_wiring(old_argv, host).ok       # the direct probe: blind
    p = hosts.verify_hook_wiring(old_argv, host)        # the executor leg: fires
    assert p.status == "fail", p.detail
    assert "git-bash" in p.detail


@live
def test_live_unanchored_wrapper_fails_digest_probe(empty_python_repo):
    # H-09 regression guard: strip the anchor from the real wrapper; identity
    # still answers (--version precedes repo discovery) but the digest goes
    # silent from a non-repo cwd — the probe must refuse the green.
    host = f"windows-wsl:{_DISTRO}"
    init(empty_python_repo, session_host=host, spawn_test=False)
    wrapper = empty_python_repo / ".clauderizer" / "hook.sh"
    baked = hosts.wrapper_engine_argv(wrapper.read_text(encoding="utf-8"))
    wrapper.write_text(hosts.render_hook_wrapper(baked), encoding="utf-8")  # no root
    p = hosts.verify_hook_wiring(_hook_argv(empty_python_repo), host)
    assert p.status == "fail", p.detail
    assert "H-09" in p.detail


@live
def test_live_doctor_green_through_executor_leg(empty_python_repo, monkeypatch, capsys):
    host = f"windows-wsl:{_DISTRO}"
    # Scoped Claude-only: session_host-composed MCP + hooks (multi default uses
    # portable .mcp.json which is correct for multi-AI, not this executor-leg claim).
    init(empty_python_repo, session_host=host, spawn_test=False,
         host_target="claude-code")
    monkeypatch.chdir(empty_python_repo)
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert "verified end-to-end via harness executor (git-bash" in out
    assert rc == 0, out
