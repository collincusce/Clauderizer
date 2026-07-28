"""Phase 2 — the Curator: cz_curate PROPOSES corpus-maintenance actions
(consolidate / obsolete / flag / promote) from telemetry-derived health, read-only
and propose-only (INVARIANT-05). The A/B test applies the proposals through the
blessed cz_obsolete_lesson and shows corpus health improves with no recall@k
regression on the handoff ranker."""

from __future__ import annotations

import os

from clauderizer import analyze, ops, telemetry
from clauderizer import paths as P


def _bare_repo_with_lessons(tmp_path, lines):
    repo = tmp_path / "repo"
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return P.resolve(repo)


def _surface(paths, phase, project=None, gameplan=None):
    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase=phase,
                              lessons=project or [], invariants=[],
                              gameplan_lessons=gameplan or [], today="2026-06-21")


def _outcome(paths, phase, status):
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase=phase,
                             status=status, criteria_total=1,
                             criteria_checked=1 if status == "complete" else 0,
                             today="2026-06-21")


def test_consolidate_proposal_for_redundant_pair(tmp_path):
    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
        "**L-03.** prefer the Write tool over heredocs for release notes *(from g)*",
    ])
    props = telemetry.curate_proposals(paths)
    cons = [p for p in props["proposals"] if p["action"] == "consolidate"]
    assert len(cons) == 1
    assert set(cons[0]["lessons"]) == {"L-01", "L-02"}
    assert cons[0]["suggested_op"] == "cz_obsolete_lesson"
    assert cons[0]["suggested_args"]["number"] in {"L-01", "L-02"}


def test_obsoletion_needs_evidence_never_surfaced_alone_is_not_enough(tmp_path):
    """D-063's decided contract, implemented in the evidence-traversal release.

    This test previously asserted that a never-surfaced lesson is proposed for
    obsoletion. That arm required NO evidence — and because
    .clauderizer/telemetry.jsonl is gitignored into every repo while LESSONS.md
    is committed, it proposed deleting 100% of the corpus on any fresh clone,
    teammate machine or CI runner. D-063 recorded its removal; Phase 3 shipped
    it. The MEASUREMENT (corpus_health never_surfaced) is unchanged; only the
    deletion proposal is gone.
    """
    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** a lesson that is never surfaced anywhere distinct topic alpha *(from g)*",
        "**L-02.** a different lesson surfaced but its phase keeps failing topic beta *(from g)*",
    ])
    for p in ("1", "2", "3"):                       # L-02: surfaced, always failed
        _surface(paths, p, project=["L-02"]); _outcome(paths, p, "failed")
    props = telemetry.curate_proposals(paths)
    obs = {p["lessons"][0] for p in props["proposals"] if p["action"] == "obsolete"}
    assert "L-01" not in obs, (
        "never-surfaced alone must NOT propose obsoletion — that is the "
        "fresh-clone corpus wipe (D-063)"
    )
    assert "L-02" in obs, (
        "the EVIDENCE-BACKED arm must survive: L-02 was surfaced 3 times and "
        "every phase failed (utility 0.0)"
    )
    # And the count is still reported honestly.
    assert telemetry.corpus_health(paths)["never_surfaced"] >= 1


def test_flag_for_mediocre_utility(tmp_path):
    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** a lone lesson with middling mixed outcomes over time *(from g)*",
    ])
    for p, s in (("1", "complete"), ("2", "failed"), ("3", "complete"), ("4", "failed")):
        _surface(paths, p, project=["L-01"]); _outcome(paths, p, s)   # utility 0.5
    props = telemetry.curate_proposals(paths)
    flags = [p for p in props["proposals"] if p["action"] == "flag"]
    assert len(flags) == 1 and flags[0]["lessons"] == ["L-01"]
    assert flags[0]["suggested_op"] is None         # review-only, no auto-op


def test_promote_proposal_for_high_utility_gameplan_lesson(temp_repo):
    GID = "2026-05-01-bootstrap"
    cwd = os.getcwd(); os.chdir(temp_repo)
    try:
        res, ok = ops.run_batch([
            {"op": "cz_add_lesson",
             "args": {"text": "a durable high-value gameplan lesson", "gameplan_id": GID}},
        ])
        assert ok, res
        num = str(res[0]["result"]["number"])
        paths = P.resolve(temp_repo)
        for p in ("1", "2"):
            _surface(paths, p, gameplan=[num]); _outcome(paths, p, "complete")
        props = telemetry.curate_proposals(paths, GID)
    finally:
        os.chdir(cwd)
    assert any(p["action"] == "promote" and p["lessons"] == [num]
               and p["suggested_op"] == "cz_promote_lesson" for p in props["proposals"])


def test_ab_curation_improves_health_without_recall_regression(temp_repo):
    doc = temp_repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + "\n".join([
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
        "**L-03.** a wholly unrelated lesson that is never surfaced at all *(from g)*",
        "**L-04.** prefer the Write tool over heredocs for release notes *(from g)*",
    ]) + "\n", encoding="utf-8")
    paths = P.resolve(temp_repo)
    before = telemetry.corpus_health(paths)
    assert before["redundant_pairs"] == 1

    props = telemetry.curate_proposals(paths)
    cons = next(p for p in props["proposals"] if p["action"] == "consolidate")
    drop = cons["suggested_args"]["number"]
    cwd = os.getcwd(); os.chdir(temp_repo)
    try:
        _res, ok = ops.run_batch([
            {"op": "cz_obsolete_lesson", "args": {"number": drop, "reason": "consolidated"}},
            {"op": "cz_obsolete_lesson", "args": {"number": "L-03", "reason": "never surfaced"}},
        ])
    finally:
        os.chdir(cwd)
    assert ok, _res
    after = telemetry.corpus_health(paths)
    assert after["redundant_pairs"] == 0                                       # improved
    assert after["active_project_lessons"] < before["active_project_lessons"]  # leaner

    # recall@k: the KEPT release-suite lesson still ranks for its topic.
    from clauderizer.rituals import handoff
    kept = "L-01" if drop == "L-02" else "L-02"
    entries = handoff._project_lesson_entries(doc.read_text(encoding="utf-8"))
    ranked = [r["id"] for r in analyze.rank_relevant(
        "run the full pytest suite before an irreversible release", entries, k=3)]
    assert kept in ranked


# --- merge-base: the id+ledger queue (D-074, executing D-059 / dreaming O-02) ---

def test_curator_proposal_ids_are_stable_across_calls(tmp_path):
    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
    ])
    a = telemetry.curate_proposals(paths)["proposals"]
    b = telemetry.curate_proposals(paths)["proposals"]
    assert [p["id"] for p in a] == [p["id"] for p in b]
    assert all(p["id"].startswith("curate:") for p in a)


def test_dismissal_ends_recurrence_and_a_text_edit_resurfaces_once(tmp_path):
    from clauderizer import proposals as PR

    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
    ])
    first = telemetry.curate_proposals(paths)
    cons = next(p for p in first["proposals"] if p["action"] == "consolidate")
    PR.dismiss(paths, cons["id"])
    # the judged pair stops re-deriving; the suppression is named, not hidden
    after = telemetry.curate_proposals(paths)
    assert cons["id"] not in [p["id"] for p in after["proposals"]]
    assert after["suppressed_count"] == 1
    assert "1 suppressed by your ledger" in after["summary"]
    # display never authority (D-013): the include-suppressed read path
    assert cons["id"] in [p["id"] for p in after["all_proposals"]]
    # merge-base advance: a material text edit resurfaces the pair as a NEW id
    doc = paths.doc("LESSONS")
    doc.write_text(doc.read_text(encoding="utf-8").replace(
        "before every irreversible release step",
        "before every irreversible release step and tag push"), encoding="utf-8")
    again = telemetry.curate_proposals(paths)
    resurfaced = [p for p in again["proposals"] if p["action"] == "consolidate"]
    assert len(resurfaced) == 1 and resurfaced[0]["id"] != cons["id"]
    assert again["suppressed_count"] == 0


def test_corrupt_or_absent_ledger_suppresses_nothing(tmp_path):
    from clauderizer import proposals as PR

    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
    ])
    PR.ledger_path(paths).parent.mkdir(parents=True, exist_ok=True)
    PR.ledger_path(paths).write_text("not [valid toml", encoding="utf-8")
    props = telemetry.curate_proposals(paths)
    assert props["suppressed_count"] == 0
    assert any(p["action"] == "consolidate" for p in props["proposals"])


def test_loop_step_converged_with_suppression_is_a_named_state(tmp_path):
    from clauderizer import proposals as PR

    paths = _bare_repo_with_lessons(tmp_path, [
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
    ])
    _surface(paths, "1", project=["L-01"]); _outcome(paths, "1", "complete")
    step = telemetry.loop_step(paths)
    assert step["converged"] is False and step["actionable_proposals"] == 1
    PR.dismiss(paths, step["proposals"][0]["id"])
    step = telemetry.loop_step(paths)
    assert step["converged"] is True
    assert step["converged_with_suppression"] is True
    assert step["suppressed_count"] == 1
    assert "converged-with-suppression — machine-local" in step["summary"]
    # the unfiltered view survives (D-013)
    assert len(step["all_proposals"]) == 1
