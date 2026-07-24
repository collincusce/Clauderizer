# Chat Handoff Index — workflow critique repairs — engine identity, ranker length bias, cascade yield, saturated telemetry

> Last updated: 2026-07-24
> Status: Phase 0 ready

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
| 0 | Engine identity — doctor certifies what it launched | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pre-flight stops arming its own failure; the baseline stops lying | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Adversarial ranking fixture — build the measuring stick before the fix | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Length-normalize the ranker and break the corpus ratchet | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Cascade self-resolves and stops blocking; utility scoring is parked | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, clean-environment verify, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A malformed tool-call argument lands in append-only memory as permanent render damage, because append-only plus never-hand-edit leaves no repair path — only a correction beside it. Validation is asymmetric: markup that displaces a required field is rejected harmlessly, while markup inside a present field writes clean-looking success over mangled content. Two cheap guards: reject argument values containing tool-call markup at write time (no legitimate ADR body contains a closing field tag), and re-read the RENDERED entry after any long structured write rather than trusting the ok:true result.
