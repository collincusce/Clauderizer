# Chat Handoff Index — evidence traversal 1.14.0

> Last updated: 2026-07-25
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1002

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
| 0 | Single-source the status parser and expose defaulted status | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | One atomic symlink-refusing write path for tracked markdown | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Well-formedness at the write boundary | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Implement D-063 so the curator stops proposing from absent evidence | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Resolve H-20 with capability-not-presence engine identity | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Preserve foreign config and converge existing installs | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Restore full lesson propagation, close H-19, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-25

Single-sourced the entry-status grammar and made defaulting observable, which closed the reframing defect: cz_list_findings went from 21 findings all reading "active" with a null date to 17 resolved / 4 open with every date populated and 21/21 status_source="parsed". Three readers each carried their own **Status** pattern and only graph/abstract_index.py tolerated the "- **Status**:" list bullet that add_finding emits — so the fix was promoting the correct copy, not writing a new one. It lives in markdown/sections.py because that module imports only `re`: analyze.py imports graph.index, which forces abstract_index to import analyze lazily, so analyze structurally cannot host a module-level regex. Shipped the two seam tests (test_canonical_parsers, test_render_roundtrip), the per-register parse reconciliation, open-findings surfacing in cz_critique and the digest, and the shared L-24 adversarial fixture. Suite 1002 to 1016.

Two criteria closed as NOT-APPLICABLE rather than faked, and one open item deliberately left unresolved. (1) The contract-fixture regeneration criterion does not apply: that fixture's HARDENING corpus contains zero Status lines, so "active"/null is the honest output there, and test_contract_corpus compares a key SUPERSET which already tolerates the added status_source key — nothing to regenerate. (2) The criterion text says "20 findings, 3 open"; it is 21 and 4 because H-21 was recorded after the plan was written — correct evolution, not a miss. (3) O-04 (the 27 founding decisions carry no date) stays open by design: the reconciliation now reports them as "defaulted", which is the correct and honest classification, and backfilling dates is deferred to 1.14.1 because the ordering only matters to the parked ranker work. Every new test was demonstrated RED on a detached worktree at pre-1.14.0-writepath before being green here; that harness is recorded as an output for the remaining phases.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
