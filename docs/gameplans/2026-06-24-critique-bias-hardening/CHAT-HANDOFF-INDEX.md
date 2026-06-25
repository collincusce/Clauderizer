# Chat Handoff Index — critique-bias-hardening

> Last updated: 2026-06-24
> Status: All 1 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 620

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
| 0 | CALM self-enhancement + authority checks | ✅ COMPLETE | 2026-06-24 | 2026-06-24 | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-24

Prototyped two CALM-derived advisory bias checks in the cz_critique reference-free rubric (D1): self-enhancement (a resolved open item closed by a hollow note, or a completion claim that outruns a live gap — the critique target is always self-authored) and authority (a lesson whose D-017 evidence cites an unverifiable external source with no in-repo anchor). Both enter as deterministic, stdlib-re surfacing: 3 pure classifiers (_evidence_is_authority / _resolution_is_hollow / _overclaims), each paired with an in-repo-anchor precision guard, wired as two appended dimensions. No new dependency, no enable/disable flag, advisory only (INVARIANT-05; follows D-017's STORM precedent; reinforces D-013).

Built the measuring stick FIRST (O-01): a 32-case labeled fixture with adversarial near-misses plus a measure.py harness comparing the shipped classifiers against a deliberately naive strawman and the prior (no-axis) rubric. Result: 100% detection (17/17) of planted bias the prior rubric scored clean, 0 false-positives on 15 sound cases, and — the property that makes the result credible rather than teaching-to-the-test — the principled detector beats the naive strawman on 6/7 near-misses (naive 20-50% FP). Full suite 626 passed (620 baseline + 6 new critique tests), 0 failures; live cz_critique stays clean on the real gameplan. Gate verdict: KEEP. Earned gameplan lesson #1 (a self-authored fixture must be able to fail a naive baseline, or its 100% is confirmation bias). Change kept on branch experiment/critique-bias-hardening, ready for review/merge.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A self-authored eval fixture proves a detector works only if the fixture can also FAIL a naive baseline. A 100%-detection / 0%-FP result on a fixture you wrote is suspicious by construction (the confirmation-bias trap behind L-32/L-39 — you may be teaching to the test). The remedy is discriminating power: seed adversarial NEAR-MISSES (a long-but-hollow note; a paper citation that is ALSO in-repo-anchored; a factual "all criteria met" with no intensifier) and run a deliberately NAIVE strawman detector alongside the real one. The gain is credible only if the principled detector beats the strawman ON the near-misses (a real mechanism — here, an in-repo-anchor guard), not merely beats the prior no-check baseline (which is a tautology: anything beats zero). Extends L-39: don't just build the adversarial fixture first — build a strawman the fixture must defeat. *(evidence: 2026-06-24-critique-bias-hardening phase 0: principled 100% det / 0% FP vs naive 20-50% FP; on 7 near-misses naive wrong on 6, principled wrong on 0 (_experiments/results.json via measure.py); full suite 626 passed)* (promoted 2026-06-24: L-40)
