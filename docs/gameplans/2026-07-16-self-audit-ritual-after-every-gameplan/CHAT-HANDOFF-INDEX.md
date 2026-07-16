# Chat Handoff Index — self-audit-ritual-after-every-gameplan

> Last updated: 2026-07-16
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 799

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
| 0 | Design the cz_audit work/release self-audit gate | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Implement rituals/audit.py + register cz_audit | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wire cz_audit into the shipped close skill + procedure | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Dogfood, ship 1.8.0, close | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-16

Designed cz_audit as a new advisory work/release gate distinct from cz_critique (memory). Split settled: deterministic signals = version single-sourcing (pyproject vs pkg __version__ vs top CHANGELOG heading), dirty git tree, pending cascades + unresolved open items; judgment checklist = clean-environment verification, consumer re-audit, claim honesty, shipped-artifact reality. Return shape mirrors cz_critique. Design captured in D-051.

### Phase 1 — completed 2026-07-16

Implemented rituals/audit.py (read-only, stdlib-only, advisory) and registered cz_audit via ops.cz_audit()/REGISTRY(writes=False)/tools_list — auto-exposed to the MCP server and CLI. Added tests/test_audit.py (6 tests) proving the version-drift signal fires on the exact pyproject-vs-__version__ 1.7.0/1.6.0 bug and on changelog drift, and stays quiet when consistent or when sides are missing (L-25 both-directions). Suite 799->805 passed, green in a fresh venv; live smoke confirmed no false positive on the consistent repo.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
