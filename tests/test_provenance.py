"""Provenance/citation on lessons and decisions (D-017): an optional `evidence`
field recording where a lesson or decision came from. Additive and backward-
compatible — omitting it reproduces today's output exactly. The lesson marker
rides inline so it survives every handoff rollup, and it must never be mistaken
for a lesson-state marker (obsolete/promoted)."""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import lesson_state
from clauderizer.rituals import handoff

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _index_text(paths):
    return (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")


def test_add_lesson_evidence_is_optional_and_backward_compatible(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_lesson(paths, gameplan_id=GID, text="plain lesson")
    idx = _index_text(paths)
    assert f"**{r['number']}.** plain lesson" in idx
    assert "(evidence:" not in idx  # omitted -> no marker; output unchanged from today


def test_add_lesson_evidence_renders_inline(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_lesson(paths, gameplan_id=GID, text="grounded lesson",
                     evidence="commit abc123; tests/test_x.py:10")
    idx = _index_text(paths)
    assert (f"**{r['number']}.** grounded lesson "
            "*(evidence: commit abc123; tests/test_x.py:10)*") in idx


def test_add_decision_evidence_is_optional(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.add_decision(paths, title="No-ev", context="c", decision="d", consequences="x")
    body = (paths.doc("DECISIONS").read_text(encoding="utf-8")
            .split(f"### {r1['id']} — No-ev")[1].split("###")[0])
    assert "**Evidence**:" not in body  # omitted -> no Evidence line


def test_add_decision_evidence_renders_as_field(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.add_decision(paths, title="With-ev", context="c", decision="d",
                   consequences="x", evidence="benchmark in docs/PERF.md")
    txt = paths.doc("DECISIONS").read_text(encoding="utf-8")
    assert "**Evidence**: benchmark in docs/PERF.md" in txt


def test_lesson_evidence_survives_handoff_rollup(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.add_lesson(paths, gameplan_id=GID, text="grounded lesson", evidence="commit deadbeef")
    rolled, _count = handoff.collect_lessons(_index_text(paths))
    assert "grounded lesson" in rolled
    assert "*(evidence: commit deadbeef)*" in rolled  # provenance rides into the handoff


def test_evidence_marker_is_not_a_lesson_state_marker():
    """The inline evidence marker reads as ACTIVE, and a real state marker
    appended after it still parses — the two grammars coexist."""
    active = "**5.** grounded lesson *(evidence: commit deadbeef)*"
    assert lesson_state.parse_state(active)[0] == lesson_state.ACTIVE
    obsoleted = active + " (obsolete 2026-06-18: superseded)"
    assert lesson_state.parse_state(obsoleted)[0] == lesson_state.OBSOLETE
