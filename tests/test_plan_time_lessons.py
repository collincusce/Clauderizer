"""Planning surfaces the lessons that govern planning (H-25).

Lesson surfacing lived only in `handoff.assemble`, which runs per PHASE. So a
lesson about how to PLAN could never reach the moment it applies. The measured
cost was not hypothetical: `L-11` ("declare phase dependencies by technical need,
not narrative order") had `surfaced_count` 0 — it had reached nothing, ever — and
the very next gameplan declared a narrative chain for four independent phases.

The compounding harm is what makes this medium and not low: that zero was then
read as evidence the lesson had no value, when it was an artifact of where the
ranker happened to be wired. Curating on a never-surfaced signal would have
deleted exactly the lessons the engine never gave a chance.
"""

from __future__ import annotations

import json
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.rituals import handoff

PLANNING_LESSON = (
    "**L-11.** Declare phase dependencies by technical need, not narrative order — "
    "and expect a restart-gated exit criterion to split its phase across sessions.\n\n")
UNRELATED_LESSON = (
    "**L-99.** Prefer a symlink-refusing atomic writer for every tracked markdown "
    "mutation, with a bounded retry on Windows held handles.\n\n")


def _with_lessons(repo: Path) -> Path:
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Lessons\n\n## Lessons\n\n" + PLANNING_LESSON + UNRELATED_LESSON,
                   encoding="utf-8")
    return doc


# --- the ranker at plan time ---------------------------------------------------

def test_a_planning_goal_retrieves_the_planning_lesson(temp_repo):
    _with_lessons(temp_repo)
    ranked = handoff.plan_lessons(
        P.resolve(temp_repo),
        "phase dependencies declared by technical need across independent phases")
    assert [r["id"] for r in ranked][:1] == ["L-11"], (
        "the lesson that governs this exact planning decision must reach it")


def test_ranking_is_relevance_not_a_dump(temp_repo):
    _with_lessons(temp_repo)
    ranked = handoff.plan_lessons(P.resolve(temp_repo),
                                  "atomic writer symlink windows handles")
    assert [r["id"] for r in ranked][:1] == ["L-99"]


def test_degrades_to_empty_rather_than_raising(temp_repo):
    paths = P.resolve(temp_repo)
    assert handoff.plan_lessons(paths, "") == []          # no goal text
    assert handoff.plan_lessons(paths, "   ") == []
    assert handoff.plan_lessons(paths, "anything") == []  # no LESSONS.md yet


# --- wired into the plan-time op ----------------------------------------------

def test_create_gameplan_returns_ranked_lessons(temp_repo, monkeypatch):
    _with_lessons(temp_repo)
    monkeypatch.chdir(temp_repo)
    res = ops.cz_create_gameplan(
        name="declare phase dependencies for independent phases", focus=False)
    assert res["ok"]
    assert "L-11" in [r["id"] for r in res["relevant_lessons"]]
    assert "L-11" in res["advisory"]
    assert "not instructions" in res["advisory"], "a pointer, never an authority (D-013)"


def test_plan_time_surfacing_reaches_telemetry(temp_repo, monkeypatch):
    """So lesson-utility scoring sees plan-time surfacings and a future
    never-surfaced judgment is sound — the compounding half of H-25."""
    _with_lessons(temp_repo)
    monkeypatch.chdir(temp_repo)
    res = ops.cz_create_gameplan(name="phase dependencies technical need", focus=False)

    raw = (temp_repo / ".clauderizer" / "telemetry.jsonl").read_text(encoding="utf-8")
    events = [json.loads(l) for l in raw.splitlines() if l.strip()]
    plan_ev = [e for e in events if e.get("kind") == "surfaced" and e.get("phase") == "plan"]
    assert plan_ev, "a plan-time surfacing must be logged like a phase-time one"
    assert "L-11" in plan_ev[-1]["lessons"]
    assert plan_ev[-1]["gameplan"] == res["gameplan_id"]


def test_creation_still_succeeds_with_no_lesson_corpus(temp_repo, monkeypatch):
    """Advisory means advisory: a plan must never fail over its own advice."""
    monkeypatch.chdir(temp_repo)
    res = ops.cz_create_gameplan(name="a brand new initiative", focus=False)
    assert res["ok"] and res.get("gameplan_id")
    assert "relevant_lessons" not in res


def test_focus_and_scaffold_behavior_is_unchanged(temp_repo, monkeypatch):
    """The 1.14.1 contract for this op is untouched — surfacing is additive."""
    _with_lessons(temp_repo)
    monkeypatch.chdir(temp_repo)
    before = cfg.Config.load(P.resolve(temp_repo).config_file).focus
    res = ops.cz_create_gameplan(name="a second axis", focus=False)
    after = cfg.Config.load(P.resolve(temp_repo).config_file).focus
    assert res["focused"] is False and after == before, "focus=False must not steal focus"
    assert (temp_repo / "docs" / "gameplans" / res["gameplan_id"] / "GAMEPLAN.md").exists()
