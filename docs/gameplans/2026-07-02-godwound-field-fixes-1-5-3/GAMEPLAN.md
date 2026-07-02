# godwound-field-fixes-1-5-3 Gameplan

> Created: 2026-07-02
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

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Repro & fix the three gameplan-machinery bugs

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Bug 1: a name already carrying an ISO-date prefix is not double-dated (test); tool description documents the always-dated behavior and how to pin the date
- [x] Bug 2: gameplan-scoped writes (add_phase and its siblings) hard-error on an unknown gameplan_id, listing the known ids — no silent shadow-gameplan scaffolding (tests)
- [x] Bug 3: phase-status parsing normalizes decorated statuses (emoji/dash-suffix variants of the known vocabulary); an unrecognized status yields an error naming what was found and the accepted vocabulary (tests)
- [x] Full suite green

### Phase 1: Ship 1.5.3

**Goal**: D-011 ritual: suite green, PII sweep, PR, 9-cell CI before tag, squash-merge, release-check 0, tag v1.5.3, Release, OIDC publish, PyPI + uvx verified; close-out.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] 9-cell CI green before tag; release-check exit 0; tag v1.5.3; Release latest; OIDC publish green; PyPI 1.5.3 + uvx --refresh verified
- [ ] Gameplan closed, focus handed back, memory updated
