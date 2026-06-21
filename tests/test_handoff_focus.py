"""Focused project-lesson injection in handoffs.

Gameplan 2026-06-20-empirical-memory-gains, Phase 1: under memory pressure the
cumulative handoff carries the top-k project lessons most relevant to the phase
(ranked, most-relevant first so it is not buried) plus a pointer to the canonical
full set, instead of dumping all of them. Reconciles D-022 (relevance-focus +
pointer-to-canonical, not tail truncation).
"""
from clauderizer.rituals import handoff

LESSONS = (
    "## Lessons\n\n"
    "**L-01.** unrelated topic one\n"
    "**L-02.** unrelated topic two\n"
    "**L-03.** alpha beta gamma signal\n"
    "**L-04.** unrelated topic four\n"
    "**L-05.** alpha beta partial\n"
    "**L-06.** unrelated topic six\n"
    "**L-07.** alpha only here\n"
    "**L-08.** unrelated topic eight\n"
)


def test_focuses_and_ranks_when_over_k():
    res = handoff.focused_project_lessons(LESSONS, "alpha beta gamma", k=3)
    assert res is not None
    md, shown, total = res
    assert (shown, total) == (3, 8)
    lines = [ln for ln in md.splitlines() if ln.strip()]
    assert lines[0].startswith("**L-03")  # most relevant first — edge position, not buried
    assert "**L-05" in md and "**L-07" in md  # the next-most-relevant included
    assert "**L-01" not in md  # unrelated lessons stay canonical in LESSONS.md, off the handoff


def test_full_list_when_at_or_below_k():
    small = "## Lessons\n\n**L-01.** alpha\n**L-02.** beta\n"
    # <= k active lessons -> no focusing, caller renders the full list (propagation-safe)
    assert handoff.focused_project_lessons(small, "alpha", k=5) is None


def test_no_query_returns_none():
    assert handoff.focused_project_lessons(LESSONS, "", k=3) is None


def test_obsolete_lessons_excluded_from_focus():
    text = (
        "## Lessons\n\n"
        "**L-01.** alpha one\n**L-02.** alpha two\n**L-03.** alpha three\n"
        "**L-04.** alpha four (obsolete 2026-06-20: superseded)\n"
        "**L-05.** alpha five\n**L-06.** alpha six\n"
    )
    res = handoff.focused_project_lessons(text, "alpha", k=3)
    assert res is not None
    md, shown, total = res
    assert total == 5  # the obsolete L-04 is not an active lesson
    assert "**L-04" not in md


# --- Phase 6: focused governing-invariant surfacing (trim-consistent steering) ---

_INVARIANTS_DOC = (
    "## Invariants\n\n"
    "### INVARIANT-90 — Markdown is the canonical source of truth\n\n"
    "the index rebuilds from markdown on disagreement.\n\n"
    "### INVARIANT-91 — Cascade is advisory and never blocks a write\n\n"
    "the engine surfaces candidates; the agent decides.\n\n"
    "### INVARIANT-92 — Releases sweep all four version registries\n\n"
    "source, tags, github releases, and the pypi index.\n"
)


def test_invariant_pointer_surfaces_phase_relevant(temp_repo):
    from clauderizer import paths as P
    paths = P.resolve(temp_repo)
    paths.doc("INVARIANTS").write_text(_INVARIANTS_DOC, encoding="utf-8")
    res = handoff.relevant_invariant_pointer(paths, "the cascade write advisory flow", k=2)
    assert res is not None
    md, shown, total = res
    assert total == 3
    assert "INVARIANT-91" in md  # the cascade/advisory rule is surfaced (relevant)
    assert "INVARIANT-92" not in md  # the unrelated release rule is not injected


def test_invariant_pointer_none_when_nothing_relevant(temp_repo):
    from clauderizer import paths as P
    paths = P.resolve(temp_repo)
    paths.doc("INVARIANTS").write_text(_INVARIANTS_DOC, encoding="utf-8")
    # A phase that touches no invariant's vocabulary injects no rules (trim-first).
    assert handoff.relevant_invariant_pointer(paths, "photosynthesis chloroplast", k=2) is None
