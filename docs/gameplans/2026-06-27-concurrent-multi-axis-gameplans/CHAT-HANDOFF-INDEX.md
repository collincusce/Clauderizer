# Chat Handoff Index — concurrent multi-axis gameplans

> Last updated: 2026-06-27
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

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
| 0 | Bootstrap and back-compat harness | ✅ COMPLETE | 2026-06-27 | 2026-06-27 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Focus model (concurrent gameplans + portfolio) | 🟢 READY | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Kinds as real profiles (parse + lexicon) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Per-kind / per-gameplan preflight | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Cross-gameplan dependencies and explicit scoping | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs, dogfood, release | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-27

Bootstrap + back-compat harness complete. Branched off main into feat/concurrent-multi-axis-gameplans (clean, 0/0 vs main). Captured the real baseline (629 passed / 4 skipped / 633 collected on v1.1.1) and corrected the inherited 663 figure (C-01: that was the abstract-index branch). Wrote tests/test_back_compat_focus.py: a frozen golden snapshot of the single-gameplan status digest + bundle (the byte-identical gate every later phase must keep green), plus legacy [active_gameplan] config load + rewrite round-trip stubs that Phase 1 extends when Config.focus lands. Full suite green at 633 passed. Design decisions D1-D6 already recorded at scaffold.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A SessionStart baseline reflects the focused gameplan's branch, not main; when a new initiative branches off main, re-measure the baseline on that branch rather than trusting the inherited digest figure.
