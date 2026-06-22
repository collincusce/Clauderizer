# Chat Handoff Index — skill-awareness

> Last updated: 2026-06-22
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 573

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
| 0 | Skill model + SKILLS.md | ✅ COMPLETE | 2026-06-22 | 2026-06-22 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Skill discovery (propose-confirm) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Relevance surfacing | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Curation parity + docs + integration sweep | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Release 1.0.0rc1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-22

Built the skill model as a clean mirror of the lesson architecture (D1). New: markdown/skill_state.py (the single grammar for skill state + the entry fields name/description/source; states active|obsolete|superseded - the supersede-vs-promote divergence from lessons, since skills are already project-level); templates/docs/SKILLS.md (lazy-created from template like LESSONS.md); and the blessed writes mutations.register_skill (S-NN auto-id under a category, idempotent on name so repeat discovery proposals never duplicate) + mutations.obsolete_skill (append-only marker, idempotent). Exposed as cz_register_skill / cz_obsolete_skill via ops.REGISTRY + tools_list.TOOL_NAMES, inserted next to the lesson ops so parity holds. 13 new tests (grammar round-trip incl. mid-text-mention inertness; register/obsolete lifecycle; L-22 idempotency). Full suite 586 passed / 4 skipped / exit 0 - strictly additive, INVARIANT-07 honored. No tracked graph entities touched, so no cascade.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
