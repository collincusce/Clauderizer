# windows-field-fixes-1.5.2 Gameplan

> Created: 2026-07-02
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

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Repro & fix all four field bugs

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Bug 1 cp1252: CLI + hook stdio never crash on unencodable glyphs (repro test with a cp1252 stream; glyphs degrade, exit codes unchanged)
- [x] Bug 2 frontmatter: depends_on: [] and inline [a, b] lists parse correctly — no dangling [ ] deps (tests)
- [x] Bug 3 add_decision: appending honors an existing Decisions section at a different heading depth instead of creating a duplicate ## Decisions at EOF (tests); newest-first insertion recorded as out-of-scope with reason
- [x] Bug 4 --run-cmd help states it is a launcher prefix (test or direct assert)
- [x] Full suite green

### Phase 1: Ship 1.5.2

**Goal**: D-011 ritual: suite green, PII sweep, PR, 9-cell CI green before tag, squash-merge, release-check 0, tag v1.5.2, Release, OIDC publish, PyPI + uvx verified; close-out with lessons.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] 9-cell CI green before tag; windows cells especially (the bugs are Windows-born)
- [x] release-check exit 0; tag v1.5.2; Release latest; OIDC publish green; PyPI 1.5.2 + uvx --refresh verified
- [x] Field-report win + bugs recorded in memory; gameplan closed, focus handed back
