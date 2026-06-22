"""Phase 0 — telemetry substrate: the append-only surfacing/outcome log, the
deterministic corpus_health metric, and the cz_write_handoff / cz_transition_phase
wiring that the empirical self-improvement loop is built on."""

from __future__ import annotations

import os

from clauderizer import ops, telemetry
from clauderizer import paths as P


def test_record_and_read_round_trip(tmp_path):
    f = tmp_path / "telemetry.jsonl"
    r1 = telemetry.record_surfaced(f, gameplan="gp", phase="0",
                                   lessons=["L-3", "L-1"], invariants=["INVARIANT-05"],
                                   today="2026-06-21")
    r2 = telemetry.record_outcome(f, gameplan="gp", phase="0", status="complete",
                                  criteria_total=4, criteria_checked=4, today="2026-06-21")
    events = telemetry.read_events(f)
    assert events == [r1, r2]                       # append order, exact round-trip
    assert events[0]["lessons"] == ["L-1", "L-3"]   # ids deduped + sorted, deterministic


def test_append_only(tmp_path):
    f = tmp_path / "telemetry.jsonl"
    telemetry.record_outcome(f, gameplan="gp", phase="0", status="failed",
                             criteria_total=2, criteria_checked=1, today="2026-06-21")
    first = f.read_text(encoding="utf-8")
    telemetry.record_outcome(f, gameplan="gp", phase="1", status="complete",
                             criteria_total=3, criteria_checked=3, today="2026-06-21")
    after = f.read_text(encoding="utf-8")
    assert after.startswith(first)                  # prior line untouched (INVARIANT-03)
    assert len(telemetry.read_events(f)) == 2


def test_read_events_tolerates_garbage(tmp_path):
    f = tmp_path / "telemetry.jsonl"
    f.write_text('{"kind": "outcome"}\nnot json\n42\n{"kind": "surfaced"}\n', encoding="utf-8")
    kinds = [e.get("kind") for e in telemetry.read_events(f)]
    assert kinds == ["outcome", "surfaced"]         # garbled + non-dict lines skipped


def _write_lessons(repo, body):
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + body, encoding="utf-8")


def test_corpus_health_is_deterministic_and_measures(tmp_path):
    repo = tmp_path / "repo"
    _write_lessons(repo, "\n".join([
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
        "**L-03.** prefer the Write tool over heredocs for release notes *(from g)*",
    ]) + "\n")
    paths = P.resolve(repo)

    h1 = telemetry.corpus_health(paths, today="2026-06-21")
    h2 = telemetry.corpus_health(paths, today="2026-06-21")
    assert h1 == h2                                  # deterministic
    assert h1["active_project_lessons"] == 3
    assert h1["redundant_pairs"] == 1                # L-01/L-02 are near-duplicates
    assert h1["never_surfaced"] == 3                 # no telemetry yet
    assert h1["pass_rate"] is None

    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase="0",
                              lessons=["L-01"], invariants=[], today="2026-06-21")
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase="0",
                             status="complete", criteria_total=2, criteria_checked=2,
                             today="2026-06-21")
    h3 = telemetry.corpus_health(paths, today="2026-06-21")
    assert h3["never_surfaced"] == 2                 # L-01 now surfaced at least once
    assert h3["surfaced_events"] == 1 and h3["outcome_events"] == 1
    assert h3["pass_rate"] == 1.0


def test_corpus_health_excludes_obsolete_lessons(tmp_path):
    repo = tmp_path / "repo"
    _write_lessons(repo, "\n".join([
        "**L-01.** active lesson about releases *(from g)*",
        "**L-02.** stale lesson *(from g)* (obsolete 2026-06-21: consolidated into L-01)",
    ]) + "\n")
    paths = P.resolve(repo)
    h = telemetry.corpus_health(paths, today="2026-06-21")
    assert h["active_project_lessons"] == 1          # obsolete L-02 excluded


def test_wiring_surfaced_on_handoff_and_outcome_on_transition(temp_repo):
    """Exit criterion #1: a 'surfaced' record lands on cz_write_handoff and an
    'outcome' record lands on cz_transition_phase->complete, both append-only and
    through the real op surface — built on a gameplan this test creates itself, so
    it never couples to the fixture's phase layout."""
    cwd = os.getcwd()
    os.chdir(temp_repo)
    try:
        _, ok0 = ops.run_batch([
            {"op": "cz_create_gameplan",
             "args": {"name": "telemetry wiring probe", "first_phase": "Bootstrap"}},
        ])
        assert ok0
        results, ok = ops.run_batch([
            {"op": "cz_set_exit_criteria",
             "args": {"phase": "0", "criteria": ["the suite is green", "docs updated"]}},
            {"op": "cz_transition_phase", "args": {"phase_n": "0", "to_status": "in_progress"}},
            {"op": "cz_write_handoff", "args": {"phase_n": "0"}},
            {"op": "cz_transition_phase", "args": {"phase_n": "0", "to_status": "complete"}},
            {"op": "cz_corpus_health", "args": {}},
        ])
    finally:
        os.chdir(cwd)
    assert ok, results
    paths = P.resolve(temp_repo)
    events = telemetry.read_events(paths.telemetry_file)
    surfaced = [e for e in events if e["kind"] == "surfaced"]
    outcomes = [e for e in events if e["kind"] == "outcome"]
    assert surfaced, events
    assert outcomes, events
    o = outcomes[-1]
    assert o["status"] == "complete"
    assert o["criteria_total"] == 2 and o["criteria_checked"] == 0
    assert results[-1]["result"]["ok"]               # cz_corpus_health read returns
