# Chat Handoff Index — phasekeep-contract-asks

> Last updated: 2026-07-19
> Status: Phase 1 of 2 in progress

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 907

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
| 0 | Contract Surface | ✅ COMPLETE | 2026-07-19 | 2026-07-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Release and Verify | 🟡 IN PROGRESS | 2026-07-19 | — | handoffs/PHASE-1-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-19

Implemented the full PhaseKeep m0 ask set as one additive contract release-candidate. schema_version 1.0 stamps every registry result at the shared dispatch table (contract.py + ops.run_op; the status/gameplans/focus --json verbs now route through it, so CLI and MCP emit identical payloads). The monotonic revision lives in .clauderizer/revision.json (epoch + counter, atomic replace) and bumps at the byte-writer choke points: markdown writer, cascade-report writes, handoff writes, focus flips; no-op rewrites never bump, and status --json carries the record. Thirteen new registry ops land the read side of every append-only register (open items with resolutions, decisions/invariants/findings with supersession links both ways, lessons with curation state, corrections, amendments, phase_detail with per-criterion exit-criteria state and computed approval staleness, cascade reports with verdicts, docs index/doc reads, assignments, revision) plus cz_assign writes the provisional O-02 shape (gameplan Assignee header, phase Assigned line, config manager role). ops --list --json gives machine-readable introspection; graph entities carry structured depends_on_pins. The PhaseKeep CLAUDE.md truncation (their O-04) is fixed at the root: upsert_marker_block is now lossless, moving H1-headed foreign content below the block under a visible banner, with end-to-end init regression tests. Suite: 943 passed (36 new).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
