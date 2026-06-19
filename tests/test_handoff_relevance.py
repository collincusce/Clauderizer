"""Idea #2: relevance-ranked lesson pointers in the handoff (reorder-not-drop).

Proves the ranker focuses on the phase-relevant lessons while the canonical
cumulative roll-up keeps ALL of them (D-009 pressure-not-caps; the
incomplete-lesson-propagation anti-pattern in handoff.py).
"""
from clauderizer.config import Config
from clauderizer.markdown import sections
from clauderizer.paths import resolve
from clauderizer.rituals import handoff as H

SIX = [
    "Always run pytest before claiming a phase green (Testing).",
    "The handoff must carry all lessons forward to avoid incomplete propagation (Process).",
    "Cascade reports are resolved via cz_resolve_cascade, never hand-edited (Process).",
    "Frontmatter is parsed by a vendored YAML reader; keep it minimal (Architecture).",
    "Semver pins gate the graph; bumping a subsystem cascades to dependents (Graph).",
    "Prefer deterministic markdown over embeddings for recall (Architecture).",
]


def _index(lessons):
    body = "\n\n".join(f"**{i + 1}.** {t}" for i, t in enumerate(lessons))
    return f"# Index\n\n## Accumulated Lessons\n\n{body}\n"


def test_pointer_absent_when_few_lessons():
    # <= k lessons: the whole list is short enough; no focus block.
    assert H.relevant_lesson_pointer(_index(SIX[:3]), "handoff propagation", k=5) is None


def test_pointer_absent_without_query():
    assert H.relevant_lesson_pointer(_index(SIX), "", k=3) is None


def test_pointer_surfaces_most_relevant_first():
    out = H.relevant_lesson_pointer(
        _index(SIX),
        "the handoff must carry every lesson forward to avoid incomplete propagation",
        k=3)
    assert out is not None
    assert out.splitlines()[0].startswith("- **#2**"), out


def test_different_phases_reorder_differently():
    a = H.relevant_lesson_pointer(_index(SIX), "handoff carry forward incomplete propagation", k=3)
    b = H.relevant_lesson_pointer(
        _index(SIX), "semver pins gate graph bumping subsystem cascades dependents", k=3)
    assert a != b
    assert a.splitlines()[0].startswith("- **#2**")
    assert b.splitlines()[0].startswith("- **#5**")


def test_all_active_lessons_survive_no_drop():
    rolled, count = H.collect_lessons(_index(SIX))
    assert count == 6
    for i in range(1, 7):
        assert f"**{i}.**" in rolled


def test_obsolete_lessons_excluded_from_ranking_pool():
    idx = _index(SIX).replace(
        "**1.** Always run pytest before claiming a phase green (Testing).",
        "**1.** Always run pytest before claiming a phase green (Testing). "
        "(obsolete 2026-06-19: superseded)")
    ids = {e["id"] for e in H._active_lesson_entries(idx)}
    assert "1" not in ids
    assert "2" in ids


def test_assemble_inserts_pointer_and_keeps_all_lessons(temp_repo):
    paths = resolve(temp_repo)
    config = Config.load(paths.config_file)
    gid = config.active_gameplan
    idx_path = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    lessons = [
        "Wire and connect the parts deterministically when integrating subsystems (Process).",
        "Always run pytest before claiming a phase green (Testing).",
        "Cascade reports are resolved via cz_resolve_cascade, never hand-edited (Process).",
        "Frontmatter is parsed by a vendored YAML reader; keep it minimal (Architecture).",
        "Semver pins gate the graph; bumping a subsystem cascades to dependents (Graph).",
        "Prefer deterministic markdown over embeddings for recall (Architecture).",
    ]
    body = "\n\n".join(f"**{i + 1}.** {t}" for i, t in enumerate(lessons))
    text = sections.upsert_section(idx_path.read_text(encoding="utf-8"),
                                   "Accumulated Lessons", body)
    idx_path.write_text(text, encoding="utf-8")

    out = H.assemble(paths, config, gid, "1", write=False)["handoff_md"]
    assert "## Most Relevant Lessons for This Phase" in out
    for i in range(1, 7):  # every lesson still rides along (no drop)
        assert f"**{i}.**" in out
