"""Reinforce-instead-of-duplicate (2.0 P8, D-075/A-002): the write-time
near-duplicate advisory OFFERS a third verb beside consolidate/append, and the
blessed reinforcement write strengthens the EXISTING lesson in place — a
compact tracked trailer ``*(reinforced xN, last <date>)*`` rendered through the
single ``mutations._inline_trailer`` renderer, plus a telemetry ``reinforced``
event for lesson_health.

Law pinned here:
  * H-18 family — the trailer is STATE-INERT: it can never match the
    end-anchored ``lesson_state._STATE_RE``, and state markers keep winning;
  * L-52 — the in-place update is single-trailer (reinforce twice = one
    trailer at x2, never two trailers), and the doc round-trips;
  * INVARIANT-05 — nothing auto-reinforces; the advisory offers, the agent
    decides via the op;
  * INVARIANT-09 — the offer derives from the ONE canonical near-duplicate
    detector (analyze.near_duplicate_lessons @ analyze._LESSON_DUP_JACCARD);
    no second tokenizer/threshold exists for the reinforce path;
  * D-013/D-063 — strength is EVIDENCE in lesson_health/curator output (with
    the wording-may-not-land inverse reading); nothing ranks, keeps, or
    deletes on it.
"""

from __future__ import annotations

import json
import os
import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest

from clauderizer import mutations, ops, telemetry
from clauderizer import paths as P
from clauderizer.markdown import lesson_state, sections, writer
from clauderizer.tools_list import TOOL_NAMES

GID = "2026-05-01-bootstrap"
TODAY = "2026-07-28"


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


@pytest.fixture(autouse=True)
def _own_repo_only(monkeypatch):
    monkeypatch.delenv("CLAUDERIZER_REPO", raising=False)


def _seed_project_lesson(repo: Path, text: str, lid: str = "L-50") -> Path:
    doc = repo / "docs" / "LESSONS.md"
    doc.write_text("# Distilled Lessons\n\n## Lessons\n\n"
                   f"**{lid}.** {text}\n", encoding="utf-8")
    return doc


def _project_line(repo: Path, lid: str = "L-50") -> str:
    doc = repo / "docs" / "LESSONS.md"
    return next(ln for ln in doc.read_text(encoding="utf-8").splitlines()
                if ln.startswith(f"**{lid}.**"))


LESSON = ("Always measure the real artifact on the real target platform "
          "before claiming the install path works")


# --- the advisory offers reinforce as a third verb (INVARIANT-05: offer only) --


def test_advisory_offers_reinforce_as_third_verb(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    res = mutations.add_lesson(paths, gameplan_id=GID, text=LESSON + " today")
    assert res["ok"] and res["related_lessons"]
    # all three verbs present: consolidate, (obsolete,) reinforce
    assert "consolidat" in res["advisory"].lower()
    assert "cz_reinforce_lesson" in res["advisory"]


def test_nothing_auto_reinforces(temp_repo):
    """The advisory OFFERS; only the explicit op writes (INVARIANT-05)."""
    doc = _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.add_lesson(paths, gameplan_id=GID, text=LESSON + " again")
    assert "reinforced" not in doc.read_text(encoding="utf-8")
    events = telemetry.read_events(paths.telemetry_file)
    assert [e for e in events if e.get("kind") == "reinforced"] == []


def test_no_reinforce_offer_below_the_canonical_threshold(temp_repo):
    """INVARIANT-09: the offer rides the ONE detector at the ONE threshold —
    a lesson that does not clear analyze._LESSON_DUP_JACCARD gets no verb."""
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    res = mutations.add_lesson(
        paths, gameplan_id=GID,
        text="Rotate the signing keys quarterly and audit the rotation log")
    assert "related_lessons" not in res and "advisory" not in res


# --- the blessed write: tracked trailer through the single renderer ------------


def test_first_reinforce_appends_the_trailer(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    res = mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                                     today=TODAY)
    assert res["ok"] and res["count"] == 1
    line = _project_line(temp_repo)
    # rendered exactly as the single _inline_trailer renderer produces it
    assert line.endswith(mutations._inline_trailer(f"reinforced x1, last {TODAY}"))
    assert lesson_state.parse_state(line)[0] == lesson_state.ACTIVE


def test_second_reinforce_updates_in_place_single_trailer(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                               today="2026-07-01")
    res = mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                                     today=TODAY)
    assert res["ok"] and res["count"] == 2
    line = _project_line(temp_repo)
    assert line.count("reinforced") == 1, "in-place update, never a second trailer"
    assert f"*(reinforced x2, last {TODAY})*" in line
    assert "2026-07-01" not in line


def test_reinforce_preserves_existing_trailers_and_round_trips(temp_repo):
    """A promoted line already carries ancestry/evidence trailers; the
    reinforcement trailer joins them without disturbing any (L-52)."""
    doc = temp_repo / "docs" / "LESSONS.md"
    doc.write_text(
        "# Distilled Lessons\n\n## Lessons\n\n"
        f"**L-50.** {LESSON} *(evidence: CI run 42)* *(from {GID} #3, 2026-07-01)*\n",
        encoding="utf-8")
    paths = P.resolve(temp_repo)
    assert mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                                      today=TODAY)["ok"]
    line = _project_line(temp_repo)
    assert "*(evidence: CI run 42)*" in line
    assert f"*(from {GID} #3, 2026-07-01)*" in line
    assert f"*(reinforced x1, last {TODAY})*" in line
    # round-trip: the section parser still finds exactly this one lesson line
    body = sections.get_section(writer.full_text(doc), "Lessons")
    assert sum(1 for ln in body.splitlines() if ln.startswith("**L-50.**")) == 1


def test_gameplan_lesson_number_form_works(temp_repo):
    paths = P.resolve(temp_repo)
    n = mutations.add_lesson(paths, gameplan_id=GID, text="A gameplan lesson "
                             "about flaky spawn probes on windows")["number"]
    res = mutations.reinforce_lesson(paths, gameplan_id=GID, number=n,
                                     today=TODAY)
    assert res["ok"] and res["count"] == 1
    idx = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    assert f"*(reinforced x1, last {TODAY})*" in idx.read_text(encoding="utf-8")


def test_cannot_reinforce_a_non_active_lesson(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.obsolete_lesson(paths, gameplan_id=GID, number="L-50",
                              reason="consolidated into L-51", today=TODAY)
    res = mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                                     today=TODAY)
    assert res["ok"] is False and "obsolete" in res["summary"]


def test_missing_lesson_refuses_honestly(temp_repo):
    paths = P.resolve(temp_repo)
    res = mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-99",
                                     today=TODAY)
    assert res["ok"] is False


# --- H-18 family: grammar interplay with lesson_state._STATE_RE ----------------


def test_trailer_never_matches_the_state_grammar():
    trailer = mutations._inline_trailer(f"reinforced x3, last {TODAY}")
    line = f"**L-01.** some lesson{trailer}"
    assert lesson_state._STATE_RE.search(line) is None
    assert lesson_state.parse_state(line) == (lesson_state.ACTIVE, "")
    assert lesson_state.parse_reinforcement(line) == (3, TODAY)


def test_state_marker_still_wins_beside_the_trailer(temp_repo):
    """Reinforced-then-obsoleted: the state marker lands after the trailer and
    the line reads OBSOLETE — reinforcement never resurrects a lesson."""
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50", today=TODAY)
    mutations.obsolete_lesson(paths, gameplan_id=GID, number="L-50",
                              reason="superseded by L-51", today=TODAY)
    line = _project_line(temp_repo)
    assert lesson_state.parse_state(line)[0] == lesson_state.OBSOLETE
    assert lesson_state.parse_reinforcement(line) == (1, TODAY)


# --- telemetry: the reinforced event rides along, ids only ---------------------


def test_reinforce_appends_a_text_free_telemetry_event(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50", today=TODAY)
    events = [e for e in telemetry.read_events(paths.telemetry_file)
              if e.get("kind") == "reinforced"]
    assert len(events) == 1
    rec = events[0]
    assert set(rec) == {"kind", "date", "gameplan", "lesson", "count"}
    assert rec["lesson"] == "L-50" and rec["count"] == 1
    assert "measure" not in paths.telemetry_file.read_text(encoding="utf-8")


# --- strength is EVIDENCE, never authority (D-013/D-063) -----------------------


def test_lesson_health_surfaces_strength_as_evidence_with_inverse_reading(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50",
                               today="2026-07-01")
    mutations.reinforce_lesson(paths, gameplan_id=GID, number="L-50", today=TODAY)
    by = {r["id"]: r for r in telemetry.lesson_health(paths)["scores"]}
    assert by["L-50"]["reinforced_count"] == 2
    # the inverse reading rides the evidence — never a verdict
    assert "may be worded so it does not land" in by["L-50"]["reinforcement"]
    assert "evidence" in by["L-50"]["reinforcement"]


def test_unreinforced_lessons_carry_zero_and_no_evidence_string(temp_repo):
    _seed_project_lesson(temp_repo, LESSON)
    paths = P.resolve(temp_repo)
    by = {r["id"]: r for r in telemetry.lesson_health(paths)["scores"]}
    assert by["L-50"]["reinforced_count"] == 0
    assert "reinforcement" not in by["L-50"]


def test_nothing_ranks_or_deletes_on_strength(tmp_path):
    """Twin corpora identical but for the reinforcement trailer: the curator
    proposes the SAME actions on the same lessons, and lesson_health orders
    identically — strength changed only the evidence text. (Trailer tokens do
    join the lesson text for similarity, as every inline trailer always has;
    these fixtures are nowhere near the threshold either way.)

    Division of labor (armed 2026-07-28): this fixture has NO proposals, so it
    guards the creates-nothing and ordering directions; the suppresses-nothing
    direction — a REAL proposal on a reinforced lesson must survive — is
    carried by test_curator_threads_reinforcement_as_evidence_only, which went
    red under the strength-as-authority injection where this one could not."""
    lessons = {
        "L-01": "Measure the real artifact on the real target before claiming "
                "the install path works",
        "L-02": "Rotate signing keys quarterly and audit the rotation log for "
                "stale entries",
    }
    twins = {}
    for name in ("plain", "reinforced"):
        repo = tmp_path / name
        (repo / "docs").mkdir(parents=True)
        body = "\n".join(f"**{lid}.** {txt}" for lid, txt in lessons.items())
        (repo / "docs" / "LESSONS.md").write_text(
            "## Lessons\n\n" + body + "\n", encoding="utf-8")
        twins[name] = P.resolve(repo)
    mutations.reinforce_lesson(twins["reinforced"], gameplan_id="g",
                               number="L-01", today=TODAY)
    shape = {}
    for name, paths in twins.items():
        props = telemetry.curate_proposals(paths)["all_proposals"]
        shape[name] = [(p["action"], p.get("suggested_op"), p["lessons"])
                       for p in props]
        health = telemetry.lesson_health(paths)
        shape[name + "_order"] = [r["id"] for r in health["scores"]]
    assert shape["plain"] == shape["reinforced"]
    assert shape["plain_order"] == shape["reinforced_order"]


def test_curator_threads_reinforcement_as_evidence_only(tmp_path):
    """When a proposal involves a reinforced lesson, the proposal carries the
    evidence string — same action, same suggested op as it would anyway."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    near_a = "Deploy artifacts only after the checksum manifest verifies clean"
    near_b = "Deploy artifacts only after the checksum manifest verifies fully clean"
    (repo / "docs" / "LESSONS.md").write_text(
        "## Lessons\n\n**L-01.** " + near_a + "\n**L-02.** " + near_b + "\n",
        encoding="utf-8")
    paths = P.resolve(repo)
    without = [(p["action"], p["lessons"])
               for p in telemetry.curate_proposals(paths)["all_proposals"]]
    mutations.reinforce_lesson(paths, gameplan_id="g", number="L-01", today=TODAY)
    props = telemetry.curate_proposals(paths)["all_proposals"]
    assert [(p["action"], p["lessons"]) for p in props] == without
    con = next(p for p in props if p["action"] == "consolidate")
    assert "L-01 reinforced x1" in con["reinforcement"]
    assert "may be worded so it does not land" in con["reinforcement"]


# --- the op surface: registered, ordered, honest schema ------------------------


def test_op_registered_and_reaches_the_write(temp_repo):
    assert "cz_reinforce_lesson" in TOOL_NAMES
    assert list(ops.REGISTRY) == TOOL_NAMES
    assert ops.REGISTRY["cz_reinforce_lesson"].writes is True
    _seed_project_lesson(temp_repo, LESSON)
    with _chdir(temp_repo):
        res = ops.run_op("cz_reinforce_lesson", number="L-50")
    assert res["ok"] and res["count"] == 1
    assert "reinforced x1" in _project_line(temp_repo)
