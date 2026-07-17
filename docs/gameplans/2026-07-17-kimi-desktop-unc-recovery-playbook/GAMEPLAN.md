# kimi-desktop-unc-recovery-playbook Gameplan

> Created: 2026-07-17
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

### Phase 0: Agent-recovery guide + doctor warning for the WSL/UNC combo

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] setup_guide() expanded into an agent playbook: MCP entry + a 'shell/tools failing' section (why=UNC cwd; work-now=file tools + UNC paths + read docs/, avoid CLI/bash; fix=repo on Windows OR Kimi Code CLI in WSL)
- [x] init emits the guide into .clauderizer/ when it detects the WSL-repo + Windows-side daimon combo (not only on write-failure), so a spawn-broken agent can read it
- [x] doctor warns loudly for the WSL+Windows-desktop combo and points at the guide
- [x] Tests: guide contains the recovery playbook; init emits it on the WSL combo; doctor warns
- [x] Full suite green in a fresh venv

### Phase 1: Ship 1.9.1, dogfood close, release

**Goal**: CHANGELOG 1.9.1; bump pyproject + __version__ to 1.9.1 lockstep. Bump subsys.scaffold; cascade + resolve. Verify fresh venv. Close via clauderizer-close-gameplan skill (cz_audit). Release: merge to main -> tag v1.9.1 -> CI green -> GitHub Release -> PyPI -> verify.
**Depends on**: Agent-recovery guide + doctor warning for the WSL/UNC combo.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] CHANGELOG 1.9.1; pyproject AND __version__ bumped to 1.9.1 in lockstep (cz_audit clean)
- [x] subsys.scaffold bumped; cascade resolved
- [x] Gameplan closed via the close skill with cz_audit run; post-mortem written
- [ ] Released: tag v1.9.1, CI green, GitHub Release, clauderizer 1.9.1 verified live on PyPI
