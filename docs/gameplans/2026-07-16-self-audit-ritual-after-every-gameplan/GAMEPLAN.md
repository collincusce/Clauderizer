# self-audit-ritual-after-every-gameplan Gameplan

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

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Design the cz_audit work/release self-audit gate

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] The mechanical vs judgment split is decided and written: which signals are deterministic (version single-sourcing, dirty tree, unresolved cascades/open-items, artifact-claim reality, changed-entities-missing-cascade) vs prompted checklist (clean-env, consumer re-audit, claim honesty)
- [x] cz_audit output shape is specified, mirroring cz_critique/cz_analyze (assemble signals + prompt; read-only; advisory; stdlib-only; INVARIANT-05)
- [x] Confirmed cz_audit is a NEW tool distinct from cz_critique (memory) and does not duplicate preflight's git checks beyond what's needed

### Phase 1: Implement rituals/audit.py + register cz_audit

**Goal**: Build rituals/audit.py: assemble deterministic work/release signals (version single-sourcing pyproject==__version__==metadata; dirty/untracked tree; unresolved cascades+open items; shipped-artifact/claim reality; changed-tracked-entities missing cascade) + a judgment checklist (clean-env verification, consumer re-audit, claim honesty). Read-only, stdlib-only, advisory (INVARIANT-05) — mirrors cz_critique's assemble-and-prompt shape. Register cz_audit in tools_list, mcp_server, and cli. Tests incl. one proving the version-mismatch signal fires on the exact 1.7.0/1.6.0 drift.
**Depends on**: Design the cz_audit work/release self-audit gate.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] rituals/audit.py implements the gate: read-only, stdlib-only, returns assembled signals + judgment checklist (no scoring/blocking, INVARIANT-05)
- [x] The version-single-sourcing signal detects pyproject != __version__ (a regression test reproduces the exact 1.7.0-vs-1.6.0 drift and asserts cz_audit flags it)
- [x] cz_audit is registered in tools_list, mcp_server, and cli and is callable end-to-end
- [x] Full suite green in a fresh venv (not just the working .venv)

### Phase 2: Wire cz_audit into the shipped close skill + procedure

**Goal**: Add a self-audit step to the shipped clauderizer-close-gameplan skill (src/clauderizer/skills/...) and to GAMEPLAN-PROCEDURE.md (Ending Protocol + Procedure: Close a Gameplan), so cz_audit runs at every gameplan close on ALL installs. Bump PROCEDURE_VERSION and the procedure template's version/changelog. Update the README/ARCHITECTURE MCP tool-surface lists to include cz_audit. A test asserts the shipped close skill references cz_audit.
**Depends on**: Implement rituals/audit.py + register cz_audit.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] The shipped clauderizer-close-gameplan skill (src/clauderizer/skills/) has a cz_audit self-audit step; a test asserts the shipped skill text references cz_audit
- [x] GAMEPLAN-PROCEDURE.md Ending Protocol + Close procedure include the self-audit step; PROCEDURE_VERSION and the template's version/changelog are bumped in lockstep
- [x] README + ARCHITECTURE MCP tool-surface lists include cz_audit (L-21 sweep)
- [x] Suite green in a fresh venv

### Phase 3: Dogfood, ship 1.8.0, close

**Goal**: Dogfood: run cz_audit on this gameplan and address its findings. CHANGELOG 1.8.0 entry; bump pyproject + __version__ to 1.8.0 (in lockstep — the guard test enforces it); bump subsys.rituals + subsys.scaffold as touched; cz_cascade + resolve. Verify the FULL suite in a clean/fresh venv (not the working .venv — the lesson this gameplan encodes). Close the gameplan (post-mortem, focus handback).
**Depends on**: Wire cz_audit into the shipped close skill + procedure.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_audit was run on this gameplan and its findings addressed (dogfood evidence recorded)
- [x] CHANGELOG 1.8.0 entry added; pyproject AND __version__ bumped to 1.8.0 in lockstep (guard test green)
- [x] subsys.rituals (+ subsys.scaffold if touched) bumped; cz_cascade run and resolved
- [x] FULL suite verified green in a FRESH venv; count recorded
- [x] Gameplan closed: post-mortem written, focus handed back
