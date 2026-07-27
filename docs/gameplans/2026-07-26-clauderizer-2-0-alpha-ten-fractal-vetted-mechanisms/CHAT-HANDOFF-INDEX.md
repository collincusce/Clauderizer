# Chat Handoff Index — clauderizer 2.0 alpha — ten fractal-vetted mechanisms

> Last updated: 2026-07-26
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1330

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
| 0 | Honest endings and epistemics | ✅ COMPLETE | 2026-07-26 | 2026-07-26 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Lifecycle detectors | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Live state and budgets | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Attention and consolidation | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Integrity and enforcement | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Evidence matrix and graduation | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Close-out and ship 2.0.0a1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Fleet pattern: glossary, skill, productization | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-26

Both phase-0 mechanisms landed under their binding conditions (research-fractal-vetting.json), tests-first. Honest terminal vocabulary: the status matcher became positional (earliest word-boundary match wins, longest on tie) — killing a LIVE laundering path where dict-order matching read "DEFERRED — call it done" as COMPLETE via the trailing word; `deferred` joined the write vocabulary (⏸️ DEFERRED, reason after the em-dash, engine token leads, empty-safe sanitizer) with exited/abandoned/superseded/wontfix as aliases INTO it and a ratchet test pinning exactly seven statuses; tracker headers now mirror _lifecycle's closed set (COMPLETE+DEFERRED renders "Complete", all-deferred "Deferred"); completing over unchecked criteria names the deferred alternative while the deferred door itself never nags (INVARIANT-05, no flags); deferred is a telemetry terminal outcome carrying reason, making pass_rate an honest goal-met rate. Procedure 1.9.0→1.10.0 (three-way close-out documented), both skill copies + ops docstring in the same commit (MCP schema auto-derives).

Unknowable-never-zero epistemics: the four conflation sites are fixed with the missing-arm tests written first and RED confirmed before implementation — probes that could not run are `unevaluable` (met stays boolean, additive field); preflight warns "cannot trip" on armed-but-unrunnable guards, contains a raising runner as UNKNOWN-not-pass with additive verdict/gates_unrun fields; curator consolidation stops coercing unmeasured utility to 0.0 (evidence text names the unmeasured side); staleness ages carry a hedged "~N active day(s)" only once a stale set exists, with no claim on any git failure. The corpus sweep ratchet ran green over the real trackers (all flips move toward open/deferred). Bonus proof the enforcement stack works: the L-68 separator ratchet fired on two new message-class assertions mid-phase and forced their classification (baseline 40→42). Suite 1330→1379, zero failures; commit 184c353.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
