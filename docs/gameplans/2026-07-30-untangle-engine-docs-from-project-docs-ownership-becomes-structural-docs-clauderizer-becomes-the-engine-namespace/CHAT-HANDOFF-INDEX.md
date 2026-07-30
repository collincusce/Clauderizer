# Chat Handoff Index — Untangle engine docs from project docs — ownership becomes structural, docs/clauderizer/ becomes the engine namespace

> Last updated: 2026-07-30
> Status: Phase 5 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1554

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
| 0 | Record the law — ownership taxonomy, the D-039 realization, and the compat gate | ✅ COMPLETE | 2026-07-30 | 2026-07-30 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Ownership becomes structural — the identity default | ✅ COMPLETE | 2026-07-30 | 2026-07-30 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Two glossaries, and the engine stops claiming names | ✅ COMPLETE | 2026-07-30 | 2026-07-30 | handoffs/PHASE-2-HANDOFF.md |
| 3 | The untangle — classify, git mv, conserve every entry | ✅ COMPLETE | 2026-07-30 | 2026-07-30 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Wire it to upgrade, and make an old engine say "upgrade" instead of "empty" | ✅ COMPLETE | 2026-07-30 | 2026-07-30 | handoffs/PHASE-4-HANDOFF.md |
| 5 | The 72 prose references — every surface that tells an agent where memory lives | 🟢 READY | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Prove it on the real corpus, then ship | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
