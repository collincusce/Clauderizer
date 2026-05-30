# Chat Handoff Index — Clauderizer v1 Bootstrap

> Last updated: 2026-05-30
> Status: Phase 0 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

## Ending Protocol

1. Update PHASE-STATUS.md (status + outputs + corrections).
2. `cz_add_lesson` for anything new.
3. `cz_transition_status` on touched entities (fires cascade).
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**3.** Markdown round-trip idempotency (apply-twice==apply-once) is the load-bearing test for every mutation.

**4.** Make init idempotent via marker blocks, key-scoped JSON merges, and exists-checks — never clobber user content.

### Category: Build

**1.** Keep the core dependency-free: a vendored frontmatter parser beats a PyYAML dep for a drop-in.

**2.** FastMCP may not structure deeply-nested tool returns — keep returns shallow; write big artifacts to disk.

**5.** Prefer vendoring a tiny parser over a dependency when portability is the point.
