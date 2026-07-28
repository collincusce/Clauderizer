"""Stranded-state detection: heal on PROOF, display only (D-070 P1).

A phase row saying in_progress is an assertion; the session ledger turns it
into a checkable claim. These tests pin the whole safety envelope from the
refuter verdicts: only provable death fires (alive/inconclusive heal nothing),
the probe is POSIX-gated and can never signal on win32, one's own session is
never reconciled, parked states are never probed, the read path writes zero
bytes anywhere, and a healthy repo's digest stays byte-identical.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer import session_ledger
from clauderizer.rituals import preflight, stranded
from clauderizer.rituals import status_bundle as S


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _gameplan(paths):
    gid = M.create_gameplan(paths, "Stranded probe", today="2026-07-27")["gameplan_id"]
    M.add_phase(paths, gameplan_id=gid, name="P1", goal="g")
    return gid


def _stamp_line(paths, gid, phase, **over):
    rec = {"kind": "session", "gameplan": gid, "phase": str(phase),
           "pid": 4194000, "start": None, "host": socket.gethostname(),
           "agent": "claude-code", "transport": "mcp", "at": "2026-07-27"}
    rec.update(over)
    p = paths.clauderizer_dir / session_ledger.LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def _freed_pid() -> int:
    """A pid that provably does not exist: spawn a child, wait it, use its pid
    (the kernel will not reuse it this fast)."""
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def _target(gid_phase="1", name="P1"):
    return {"number": gid_phase, "name": name}


# --- the ledger: stamp + read -------------------------------------------------

def test_transition_to_in_progress_stamps_the_ledger(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="in_progress", today="2026-07-27")
    entry = session_ledger.last_stamp(paths, gid, "1")
    assert entry is not None
    assert entry["pid"] == os.getpid()
    assert entry["host"] == socket.gethostname()
    assert entry["at"] == "2026-07-27"
    assert entry["transport"] in ("mcp", "cli", "unknown")


def test_last_stamp_survives_corrupt_lines(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    p = paths.clauderizer_dir / session_ledger.LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"torn... \nnot json\n', encoding="utf-8")
    assert session_ledger.last_stamp(paths, gid, "1") is None
    _stamp_line(paths, gid, "1", pid=123)
    assert session_ledger.last_stamp(paths, gid, "1")["pid"] == 123


# --- the probe: grading, POSIX gate, PID reuse --------------------------------

def test_probe_grades_a_freed_pid_dead(temp_repo):
    paths, _ = _ctx(temp_repo)
    entry = {"transport": "mcp", "host": socket.gethostname(),
             "pid": _freed_pid(), "start": None}
    assert session_ledger.probe(entry) == "dead"


def test_probe_grades_a_live_pid_alive():
    entry = {"transport": "mcp", "host": socket.gethostname(),
             "pid": os.getpid(), "start": session_ledger._proc_start_time(os.getpid())}
    assert session_ledger.probe(entry) == "alive"


def test_probe_detects_pid_reuse_by_start_time_mismatch():
    entry = {"transport": "mcp", "host": socket.gethostname(),
             "pid": os.getpid(), "start": "1"}  # a boot-time-ago starttime
    assert session_ledger.probe(entry) == "dead"


@pytest.mark.parametrize("over,expected", [
    ({"transport": "cli"}, "inconclusive"),
    ({"transport": "unknown"}, "inconclusive"),
    ({"host": "some-other-machine"}, "inconclusive"),
    ({"pid": "not-a-pid"}, "inconclusive"),
    ({"pid": -4}, "inconclusive"),
])
def test_probe_unprovable_cases_are_inconclusive(over, expected):
    entry = {"transport": "mcp", "host": socket.gethostname(),
             "pid": os.getpid(), "start": None}
    entry.update(over)
    assert session_ledger.probe(entry) == expected


def test_probe_never_signals_on_non_posix(monkeypatch):
    """The binding POSIX gate: on win32 os.kill delivers CTRL_C_EVENT — the
    probe must return inconclusive WITHOUT any kill call."""
    calls = []

    def _spy(*a, **k):
        calls.append(a)
        raise AssertionError("os.kill must never run on a non-posix platform")

    monkeypatch.setattr(session_ledger.os, "kill", _spy)
    monkeypatch.setattr(session_ledger.os, "name", "nt")
    entry = {"transport": "mcp", "host": socket.gethostname(),
             "pid": 12345, "start": None}
    assert session_ledger.probe(entry) == "inconclusive"
    assert calls == []


# --- detect: heal on proof only ----------------------------------------------

def test_detect_fires_on_a_provably_dead_claimant(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _stamp_line(paths, gid, "1", pid=_freed_pid())
    found = stranded.detect(paths, gid, _target(), "in_progress")
    assert found is not None
    assert found["grade"] == "dead" and found["phase"] == "1"
    assert "judgment" in stranded.describe(found).lower()


def test_detect_never_reconciles_its_own_session(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _stamp_line(paths, gid, "1", pid=os.getpid())
    assert stranded.detect(paths, gid, _target(), "in_progress") is None


def test_detect_heals_nothing_on_alive_or_inconclusive(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    # alive claimant (another live process: our parent)
    _stamp_line(paths, gid, "1", pid=os.getppid(), start=None)
    assert stranded.detect(paths, gid, _target(), "in_progress") is None
    # inconclusive: cli transport
    _stamp_line(paths, gid, "1", pid=_freed_pid(), transport="cli")
    assert stranded.detect(paths, gid, _target(), "in_progress") is None
    # inconclusive: different host
    _stamp_line(paths, gid, "1", pid=_freed_pid(), host="elsewhere")
    assert stranded.detect(paths, gid, _target(), "in_progress") is None


def test_detect_silent_with_no_stamp_or_no_target(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    assert stranded.detect(paths, gid, _target(), "in_progress") is None
    assert stranded.detect(paths, gid, None, "in_progress") is None
    assert stranded.detect(paths, "", _target(), "in_progress") is None


@pytest.mark.parametrize("state", ["blocked", "deferred", "ready",
                                   "not_started", "complete", "failed"])
def test_parked_and_terminal_states_are_never_probed(temp_repo, state, monkeypatch):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _stamp_line(paths, gid, "1", pid=_freed_pid())
    calls = []
    monkeypatch.setattr(session_ledger, "probe",
                        lambda e: calls.append(e) or "dead")
    assert stranded.detect(paths, gid, _target(), state) is None
    assert calls == []


# --- the display-only contract ------------------------------------------------

def _tree_digest(*roots: Path) -> str:
    h = hashlib.sha256()
    for root in roots:
        if not root.exists():
            continue
        for f in sorted(p for p in root.rglob("*") if p.is_file()):
            h.update(str(f).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def test_detect_read_path_writes_zero_bytes(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    _stamp_line(paths, gid, "1", pid=_freed_pid())
    before = _tree_digest(paths.docs, paths.clauderizer_dir)
    found = stranded.detect(paths, gid, _target(), "in_progress")
    assert found is not None
    stranded.describe(found)
    assert _tree_digest(paths.docs, paths.clauderizer_dir) == before


# --- surfacing: digest + preflight, one voice ---------------------------------

def _phase1_in_progress(paths, gid):
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="in_progress", today="2026-07-27")
    # replace our own live stamp with a dead claimant's
    p = paths.clauderizer_dir / session_ledger.LEDGER
    p.unlink()
    _stamp_line(paths, gid, "1", pid=_freed_pid())


def test_digest_carries_the_shared_wording_and_is_quiet_when_healthy(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = _gameplan(paths)
    config.active_gameplan = gid
    config.focus = gid
    healthy = S.render_digest(S.compute(paths, config))
    assert "Stranded" not in healthy
    _phase1_in_progress(paths, gid)
    bundle = S.compute(paths, config)
    assert bundle.get("stranded") is not None
    digest = S.render_digest(bundle)
    assert "⚠ Stranded: " + stranded.describe(bundle["stranded"]) in digest


def test_preflight_warns_never_fails_and_words_identically(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = _gameplan(paths)
    config.active_gameplan = gid
    config.focus = gid
    config.preflight_checks = ["deps_spotcheck"]
    _phase1_in_progress(paths, gid)

    from clauderizer.profiles.detect import Profile
    profile = Profile(name="generic", commands={}, baseline_test_regex="")
    res = preflight.run(paths, config, profile, runner=lambda c, w: (0, "")).to_dict()
    gate = next(c for c in res["checks"] if c["name"] == "stranded_state")
    assert gate["status"] == "warn"
    bundle = S.compute(paths, config)
    assert gate["detail"] == stranded.describe(bundle["stranded"])
    assert res["passed"] is True


def test_reauthorization_advisory_on_reopening_a_closed_phase(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _gameplan(paths)
    M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                       to_status="complete", today="2026-07-27")
    res = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                             to_status="in_progress", today="2026-07-27")
    assert res["ok"] is True
    kinds = [a["kind"] for a in res.get("advisories", [])]
    assert "reauthorization" in kinds
    fresh = M.transition_phase(paths, gameplan_id=gid, phase_n="1",
                               to_status="in_progress", today="2026-07-27")
    assert all(a["kind"] != "reauthorization"
               for a in fresh.get("advisories", []))
