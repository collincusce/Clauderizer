"""Memory-gap detection (2.0 P8, D-075/A-002): when cz_analyze finds ZERO
relevant decisions AND ZERO invariants for a probe, the RESULT carries an
explicit gap advisory ("memory had nothing on this — record it now") and a
TEXT-FREE gap event lands in telemetry for corpus_health / the dreamer to read
(D-069: a journal consumed, not just written).

The vetting conditions (research-jcode-vetting.json) pinned here:
  * advisory at the moment of the gap, in the TOOL RESULT only — the status
    digest gains ZERO bytes (INVARIANT-08's zero-bytes clause);
  * the persisted event carries counts and ids only — NEVER raw probe text;
  * the hook's analyze path (UserPromptSubmit calls the analyze LIBRARY, not
    the op) writes nothing (INVARIANT-06) — the gap event fires from the
    cz_analyze OP surface alone;
  * corpus_health reports gap_events read-only; zero events render nothing
    extra (the refusal_events precedent).
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager

import pytest

from clauderizer import analyze, config as cfg, ops, telemetry
from clauderizer import paths as P
from clauderizer.rituals import status_bundle as S

# Distinctive nonsense: guaranteed to overlap nothing in the sample corpus, and
# greppable in raw bytes to prove the persisted event never carries probe text.
GAP_PROBE = "xylozenith frobnicator cadence for the quuxplateau rollout"
# Overlaps sample_repo's D-001 ("durable cross-session memory ... markdown").
MATCH_PROBE = "durable cross-session memory in markdown"


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
    """A fleet worktree may inherit $CLAUDERIZER_REPO pointing at a hub —
    these tests must only ever touch their temp repo."""
    monkeypatch.delenv("CLAUDERIZER_REPO", raising=False)


def _events(paths):
    return telemetry.read_events(paths.telemetry_file)


# --- the advisory fires in the cz_analyze RESULT, at the moment of the gap -----


def test_gap_advisory_fires_when_decisions_and_invariants_are_both_empty(temp_repo):
    with _chdir(temp_repo):
        res = ops.run_op("cz_analyze", text=GAP_PROBE)
    assert res["ok"] and res["decisions"] == [] and res["invariants"] == []
    assert res["memory_gap"] is True
    # The record-it-now nudge, naming the blessed writes (the agent decides).
    assert "memory had nothing" in res["gap_advisory"].lower()
    assert "cz_add_decision" in res["gap_advisory"]
    assert "cz_add_lesson" in res["gap_advisory"]
    assert "memory gap" in res["summary"]


def test_no_gap_advisory_when_any_register_matches(temp_repo):
    with _chdir(temp_repo):
        res = ops.run_op("cz_analyze", text=MATCH_PROBE)
    assert res["decisions"] or res["invariants"]
    assert "memory_gap" not in res and "gap_advisory" not in res
    assert "memory gap" not in res["summary"]


def test_empty_probe_is_not_a_gap(temp_repo):
    """An empty/contentless probe surfaces nothing — that is vacuity, not a
    memory gap; nagging on it would be advisory noise (INVARIANT-05 spirit)."""
    with _chdir(temp_repo):
        res = ops.run_op("cz_analyze", text="   the of and   ")
    assert res["decisions"] == [] and res["invariants"] == []
    assert "memory_gap" not in res and "gap_advisory" not in res
    assert not _events(P.resolve(temp_repo))


# --- the persisted event: counts and ids only, never probe text ----------------


def test_gap_event_is_text_free_and_schema_exact(temp_repo):
    paths = P.resolve(temp_repo)
    with _chdir(temp_repo):
        ops.run_op("cz_analyze", text=GAP_PROBE)
    gaps = [e for e in _events(paths) if e.get("kind") == "gap"]
    assert len(gaps) == 1
    rec = gaps[0]
    # Exact key set: a new field carrying prose must be a deliberate act.
    assert set(rec) == {"kind", "surface", "gameplan", "phase", "date",
                        "query_terms"}
    assert rec["surface"] == "cz_analyze"
    assert rec["gameplan"] == "2026-05-01-bootstrap"
    assert isinstance(rec["phase"], str)
    assert rec["query_terms"] == len(analyze._tokens(GAP_PROBE))
    # No raw probe text anywhere in the journal — bytes, not parsed fields.
    raw = paths.telemetry_file.read_text(encoding="utf-8")
    for word in ("xylozenith", "frobnicator", "quuxplateau"):
        assert word not in raw


def test_no_gap_event_when_memory_had_something(temp_repo):
    paths = P.resolve(temp_repo)
    with _chdir(temp_repo):
        ops.run_op("cz_analyze", text=MATCH_PROBE)
    assert [e for e in _events(paths) if e.get("kind") == "gap"] == []


# --- INVARIANT-08: the digest gains zero bytes from gap detection --------------


def test_digest_byte_identical_with_gap_events_present(temp_repo):
    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)
    before = S.render_digest(S.compute(paths, config), tools=["cz_status"])
    with _chdir(temp_repo):
        ops.run_op("cz_analyze", text=GAP_PROBE)
        ops.run_op("cz_analyze", text=GAP_PROBE)
    assert [e for e in _events(paths) if e.get("kind") == "gap"], "precondition"
    after = S.render_digest(S.compute(paths, config), tools=["cz_status"])
    assert before == after
    assert "gap" not in after.lower()


def test_status_bundle_source_never_reads_gap_events():
    """The greppable half of the zero-bytes pin: no digest wiring exists to
    grow later (the D-076 defense pattern — record why the line is absent)."""
    from pathlib import Path
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert "gap_events" not in src and "memory_gap" not in src


# --- INVARIANT-06: the hook's analyze path stays byte-free ---------------------


def test_hook_prompt_path_writes_no_gap_event(temp_repo):
    """UserPromptSubmit calls analyze.analyze (the library) — a hook handler is
    read-only and the gap event belongs to the cz_analyze OP surface only."""
    from clauderizer.hook import handlers

    paths = P.resolve(temp_repo)
    with _chdir(temp_repo):
        out = handlers.user_prompt_submit({"prompt": GAP_PROBE, "cwd": str(temp_repo)})
    assert not paths.telemetry_file.exists()
    # and the hook printed no gap advisory either (quiet-when-empty holds)
    assert out is None or "gap" not in out.lower()


def test_analyze_library_function_writes_nothing(temp_repo):
    paths = P.resolve(temp_repo)
    analyze.analyze(paths, GAP_PROBE)
    assert not paths.telemetry_file.exists()


# --- corpus_health: read-only count; zero events render nothing extra ----------


def test_corpus_health_gap_events_zero_renders_nothing(temp_repo):
    paths = P.resolve(temp_repo)
    h = telemetry.corpus_health(paths, today="2026-07-28")
    assert h["gap_events"] == 0
    assert "gap" not in h["summary"].lower()


def test_corpus_health_counts_gap_events_read_only(temp_repo):
    paths = P.resolve(temp_repo)
    for _ in range(2):
        telemetry.record_gap(paths.telemetry_file, surface="cz_analyze",
                             gameplan="g", phase="1", query_terms=5,
                             today="2026-07-28")
    size_before = paths.telemetry_file.stat().st_size
    h = telemetry.corpus_health(paths, today="2026-07-28")
    assert h["gap_events"] == 2
    assert "2 memory gap(s)" in h["summary"]
    # read-only: the health read appended/altered nothing
    assert paths.telemetry_file.stat().st_size == size_before


def test_gap_suffix_is_the_only_summary_delta(tmp_path):
    """Twin corpora identical but for gap events: the summary differs ONLY by
    the gap suffix (plus the honest raw-event count) — the refusal_events
    precedent for quiet-when-zero surfacing."""
    a, b = tmp_path / "a", tmp_path / "b"
    for repo in (a, b):
        (repo / "docs").mkdir(parents=True)
        (repo / "docs" / "LESSONS.md").write_text(
            "## Lessons\n\n**L-01.** measure before building anything twice\n",
            encoding="utf-8")
    pb = P.resolve(b)
    telemetry.record_gap(pb.telemetry_file, surface="cz_analyze", gameplan="g",
                         phase="1", query_terms=3, today="2026-07-28")
    sa = telemetry.corpus_health(P.resolve(a), today="2026-07-28")["summary"]
    sb = telemetry.corpus_health(pb, today="2026-07-28")["summary"]
    assert "gap" not in sa.lower()
    # identical up to the honest raw-event count; then ONLY the gap suffix
    assert sb.startswith(sa.replace("0 telemetry event(s)", "1 telemetry event(s)"))
    assert "1 memory gap(s)" in sb
