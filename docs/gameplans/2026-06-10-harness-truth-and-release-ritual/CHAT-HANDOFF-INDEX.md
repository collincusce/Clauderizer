# Chat Handoff Index — harness-truth-and-release-ritual

> Last updated: 2026-06-10
> Status: Phase 1 of 5 in progress

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 215

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Executor matrix: prove the wiring shape | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | hosts.py emits the immune shape; restart-validate H-08 | 🟡 IN PROGRESS | 2026-06-10 | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Doctor traverses the consumer leg (D-010) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Release preflight ritual (O3) and 1.0 readiness gates (O4) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Memory guardrails as config: O1 ACTIVE_LESSONS_WARN, O2 consolidation trigger | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Built scripts/wiring_matrix.ps1 and ran every candidate SessionStart command shape under the three Windows executors (Git Bash bash -c, cmd /c, PowerShell direct) with an in-band pass criterion (digest on stdout — exit codes untrusted, L-09) and, after round 1, a hostile cwd (C:\) by default. Verdict per D1/D2: shape C (//bin/sh //<repo>/.clauderizer/hook.sh) passes all three executors with zero quote surface and is chosen for Phase 1; shape A (sh -c 'exec …') also passes and is the recorded fallback; B (env-prefix) is bash-only; the CURRENT shape fails exactly and only under Git Bash, proving the harness detects H-08's failure (the control fires).

The bigger catch was incidental: round 1's entire cmd column failed not on argv shape but on working directory — cmd cannot hold the UNC project cwd, and clauderizer-hook discovers its repo FROM cwd, so the hook went silently empty (exit 0, both streams 0 bytes). Recorded as H-09 with an anchored-wrapper control proving the fix (cd <repo> in the generated wrapper → 758-byte digest from C:\ under all three executors). Phase 1 therefore ships two changes: the C shape in hosts.py AND the self-anchoring wrapper template; Phase 2 must make init/doctor probes spawn from a non-repo cwd. Gameplan lesson #1: debug every surprising matrix cell before reading the verdict (cwd and a fixture missing +x each confounded a full row/column).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Debug every surprising matrix cell before reading the verdict: a cell can fail for a reason orthogonal to what the matrix measures, and a column can be 100% confounded. Round 1's entire cmd.exe column failed on working-directory fallback (H-09), not argv shape; shape A's row failed on a fixture missing +x. Both initially read as "shape ineligible" — the truthful matrix needed the confound removed (anchored wrapper, executable fixture) and the criterion hardened (hostile cwd by default). Lesson #4's "prove the probe" applies cell-by-cell, not just to the harness as a whole.
