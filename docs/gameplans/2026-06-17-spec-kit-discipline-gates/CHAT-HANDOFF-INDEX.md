# Chat Handoff Index — spec-kit-discipline-gates

> Last updated: 2026-06-17
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 266

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
| 0 | Clarify gate: structured open items (O-NN) + judgment-based surfacing | ✅ COMPLETE | 2026-06-17 | 2026-06-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Exit-criteria gate: machine-checkable phase criteria + surfacing at completion | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Analyze gate: surface conflicting invariants/decisions for agent judgment | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Integration & docs: wire gates into rituals/skills/digest, document to code | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-17

Phase 0 shipped the clarify gate: structured open items. Two blessed mutations — add_open_item (auto-numbered O-NN appended to the GAMEPLAN 'Open Items' section via next_numbered_id + append_to_section, with an optional phase tag) and resolve_open_item (idempotent in-place _(resolved date: ...)_ marker, never deletes) — exposed as cz_add_open_item / cz_resolve_open_item on the shared MCP+CLI registry (parity test green). cz_status now reports unresolved open items (bundle['open_items'] + a digest line), and transition_phase to complete surfaces the unresolved items relevant to that phase in a new result['advisories']=[{kind,ids,message}] field: advisory and non-blocking per INVARIANT-05, and the shared surfacing shape Phases 1-2 reuse. All per D-015 (no config flags, judgment-based) and D1 (reuse existing markdown conventions, no new schema). Suite 266 -> 273 (+7), 4 skipped, zero regressions.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When an exploration subagent maps an unfamiliar codebase to ground a plan, treat its file:line claims as leads to verify, not facts. The spec-kit-gates map asserted tests/test_blessed_surfaces.py held the MCP/CLI parity test; it was actually tests/test_ops.py (test_registry_is_exactly_the_tool_surface), so editing on the map alone would have changed the wrong test. Fan-out exploration locates code fast; confirm which file does what at the point of edit.
