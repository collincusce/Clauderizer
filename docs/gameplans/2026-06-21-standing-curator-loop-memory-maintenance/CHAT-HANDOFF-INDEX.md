# Chat Handoff Index — Standing curator loop - memory maintenance

> Last updated: 2026-07-28
> Status: All 1 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1516

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
| 0 | Iterate | ✅ COMPLETE | 2026-07-28 | 2026-07-28 | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Design

**1.** The file boundary is adversarial in BOTH directions, and the tests belong in the same phase that makes the robustness claim. Write side: round-trip idempotency (apply-twice == apply-once) through the engine's own parser is the load-bearing test for every mutation — every file the engine writes must round-trip through its parser in tests, and config parse errors are never swallowed silently — but necessary is NOT sufficient: an engine can read its own corruption indefinitely, so also assert render-validity for EXTERNAL readers (contiguous tables, valid markdown). Read side: a 'degrades gracefully' claim is only as strong as the input diversity it was tested against (non-dict valid JSON, BOM/CRLF, unicode, empty), and tolerance must wrap the WHOLE pipeline, not just json.loads — guard the file decode before it (non-UTF-8 bytes -> UnicodeDecodeError) and the shape after it (an unhashable dict key, a non-str field in str.join), netting per-item in any batch loop so one bad input never aborts the run. Corollary: a regex encoding a domain rule must encode it precisely ([1-9]\d* failed, never \d+ failed). (Consolidates L-24, L-52.) *(evidence: thematic re-distill under L-67's coverage gate; consolidates L-24, L-52 at 2/2 pre-apply coverage (k=5, rank 1 both))* (promoted 2026-07-28: L-69)
