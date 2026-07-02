# Chat Handoff Index — engine-1.5.0-onboarding

> Last updated: 2026-07-01
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 755

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
| 0 | Plan, baselines & commit | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Detector + cz_onboard assembly tool | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Surfacing — init advisory + modernize proposal | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Skill + docs + version bumps | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Dogfood & ship 1.5.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-01

Planned the 1.5.0 onboarding release. D-044 project ADR (assembly tool + skill; engine detects and prompts, agent reads and seeds; structure-based unseeded test) and D1 (engine 1.5.0 carries procedure 1.6.0; lean 5-phase arc). feat.onboarding entity upserted. Phases 1-4 with exit criteria. Baselines confirmed: engine 1.4.1 @ main 27df365, procedure 1.5.0, surface 44, suite 755 via green preflight on feat/engine-1.5.0-onboarding @ 4581a71. Key design facts pinned: templates are heading+placeholder shaped (VISION verified), sections.is_placeholder is the per-line predicate, init step 9 auto-ships any new assets/skills dir.

### Phase 1 — completed 2026-07-01

Detector + assembly tool shipped. onboard.py: spec_candidates walks well-known root files + docs/**/*.md excluding the engine-owned set (template names single-sourced from assets + owned dirs), returning paths+sizes only, empty/oversized skipped, capped at 25; unseeded_docs tests the ten prose docs (append-only logs excluded by design) with the meaningful-lines ⊆ current-template predicate — drift-proof where byte-identity would false-read; report() bundles unseeded + candidates + seeded_count + the seeding prompt naming the blessed writes and provenance discipline. cz_onboard registered read-only (surface 44→45, registry parity green, behavioral read-only gate covers it automatically, CLI schema verified live). Suite 761 (+6), first run green.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
