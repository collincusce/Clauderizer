"""Phase 4 — the loop-gameplan primitive: cz_loop_step (one iteration = convergence
metric + curator proposals + converged flag + spawn-gameplan escape hatch), the
K-iteration convergence proof, and kind=loop creation. Read-only, deterministic
(INVARIANT-05 / D-018)."""

from __future__ import annotations

import os

from clauderizer import ops, telemetry
from clauderizer import paths as P


def _surface(paths, phase, project):
    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase=phase,
                              lessons=project, invariants=[], gameplan_lessons=[],
                              today="2026-06-21")


def _outcome(paths, phase, status):
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase=phase,
                             status=status, criteria_total=1,
                             criteria_checked=1 if status == "complete" else 0,
                             today="2026-06-21")


def test_loop_converges_over_iterations(temp_repo):
    """Drive the loop (loop_step -> apply obsolete proposals -> repeat). Proposals
    converge to zero and the corpus-health metric is monotone non-increasing."""
    doc = temp_repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + "\n".join([
        "**L-01.** always run the full pytest suite before any irreversible release *(from g)*",
        "**L-02.** always run the full pytest suite before every irreversible release step *(from g)*",
        "**L-03.** a wholly unrelated lesson never surfaced anywhere distinct *(from g)*",
        "**L-04.** prefer the Write tool over heredocs for release notes distinct *(from g)*",
    ]) + "\n", encoding="utf-8")
    paths = P.resolve(temp_repo)
    # L-01/L-02/L-04 surfaced + passing (healthy, not never-surfaced); L-03 never.
    _surface(paths, "1", ["L-01", "L-02", "L-04"]); _outcome(paths, "1", "complete")

    metrics = []
    converged = False
    for _ in range(6):                                       # K-iteration guardrail
        step = telemetry.loop_step(paths)
        metrics.append((step["metric"]["redundant_pairs"], step["metric"]["never_surfaced"]))
        if step["converged"]:
            converged = True
            break
        batch = [{"op": "cz_obsolete_lesson", "args": p["suggested_args"]}
                 for p in step["proposals"]
                 if p["action"] in ("consolidate", "obsolete")
                 and p.get("suggested_op") == "cz_obsolete_lesson"]
        cwd = os.getcwd(); os.chdir(temp_repo)
        try:
            _res, ok = ops.run_batch(batch)
            assert ok, _res
        finally:
            os.chdir(cwd)

    assert converged
    reds = [m[0] for m in metrics]
    nevs = [m[1] for m in metrics]
    assert reds == sorted(reds, reverse=True)                # monotone non-increasing
    assert nevs == sorted(nevs, reverse=True)
    assert reds[-1] == 0                                     # fully de-duplicated at convergence


def test_loop_step_suggests_spawn_for_many_flags(tmp_path):
    """Many review-flags in one iteration -> escape hatch suggests a driven gameplan."""
    repo = tmp_path / "repo"
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("## Lessons\n\n" + "\n".join([
        "**L-01.** alpha scheduling subsystem retries jitter backoff timing *(from g)*",
        "**L-02.** beta rendering pipeline shader rasterization viewport *(from g)*",
        "**L-03.** gamma authentication token session credential issuer *(from g)*",
    ]) + "\n", encoding="utf-8")
    paths = P.resolve(repo)
    for ph, st in (("1", "complete"), ("2", "failed"), ("3", "complete"), ("4", "failed")):
        _surface(paths, ph, ["L-01", "L-02", "L-03"]); _outcome(paths, ph, st)   # utility 0.5 -> flag
    step = telemetry.loop_step(paths)
    assert step["spawn_gameplan"] is not None
    assert step["spawn_gameplan"]["suggested_op"] == "cz_create_gameplan"
    assert len(step["spawn_gameplan"]["lessons"]) >= 3


def test_create_loop_gameplan_records_kind(temp_repo):
    cwd = os.getcwd(); os.chdir(temp_repo)
    try:
        res, ok = ops.run_batch([{"op": "cz_create_gameplan",
                                  "args": {"name": "standing curator loop", "kind": "loop"}}])
    finally:
        os.chdir(cwd)
    assert ok, res
    gid = res[0]["result"]["gameplan_id"]
    gp = (temp_repo / "docs" / "gameplans" / gid / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "> Kind: loop" in gp
