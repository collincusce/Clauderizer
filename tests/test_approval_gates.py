"""Approval gates (gameplan 2026-07-01, decision D1): hash-bound exit criteria.

An APPROVAL criterion binds a human sign-off to the artifact's content hash;
satisfaction is COMPUTED at read time (stale/missing/unapproved report as
unsatisfied), surfaced by check/transition/preflight, and never blocks
(INVARIANT-05).
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import preflight, status_bundle

GID = "2026-05-01-bootstrap"
ARTIFACT = "briefs/shot-spec.md"


def _setup(repo, phase="0"):
    paths = P.resolve(repo)
    (repo / "briefs").mkdir(exist_ok=True)
    (repo / ARTIFACT).write_text("v1: seven beats, memento execution\n",
                                 encoding="utf-8")
    M.set_exit_criteria(paths, gameplan_id=GID, phase=phase, criteria=[
        f"APPROVAL: {ARTIFACT} — human signs off the shot spec",
        "plain criterion",
    ])
    return paths


def _approval_row(paths, phase="0"):
    crits = status_bundle.exit_criteria(paths.gameplan_dir(GID), phase)
    return next(c for c in crits if c.get("kind") == "approval")


def test_unapproved_row_reports_unsatisfied(temp_repo):
    paths = _setup(temp_repo)
    row = _approval_row(paths)
    assert row["state"] == "unapproved"
    assert row["checked"] is False
    assert row["artifact"] == ARTIFACT


def test_approve_records_hash_and_satisfies(temp_repo):
    paths = _setup(temp_repo)
    r = M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL",
                       note="user ok (v1)")
    assert r["ok"] and len(r["hash"]) == status_bundle.APPROVAL_HASH_LEN
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert f"sha256:{r['hash']}" in gp and "user ok [v1]" in gp  # ')' sanitized
    row = _approval_row(paths)
    assert row["state"] == "approved" and row["checked"] is True


def test_editing_artifact_reopens_approval_computed(temp_repo):
    paths = _setup(temp_repo)
    M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    (temp_repo / ARTIFACT).write_text("v2: pivot to kinetic typography\n",
                                      encoding="utf-8")
    row = _approval_row(paths)
    assert row["state"] == "stale"
    assert row["checked"] is False  # computed reopening — no write happened
    assert "approval stale" in row["detail"]
    # transition_phase(complete) surfaces it among unchecked criteria
    M.transition_phase(paths, gameplan_id=GID, phase_n="0",
                       to_status="in_progress")  # fixture state may vary
    res = M.transition_phase(paths, gameplan_id=GID, phase_n="0",
                             to_status="complete")
    ec = next(a for a in res.get("advisories", []) if a["kind"] == "exit_criteria")
    assert any("approval stale" in item for item in ec["items"])


def test_missing_artifact_surfaces_gracefully(temp_repo):
    paths = _setup(temp_repo)
    r = M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    assert r["ok"]
    (temp_repo / ARTIFACT).unlink()
    row = _approval_row(paths)
    assert row["state"] == "missing" and row["checked"] is False
    # approving a nonexistent artifact fails politely, never raises
    M.set_exit_criteria(paths, gameplan_id=GID, phase="0", criteria=[
        "APPROVAL: briefs/nope.md — sign off"])
    r2 = M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    assert not r2["ok"] and "artifact missing" in r2["summary"]


def test_hand_checking_an_approval_advises_and_does_not_count(temp_repo):
    paths = _setup(temp_repo)
    r = M.check_exit_criterion(paths, gameplan_id=GID, phase="0",
                               criterion="APPROVAL", checked=True)
    assert r["ok"] and "cz_approve_gate" in r.get("advisory", "")
    row = _approval_row(paths)
    assert row["checked"] is False and row["state"] == "unapproved"


def test_reapprove_replaces_marker(temp_repo):
    paths = _setup(temp_repo)
    r1 = M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    (temp_repo / ARTIFACT).write_text("v2\n", encoding="utf-8")
    r2 = M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    assert r1["hash"] != r2["hash"]
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert gp.count("_(approved ") == 1  # replaced, not stacked
    assert _approval_row(paths)["state"] == "approved"


def test_preflight_warns_on_stale_approval_and_stays_silent_without_approvals(temp_repo):
    paths = _setup(temp_repo)
    config = cfg.Config.load(paths.config_file)
    config.preflight_checks = ["clean_tree"]  # deterministic base checks
    profile = _stub_profile()
    M.transition_phase(paths, gameplan_id=GID, phase_n="0", to_status="in_progress")
    M.approve_gate(paths, gameplan_id=GID, phase="0", criterion="APPROVAL")
    (temp_repo / ARTIFACT).write_text("changed after approval\n", encoding="utf-8")
    res = preflight.run(paths, config, profile, runner=_ok_runner).to_dict()
    gate = next(c for c in res["checks"] if c["name"] == "approval_gates")
    assert gate["status"] == "warn" and "approval stale" in gate["detail"]
    assert "PASS WITH WARNINGS" in res["summary"]  # warns, never fails
    # No approval criteria anywhere -> the check is absent entirely (INVARIANT-07)
    M.set_exit_criteria(paths, gameplan_id=GID, phase="0",
                        criteria=["plain only"])
    res2 = preflight.run(paths, config, profile, runner=_ok_runner).to_dict()
    assert all(c["name"] != "approval_gates" for c in res2["checks"])


def _stub_profile():
    from clauderizer.profiles.detect import Profile

    return Profile(name="generic", commands={}, baseline_test_regex="")


def _ok_runner(cmd, cwd):
    return 0, ""
