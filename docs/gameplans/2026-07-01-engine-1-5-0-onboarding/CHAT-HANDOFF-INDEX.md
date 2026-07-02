# Chat Handoff Index — engine-1.5.0-onboarding

> Last updated: 2026-07-01
> Status: All 5 phases complete

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
| 2 | Surfacing — init advisory + modernize proposal | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Skill + docs + version bumps | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Dogfood & ship 1.5.0 | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-01

Planned the 1.5.0 onboarding release. D-044 project ADR (assembly tool + skill; engine detects and prompts, agent reads and seeds; structure-based unseeded test) and D1 (engine 1.5.0 carries procedure 1.6.0; lean 5-phase arc). feat.onboarding entity upserted. Phases 1-4 with exit criteria. Baselines confirmed: engine 1.4.1 @ main 27df365, procedure 1.5.0, surface 44, suite 755 via green preflight on feat/engine-1.5.0-onboarding @ 4581a71. Key design facts pinned: templates are heading+placeholder shaped (VISION verified), sections.is_placeholder is the per-line predicate, init step 9 auto-ships any new assets/skills dir.

### Phase 1 — completed 2026-07-01

Detector + assembly tool shipped. onboard.py: spec_candidates walks well-known root files + docs/**/*.md excluding the engine-owned set (template names single-sourced from assets + owned dirs), returning paths+sizes only, empty/oversized skipped, capped at 25; unseeded_docs tests the ten prose docs (append-only logs excluded by design) with the meaningful-lines ⊆ current-template predicate — drift-proof where byte-identity would false-read; report() bundles unseeded + candidates + seeded_count + the seeding prompt naming the blessed writes and provenance discipline. cz_onboard registered read-only (surface 44→45, registry parity green, behavioral read-only gate covers it automatically, CLI schema verified live). Suite 761 (+6), first run green.

### Phase 2 — completed 2026-07-01

Surfacing shipped on both delivery paths. init: a new step 6b computes the onboarding signal right after doc scaffolding and appends one advisory to the new InitReport.advisories field (printed by the CLI as "→ …run cz_onboard or the clauderizer-onboard skill"), firing only when unseeded docs and spec candidates coexist — a bare repo stays silent (both tested). modernize: tier-2 gains the unseeded_docs proposal with the same predicate so every already-clauderized repo learns about onboarding at its next clauderize upgrade (D-042); seeding a doc clears it (tested). Suite 763 (+2), first run green.

### Phase 3 — completed 2026-07-01

Skill, docs, and versions shipped. clauderizer-onboard becomes the seventh packaged skill (read cz_onboard → read candidates → seed prose docs directly → entities/decisions/invariants with provenance → re-run to confirm → cz_status; distill-don't-transcribe judgment notes), with a test pinning that assets ship it and init drops it. Procedure template 1.5.0→1.6.0 with a changelog entry and an "Onboarding an Existing Project" section in human prose. Engine 1.4.1→1.5.0; CHANGELOG entry opens by keeping the two version lines straight ("engine 1.5.0 carries procedure 1.6.0"); README's init section gains the onboarding pointer. Jargon sweep clean; venv reinstalled; suite 764.

### Phase 4 — completed 2026-07-01

Dogfooded three ways and shipped. Scratch spec-rich repo: init printed the onboarding advisory and cz_onboard returned exactly unseeded=["docs/VISION.md"] with README.md + docs/design.md as candidates. This repo and marketing-studio: upgraded to procedure stamp 1.6.0 (procedure docs refreshed), zero false onboarding fires (their docs are real), prior proposals stable. Ritual clean end to end: PR #20 → 9-cell CI green before tag → squash-merge @ 6785b9477 → release-check 0 → tag v1.5.0 → Release latest → OIDC publish → PyPI 1.5.0 + uvx --refresh verified. feat.onboarding → 1.0.0/completed; scaffold/mcp-server/rituals MINOR-bumped. Suite 764.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
