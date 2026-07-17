# hotpatch-lesson-redistill-and-proposal-triage Gameplan

> Created: 2026-07-16
> Status: Complete
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

### A-001 — Phase 3 folds in the H-18 code fix so 1.8.1 has a real payload

- **Date**: 2026-07-16
- **Affected sections in GAMEPLAN.md**: Phase Breakdown (Phase 3), Decisions
- **Affected phases**: 3
- **Triggered by**: Phase 1 dogfooding surfaced H-18; Phase 3 review found no shipped src/ code changed, so a 1.8.1 PyPI release would be byte-identical to 1.8.0. User chose to fold in the H-18 fix.
- **What changed**: Expand Phase 3 beyond version/changelog: fix the obsolete/promoted marker parser in src/clauderizer/markdown/lesson_state.py so a reason containing parentheses no longer makes the lesson parse as ACTIVE, add a regression test, resolve H-18, then bump 1.8.1, changelog, cz_audit/cz_preflight, commit, tag and push to CI/PyPI.
- **Why**: A release must carry a real payload (L-50/L-51). The H-18 memory-correctness bug — an obsoleted lesson silently keeps riding every handoff — is exactly the substance a 1.8.1 patch should ship, and it was found by dogfooding this gameplan.

## Decisions

### D1 — Lesson re-distill is promote-then-obsolete, append-only per INVARIANT-03

**Context**: 34 active project lessons exceed the 20 threshold; docs/LESSONS.md rides in every handoff across all gameplans. cz_lesson_health flags L-07, L-21, L-42 as high-utility promotion candidates and ~24 lessons as never-surfaced.
**Decision**: Cut under 20 by: (1) promote high-utility recurring lessons (L-07, L-21, L-42) to docs/LESSONS.md via cz_promote_lesson; (2) consolidate lexically-overlapping clusters via cz_consolidate_lessons; (3) cz_obsolete_lesson the never-surfaced/superseded entries. Promote before obsolete so enduring value survives.
**Consequences**: Nothing is hand-deleted — cz_obsolete_lesson marks stale while preserving the append-only record (INVARIANT-03). Handoff shrinks below the 20-lesson warning across the whole portfolio.
**Status**: active (2026-07-16)

### D2 — Declare a standing condition for the curator loop rather than dismiss the proposal

**Context**: The no_standing_conditions advisory flagged that the standing-curator-loop-memory-maintenance loop gameplan declared no standing conditions, so status never proposed iterations for it. Standing conditions are shell probes: exit 0 means met and an iteration is proposed, advisory-only per INVARIANT-05.
**Decision**: Declare a probe rather than dismiss. Added conditions.2026-06-21-standing-curator-loop-memory-maintenance.toml with lessons_over_threshold, a shell test that trips when active docs/LESSONS.md lessons exceed 20 — the exact drift this hotpatch fixed. The loop now self-arms for future memory bloat.
**Consequences**: status, cz_preflight, and cz_loop_step will surface an iteration proposal when the corpus drifts past 20 active lessons; nothing auto-runs. The conditions file is host-agnostic config the engine reads, not a tracked corpus log.
**Status**: active (2026-07-16)

## Open Items

**O-01.** Decide the no_standing_conditions proposal (no_standing_conditions:3f4873045bf1): the standing-curator loop gameplan declares no standing conditions. Phase 1 either declares threshold probes in .clauderizer/conditions.2026-06-21-standing-curator-loop-memory-maintenance.toml (e.g. project_lessons > 20, the very threshold this hotpatch fixes) so status can auto-propose iterations, or dismisses via cz_dismiss_proposal if not worth the machinery. Resolve to 0 pending proposals. _(resolved 2026-07-16: Declared, not dismissed. Wrote .clauderizer/conditions.2026-06-21-standing-curator-loop-memory-maintenance.toml with one shell probe lessons_over_threshold that exits 0 when active docs/LESSONS.md lessons exceed 20 — so status/preflight/loop_step auto-propose a curator iteration when memory bloats again. Standing conditions are shell probes evaluated at repo root, exit 0 == met, advisory-only per INVARIANT-05. Verified: TOML parses, probe returns not-met at the current 19, and cz_modernize now reports 0 advisory proposals.)_

## Phase Breakdown

### Phase 0: Bootstrap

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: Re-distill lessons under the 20 threshold

**Goal**: Promote high-utility recurring lessons (L-07, L-21, L-42) to docs/LESSONS.md, consolidate lexically-overlapping clusters, and obsolete never-surfaced/superseded entries — bringing active project lessons under 20 while preserving the append-only record (INVARIANT-03). Verify with cz_lesson_health / cz_status.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_status reports active project lessons < 20 (memory.project_lessons)
- [x] L-07, L-21, L-42 promoted to docs/LESSONS.md (cz_lesson_health promotion candidates actioned)
- [x] No active lesson hand-deleted — obsoleted entries remain in the append-only record (INVARIANT-03)

### Phase 2: Triage the no_standing_conditions proposal

**Goal**: Resolve open item O-01: decide the pending no_standing_conditions proposal for the standing-curator loop gameplan — either declare threshold probes (e.g. project_lessons > 20) in its conditions TOML so status auto-proposes iterations, or dismiss via cz_dismiss_proposal. Land at 0 pending proposals.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_status / cz_modernize reports 0 pending proposals
- [x] Open item O-01 resolved with a recorded rationale (declared probe or dismissed)

### Phase 3: Ship 1.8.1 release

**Goal**: Bump version 1.8.0 → 1.8.1, update changelog/docs, run cz_audit self-audit and cz_preflight, commit and tag the hotpatch release. Claude Code parity is unaffected (INVARIANT-07) — no engine code changes.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] pyproject.toml version == 1.8.1
- [x] Changelog/release notes updated for 1.8.1
- [x] cz_preflight passes and cz_audit run at close
- [ ] Release committed and tagged
