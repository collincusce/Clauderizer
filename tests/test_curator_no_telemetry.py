"""The curator never proposes deletion from evidence it does not have.

Phase 3, implementing what D-063 already decided and nobody coded:

  > the "never-surfaced: consider whether it still earns its place" pressure
  > is removed

``.clauderizer/telemetry.jsonl`` is machine-local and gitignored into EVERY repo
by ``init``, while ``docs/LESSONS.md`` is committed. So on any fresh clone,
teammate machine, or CI runner there were zero surfacing events, every lesson
read as ``surfaced_count == 0``, and the curator proposed obsoleting **the entire
corpus** — measured at 25 of 25, including a lesson promoted the day before and
three that are the *outputs* of the coverage-gated consolidation ritual. The
standing loop then reported ``converged: True`` after driving the corpus to zero.

Every other obsoletion arm already required ``n >= 2`` resolved surfacings. This
one required no evidence at all, which is exactly what D-065 forbids.
"""

from __future__ import annotations

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer import telemetry


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


GID = "2026-05-01-bootstrap"


def _seed_lessons(paths, n: int = 6) -> None:
    """Project lessons with no telemetry — the fresh-clone shape."""
    # Lexically DISJOINT texts: the consolidate arm keys on token overlap and
    # needs no telemetry, so near-duplicate fixtures would make `converged`
    # False for a legitimate reason and mask what these tests measure.
    topics = [
        "Windows path separators in a wrapper assertion are a platform claim.",
        "A stale editable install hides a version bumped in only one place.",
        "Cold uv cache resolution answers from a mirror nobody swept.",
        "Symlinked parent directories escape a leaf-only containment guard.",
        "Frontmatter with a byte-order mark vanishes from the entity graph.",
        "Publishing fires on the Release event, never on the bare tag.",
        "Trusted publishing needs no long-lived token in any secret store.",
        "Reading transcripts from a home directory leaves the repository.",
    ]
    for text in topics[:n]:
        r = M.add_lesson(paths, gameplan_id=GID, text=text)
        M.promote_lesson(paths, gameplan_id=GID, number=r["number"])


def test_zero_telemetry_yields_zero_obsoletion_proposals(temp_repo):
    """THE regression. Pre-fix: one obsolete proposal per active lesson."""
    paths, _ = _ctx(temp_repo)
    _seed_lessons(paths)
    assert not paths.telemetry_file.exists(), "fixture must have no telemetry"

    out = telemetry.curate_proposals(paths, GID)
    obsolete = [p for p in out["proposals"] if p["action"] == "obsolete"]
    assert obsolete == [], (
        "the curator proposed deleting lessons from the ABSENCE of a gitignored "
        f"machine-local file — the fresh-clone corpus wipe. Proposals: {obsolete}"
    )


def test_the_never_surfaced_count_is_still_reported_honestly(temp_repo):
    """Removing the *proposal* must not remove the *measurement*: the count is
    useful and true; treating it as grounds for deletion was the defect."""
    paths, _ = _ctx(temp_repo)
    _seed_lessons(paths, 4)
    health = telemetry.corpus_health(paths)
    assert health["active_project_lessons"] >= 4
    assert health["never_surfaced"] == health["active_project_lessons"], (
        "with no telemetry every lesson IS never-surfaced; that fact should "
        "still be reported"
    )


def test_the_signal_wording_says_unmeasured_not_unused(temp_repo):
    """A per-lesson signal that says 'consider whether it still earns its place'
    on a checkout that measured nothing is a claim from absent evidence."""
    paths, _ = _ctx(temp_repo)
    _seed_lessons(paths, 3)
    health = telemetry.lesson_health(paths)
    signals = [s for s in (r.get("signal") for r in health["scores"]) if s]
    assert signals, "expected a signal per never-surfaced lesson"
    for s in signals:
        assert "UNMEASURED" in s, s
        assert "still earns its place" not in s, s


def test_loop_step_distinguishes_no_evidence_from_a_healthy_corpus(temp_repo):
    """Otherwise the guard trades a false wipe for a false green."""
    paths, _ = _ctx(temp_repo)
    _seed_lessons(paths, 3)
    out = telemetry.loop_step(paths, GID)
    assert out["converged"] is True
    assert out["has_telemetry"] is False
    assert "no telemetry" in out["summary"], out["summary"]


def test_the_standing_loop_cannot_drive_the_corpus_to_zero(temp_repo):
    """Drive the shipped loop body the way the procedure documents it: apply
    every actionable proposal, then loop. Pre-fix this reached 0 lessons and
    reported converged."""
    paths, _ = _ctx(temp_repo)
    _seed_lessons(paths, 6)
    before = telemetry.corpus_health(paths)["active_project_lessons"]

    for _ in range(10):
        out = telemetry.loop_step(paths, GID)
        actionable = [p for p in out["proposals"]
                      if p["action"] in ("consolidate", "obsolete", "promote")]
        if not actionable:
            break
        for prop in actionable:
            if prop["action"] == "obsolete":
                M.obsolete_lesson(paths, number=prop["lessons"][0], reason="loop")

    after = telemetry.corpus_health(paths)["active_project_lessons"]
    assert after == before, (
        f"the standing loop consumed the corpus: {before} -> {after} active "
        "lessons, with no telemetry to justify a single deletion"
    )


def test_low_utility_obsoletion_still_works_when_there_IS_evidence(temp_repo):
    """The fix must not disarm the arm that has real evidence behind it — that
    arm requires n >= 2 resolved surfacings and is untouched."""
    paths, _ = _ctx(temp_repo)
    src = (P.resolve(temp_repo).clauderizer_dir)
    src.mkdir(parents=True, exist_ok=True)
    # The arm is gated on resolved_count >= 2 and utility <= 0.2; assert the
    # gate itself is still present rather than simulating a whole telemetry log.
    import inspect
    body = inspect.getsource(telemetry.curate_proposals)
    assert "n >= 2 and u is not None and u <= 0.2" in body, (
        "the evidence-backed low-utility obsoletion arm was removed along with "
        "the evidence-free one"
    )
    assert 'evidence": "never surfaced in any handoff to date"' not in body, (
        "the evidence-free obsoletion arm is still present"
    )
