"""Phase 1 — per-lesson empirical health (utility / failure-risk / signal) joined
from telemetry. Deterministic, read-only (INVARIANT-05). Includes the held-out
labeled-sample check: the advisory signal must agree with constructed ground
truth (good lessons -> promotion candidate, bad -> review, unused -> never)."""

from __future__ import annotations

from clauderizer import ops, telemetry
from clauderizer import paths as P


def _repo_with_lessons(tmp_path, ids):
    repo = tmp_path / "repo"
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"**{i}.** lesson {i} about something durable *(from g)*" for i in ids)
    doc.write_text("## Lessons\n\n" + body + "\n", encoding="utf-8")
    return repo


def _surface(paths, phase, ids):
    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase=phase,
                              lessons=ids, invariants=[], today="2026-06-21")


def _outcome(paths, phase, status):
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase=phase,
                             status=status, criteria_total=1,
                             criteria_checked=1 if status == "complete" else 0,
                             today="2026-06-21")


def test_utility_and_failure_risk_join(tmp_path):
    repo = _repo_with_lessons(tmp_path, ["L-01", "L-02", "L-03"])
    paths = P.resolve(repo)
    for p in ("1", "2", "3"):                       # L-01: surfaced -> always passed
        _surface(paths, p, ["L-01"]); _outcome(paths, p, "complete")
    for p in ("4", "5", "6"):                       # L-02: surfaced -> always failed
        _surface(paths, p, ["L-02"]); _outcome(paths, p, "failed")
    # L-03 never surfaced.
    h1 = telemetry.lesson_health(paths)
    h2 = telemetry.lesson_health(paths)
    assert h1 == h2                                  # deterministic
    by = {r["id"]: r for r in h1["scores"]}
    assert by["L-01"]["utility"] == 1.0 and by["L-01"]["failure_risk"] == 0.0
    assert by["L-02"]["utility"] == 0.0 and by["L-02"]["failure_risk"] == 1.0
    assert by["L-03"]["utility"] is None and by["L-03"]["surfaced_count"] == 0


def test_signals_agree_with_labeled_sample(tmp_path):
    repo = _repo_with_lessons(tmp_path, ["L-01", "L-02", "L-03"])
    paths = P.resolve(repo)
    for p in ("1", "2", "3"):
        _surface(paths, p, ["L-01"]); _outcome(paths, p, "complete")
    for p in ("4", "5", "6"):
        _surface(paths, p, ["L-02"]); _outcome(paths, p, "failed")
    by = {r["id"]: r for r in telemetry.lesson_health(paths)["scores"]}
    assert "promotion candidate" in by["L-01"]["signal"]   # good -> promote
    assert "review" in by["L-02"]["signal"]                # bad -> review
    assert "never-surfaced" in by["L-03"]["signal"]        # unused -> never


def test_unresolved_surfacing_has_no_utility_yet(tmp_path):
    """Surfaced but the phase hasn't completed -> no signal, utility None."""
    repo = _repo_with_lessons(tmp_path, ["L-01"])
    paths = P.resolve(repo)
    _surface(paths, "1", ["L-01"])                   # no outcome recorded
    r = telemetry.lesson_health(paths)["scores"][0]
    assert r["surfaced_count"] == 1 and r["resolved_count"] == 0
    assert r["utility"] is None and r["signal"] is None


def test_window_limits_recency(tmp_path):
    repo = _repo_with_lessons(tmp_path, ["L-01"])
    paths = P.resolve(repo)
    for p in ("1", "2"):                             # 2 early failures
        _surface(paths, p, ["L-01"]); _outcome(paths, p, "failed")
    for p in ("3", "4"):                             # 2 recent passes
        _surface(paths, p, ["L-01"]); _outcome(paths, p, "complete")
    full = telemetry.lesson_health(paths)["scores"][0]
    windowed = telemetry.lesson_health(paths, window=2)["scores"][0]
    assert full["utility"] == 0.5
    assert windowed["utility"] == 1.0               # only the 2 most-recent surfacings

# cz_lesson_health's registration + name parity is the test_ops.py gate
# (REGISTRY == TOOL_NAMES + signature-drift); its read-only-ness is proven
# behaviorally in tests/test_read_only_ops.py — not by a tautological flag assert.
