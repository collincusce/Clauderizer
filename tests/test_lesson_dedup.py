"""Phase 5: the write-time near-duplicate-lesson advisory (gameplan abstract-index-fast-retrieval).

The principled signal is LENGTH-NORMALIZED token overlap (Jaccard), validated by the
_experiments/lesson_dedup_measure.py measuring stick to beat a naive raw-count
strawman on adversarial near-misses (L-40). These tests lock the behaviour: a
near-paraphrase is flagged, a distinct-but-similar lesson is NOT, and the advisory
NEVER blocks the (append-only) write (INVARIANT-03 / INVARIANT-05).
"""
from __future__ import annotations

from clauderizer import analyze
from clauderizer import config as C
from clauderizer import mutations as M
from clauderizer import paths as P

# Two project lessons to check a new lesson against (the L-NN form the index reads).
_LESSONS = (
    "# Distilled Lessons\n\n## Lessons\n\n"
    "**L-50.** Before an irreversible release, run the full test suite on every host leg the "
    "CI matrix covers; a green on one operating system is only a guess about the others, and "
    "the publish cannot be undone.\n"
    "**L-51.** A dependency's footprint relative to the data it serves is a first-class go or "
    "no-go axis; two gigabytes of machine-learning stack to search one megabyte of markdown is "
    "an absurd ratio.\n"
)

# A near-paraphrase of L-50 (true duplicate) and a distinct-but-similar near-miss.
_DUP = ("Run the entire test suite across every operating system the CI matrix covers before "
        "any irreversible release; one platform passing does not prove the rest and a publish "
        "cannot be undone.")
_NEAR_MISS = ("Before an irreversible release, run the release checklist and sweep the version "
              "across all four registries; the test suite passing is necessary but the registries "
              "must also agree or the publish is double-claimed.")
_NOVEL = ("Prefer literal paths over shell command substitution when isolating a destructive "
          "operation, because dollar-paren expands in the outer shell.")


def _ctx(repo):
    paths = P.resolve(repo)
    paths.doc("LESSONS").write_text(_LESSONS, encoding="utf-8")
    return paths, C.Config.load(paths.config_file)


def test_near_duplicate_lessons_flags_dup_not_near_miss(temp_repo):
    paths, _ = _ctx(temp_repo)
    dup = analyze.near_duplicate_lessons(paths, _DUP)
    assert [d["id"] for d in dup] == ["L-50"]
    assert dup[0]["jaccard"] >= analyze._LESSON_DUP_JACCARD
    # the distinct-but-similar near-miss shares release vocabulary but a different
    # point — Jaccard below the bar, so NOT flagged (the L-40 discriminator)
    assert analyze.near_duplicate_lessons(paths, _NEAR_MISS) == []
    # a novel lesson surfaces nothing
    assert analyze.near_duplicate_lessons(paths, _NOVEL) == []


def test_near_duplicate_lessons_skips_obsolete_targets(temp_repo):
    # an obsolete lesson is not a live consolidation target
    paths = P.resolve(temp_repo)
    paths.doc("LESSONS").write_text(
        "# Distilled Lessons\n\n## Lessons\n\n"
        "**L-50.** Before an irreversible release, run the full test suite on every host leg the "
        "CI matrix covers; a green on one operating system is only a guess about the others "
        "(obsolete 2026-01-01: consolidated into L-99).\n", encoding="utf-8")
    assert analyze.near_duplicate_lessons(paths, _DUP) == []


def test_add_lesson_surfaces_dup_advisory_and_never_blocks(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Dedup Plan", today="2026-06-08")["gameplan_id"]
    res = M.add_lesson(paths, gameplan_id=gid, text=_DUP)
    # the append-only write STILL succeeded — the advisory never blocks (INVARIANT-05/03)
    assert res["ok"] and res["number"] >= 1
    # ...and it surfaced the overlapping project lesson as a consolidate nudge
    assert "L-50" in [d["id"] for d in res["related_lessons"]]
    assert "consolidat" in res["advisory"].lower()


def test_add_lesson_no_advisory_for_novel_lesson(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Novel Plan", today="2026-06-08")["gameplan_id"]
    res = M.add_lesson(paths, gameplan_id=gid, text=_NOVEL)
    assert res["ok"]
    assert "related_lessons" not in res and "advisory" not in res
