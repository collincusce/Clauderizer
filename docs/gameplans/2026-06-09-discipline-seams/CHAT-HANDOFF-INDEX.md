# Chat Handoff Index — Discipline Seams

> Last updated: 2026-06-09
> Status: Phase 0 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 99

## Ending Protocol

1. Update PHASE-STATUS.md (status + outputs + corrections).
2. `cz_add_lesson` for anything new.
3. `cz_transition_status` on touched entities (fires cascade).
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Blessed cascade resolution & lesson obsolescence | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

| 1 | Marker-protected handoff regeneration | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |

| 2 | Fresh baseline & completed-gameplan status | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-2-HANDOFF.md |

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Design

**1.** Auto-numbering must not count IDs that only appear in scaffold placeholder prose — strip placeholders before scanning, or use ID patterns anchored to heading lines.

**2.** A context fetch should return the merged on-disk view, not just freshly generated content — cz_next_phase_context now includes agent enrichment living outside the marker block.

**5.** Cascade report filenames are date+entity, so two same-day cascades of one entity silently overwrite the earlier report — report_filename needs a time or sequence component (candidate next fix).

### Category: Integration

**3.** Every file the engine writes must round-trip through its own parser in tests; silent fallback on config parse errors is a footgun — surface it (doctor now checks the lock parses). (promoted 2026-06-09: L-04)

**4.** Host profile commands can double flags the project config already supplies (pytest -q + addopts -q = -qq kills the count summary) — verify the baseline regex matches real output when wiring a repo.
