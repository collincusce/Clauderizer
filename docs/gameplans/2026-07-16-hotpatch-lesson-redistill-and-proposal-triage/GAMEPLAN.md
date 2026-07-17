# hotpatch-lesson-redistill-and-proposal-triage Gameplan

> Created: 2026-07-16
> Status: Executing
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

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Lesson re-distill is promote-then-obsolete, append-only per INVARIANT-03

**Context**: 34 active project lessons exceed the 20 threshold; docs/LESSONS.md rides in every handoff across all gameplans. cz_lesson_health flags L-07, L-21, L-42 as high-utility promotion candidates and ~24 lessons as never-surfaced.
**Decision**: Cut under 20 by: (1) promote high-utility recurring lessons (L-07, L-21, L-42) to docs/LESSONS.md via cz_promote_lesson; (2) consolidate lexically-overlapping clusters via cz_consolidate_lessons; (3) cz_obsolete_lesson the never-surfaced/superseded entries. Promote before obsolete so enduring value survives.
**Consequences**: Nothing is hand-deleted — cz_obsolete_lesson marks stale while preserving the append-only record (INVARIANT-03). Handoff shrinks below the 20-lesson warning across the whole portfolio.
**Status**: active (2026-07-16)

## Open Items

**O-01.** Decide the no_standing_conditions proposal (no_standing_conditions:3f4873045bf1): the standing-curator loop gameplan declares no standing conditions. Phase 1 either declares threshold probes in .clauderizer/conditions.2026-06-21-standing-curator-loop-memory-maintenance.toml (e.g. project_lessons > 20, the very threshold this hotpatch fixes) so status can auto-propose iterations, or dismisses via cz_dismiss_proposal if not worth the machinery. Resolve to 0 pending proposals.

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
- [ ] cz_status reports active project lessons < 20 (memory.project_lessons)
- [ ] L-07, L-21, L-42 promoted to docs/LESSONS.md (cz_lesson_health promotion candidates actioned)
- [ ] No active lesson hand-deleted — obsoleted entries remain in the append-only record (INVARIANT-03)

### Phase 2: Triage the no_standing_conditions proposal

**Goal**: Resolve open item O-01: decide the pending no_standing_conditions proposal for the standing-curator loop gameplan — either declare threshold probes (e.g. project_lessons > 20) in its conditions TOML so status auto-proposes iterations, or dismiss via cz_dismiss_proposal. Land at 0 pending proposals.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_status / cz_modernize reports 0 pending proposals
- [ ] Open item O-01 resolved with a recorded rationale (declared probe or dismissed)

### Phase 3: Ship 1.8.1 release

**Goal**: Bump version 1.8.0 → 1.8.1, update changelog/docs, run cz_audit self-audit and cz_preflight, commit and tag the hotpatch release. Claude Code parity is unaffected (INVARIANT-07) — no engine code changes.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] pyproject.toml version == 1.8.1
- [ ] Changelog/release notes updated for 1.8.1
- [ ] cz_preflight passes and cz_audit run at close
- [ ] Release committed and tagged
