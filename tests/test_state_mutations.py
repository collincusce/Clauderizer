"""Tests for the 0.3.0 state-mutation surface fixes:

- cz_transition_phase: phases get a blessed lifecycle write (P0)
- preflight advisory: checks can be informational, not fatal (P2)
- init: profile.lock overrides preserved; --workflow sets advisory (P2/P3)
- cz_resolve_finding: update a finding's status without a hand-edit (P4)
- status drift hint: planned entities + completed phases gets surfaced (P1)
"""
from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.profiles.detect import Profile
from clauderizer.rituals import _tables, preflight, status_bundle
from clauderizer.scaffold.init import init

GID = "2026-05-01-bootstrap"


def _pc(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- P0: cz_transition_phase -------------------------------------------------

def test_transition_phase_updates_both_trackers_and_dates(temp_repo):
    paths, _ = _pc(temp_repo)
    r = M.transition_phase(paths, gameplan_id=GID, phase_n="1", to_status="complete",
                           today="2026-06-05")
    assert r["ok"] and r["to_status"] == "complete"
    for fname in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
        text = (paths.gameplan_dir(GID) / fname).read_text()
        rows = {row.number: row.status for row in _tables.parse_phase_table(text)}
        assert rows["1"] == "complete", fname
        assert "| 1 | Wire it up | ✅ COMPLETE | 2026-05-01 | 2026-06-05 |" in text


def test_transition_phase_alias_and_unknown(temp_repo):
    paths, _ = _pc(temp_repo)
    assert M.transition_phase(paths, gameplan_id=GID, phase_n="1",
                              to_status="done")["to_status"] == "complete"
    assert M.transition_phase(paths, gameplan_id=GID, phase_n="1",
                              to_status="bogus")["ok"] is False


def test_transition_phase_unknown_phase(temp_repo):
    paths, _ = _pc(temp_repo)
    assert M.transition_phase(paths, gameplan_id=GID, phase_n="99",
                              to_status="complete")["ok"] is False


def test_cz_status_reflects_phase_transition(temp_repo):
    # The headline fix: advancing a phase makes cz_status move off it.
    paths, config = _pc(temp_repo)
    M.transition_phase(paths, gameplan_id=GID, phase_n="1", to_status="complete",
                       today="2026-06-05")
    bundle = status_bundle.compute(paths, config)
    assert bundle["current_phase"] is None  # phase 1 no longer in progress
    done = [p for p in bundle["phases"] if p["status"] == "complete"]
    assert {"0", "1"} <= {p["number"] for p in done}


# --- P2: preflight advisory --------------------------------------------------

def _runner(responses):
    def run(cmd, _cwd):
        for key, val in responses.items():
            if key in cmd:
                return val
        return (0, "")
    return run


def test_preflight_advisory_downgrades_fail_to_warn(sample_repo):
    paths, config = _pc(sample_repo)
    config.preflight_checks = ["clean_tree", "tests"]
    config.preflight_advisory = ["clean_tree"]
    prof = Profile(name="python", commands={"test": "pytest -q"},
                   baseline_test_regex=r"(\d+) passed")
    runner = _runner({"git status": (0, " M dirty.py"), "pytest": (0, "5 passed")})
    res = preflight.run(paths, config, prof, runner=runner)
    by = {c.name: c.status for c in res.checks}
    assert by["clean_tree"] == "warn"   # would be fail, downgraded
    assert res.passed is True           # advisory never fails preflight


# --- P3: init preserves profile.lock + workflow ------------------------------

def test_init_preserves_profile_lock_overrides(empty_python_repo):
    init(empty_python_repo, size="standard")
    lock = empty_python_repo / ".clauderizer" / "profile.lock.toml"
    lock.write_text('profile = "python"\n[commands]\ntest = "MY-PINNED-CMD"\n', encoding="utf-8")
    init(empty_python_repo, size="standard")  # re-run must not clobber
    assert "MY-PINNED-CMD" in lock.read_text()


def test_init_workflow_audit_sets_advisory(empty_python_repo):
    init(empty_python_repo, size="standard", workflow="audit")
    text = (empty_python_repo / ".clauderizer" / "config.toml").read_text()
    assert "preflight_advisory" in text
    assert "clean_tree" in text.split("preflight_advisory")[1].split("\n")[0]


# --- P4: cz_resolve_finding --------------------------------------------------

def test_resolve_finding_updates_status_and_keeps_entry(temp_repo):
    paths, _ = _pc(temp_repo)
    M.add_finding(paths, title="Reentrancy risk", severity="HIGH", impact="x",
                  today="2026-06-05")
    r = M.resolve_finding(paths, finding_id="H-01", status="resolved",
                          note="owner confirmed 3-of-5 Safe", today="2026-06-06")
    assert r["ok"]
    text = paths.doc("HARDENING").read_text()
    assert "### H-01 — Reentrancy risk" in text      # append-only: entry kept
    assert "**Status**: resolved (2026-06-06)" in text
    assert "**Resolution**: owner confirmed 3-of-5 Safe" in text


def test_resolve_finding_resolution_is_idempotent(temp_repo):
    paths, _ = _pc(temp_repo)
    M.add_finding(paths, title="f", severity="LOW", impact="x", today="2026-06-05")
    M.resolve_finding(paths, finding_id="H-01", note="first", today="2026-06-06")
    M.resolve_finding(paths, finding_id="H-01", note="second", today="2026-06-07")
    text = paths.doc("HARDENING").read_text()
    assert text.count("**Resolution**:") == 1   # replaced, not stacked
    assert "second" in text and "first" not in text


def test_resolve_finding_missing(temp_repo):
    paths, _ = _pc(temp_repo)
    assert M.resolve_finding(paths, finding_id="H-99")["ok"] is False


# --- P1: drift hint ----------------------------------------------------------

def test_drift_hint_fires_on_planned_entity_with_completed_phase(temp_repo):
    paths, config = _pc(temp_repo)
    # fixture already has phase 0 complete; add an untouched 'planned' entity
    M.upsert_entity(paths, id="subsys.untouched", type="subsystem",
                    version="1.0.0", status="planned")
    bundle = status_bundle.compute(paths, config)
    assert bundle["drift"]
    assert any("planned" in w and "cz_transition_status" in w for w in bundle["drift"])


def test_no_drift_hint_without_completed_phases(temp_repo):
    # Reset all phases to not-started -> no completed phase -> no drift noise.
    paths, config = _pc(temp_repo)
    M.transition_phase(paths, gameplan_id=GID, phase_n="0", to_status="not_started")
    M.transition_phase(paths, gameplan_id=GID, phase_n="1", to_status="not_started")
    M.upsert_entity(paths, id="subsys.untouched", type="subsystem",
                    version="1.0.0", status="planned")
    bundle = status_bundle.compute(paths, config)
    assert bundle["drift"] == []
