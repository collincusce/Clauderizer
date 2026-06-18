# STORM-inspired curation methods Gameplan

> Created: 2026-06-18
> Status: Complete
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

### D1 — Out of scope: the Co-STORM hierarchical lesson mind-map

**Context**: The originating analysis ranked five STORM-inspired opportunities. The hierarchical lesson "mind map" (Co-STORM #3) — reorganizing lessons into a graph-backed concept hierarchy so consolidation is concept-scoped and the digest can surface gap-clusters — was rated high value. But lessons today are a flat, numbered, state-tagged list (markdown/lesson_state.py) carried whole into every handoff; the mind-map changes that data model.
**Decision**: This gameplan implements perspective-guided planning (#1), the analyze gap-finder (#2 / D-018), provenance/citations (#4), and multi-LM guidance (#5). It explicitly EXCLUDES the hierarchical lesson mind-map (#3), which touches the lesson data model and the consolidation/digest paths on a shipping beta and deserves its own gameplan with a migration story.
**Consequences**: Scope stays small and low-blast-radius (skills + one analyze extension + additive write-path fields). The mind-map is tracked as an open item for a future gameplan. If the user wants it folded in, it enters via cz_add_amendment, not silently.

## Open Items

**O-01.** Deferred (Co-STORM #3): hierarchical lesson "mind map" — reorganize lessons into a graph-backed concept hierarchy so cz_consolidate_lessons is concept-scoped and the SessionStart digest can surface concept clusters and gap-clusters instead of a flat list. Excluded from this gameplan per gameplan-decision (changes the lesson data model in markdown/lesson_state.py); candidate for its own gameplan with a migration story.

## Phase Breakdown

### Phase 0: Perspective-guided planning and multi-LM guidance

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderizer-new-gameplan SKILL.md adds a perspective-discovery step with a named lens set (e.g. security, performance, ops/release, testing, cost, failure-modes, prerequisite-chains) that interrogates the goal before phases are laid out
- [x] The skill adds a synthesis step that folds the interrogation findings into phases, decisions, and open items, and cross-references the cz_analyze gap-finder
- [x] The skill includes a multi-LM cost-split note: cheap models for the perspective fan-out, the strong model for synthesis
- [x] The .claude/skills/clauderizer-new-gameplan/SKILL.md mirror is byte-identical to the src/clauderizer/skills canonical copy
- [x] pytest is green with 0 failures (baseline 289 passed / 4 skipped preserved — Phase 0 changes no engine code)

### Phase 1: Gap-finder: graph-adjacency surfacing in cz_analyze

**Goal**: Extend the analyze gate (D-018) to surface one-hop graph neighbors of the most-relevant entities as an advisory "adjacent" set — Co-STORM's moderator move, in pure stdlib — wired through the cz_analyze tool and clauderize ops, framed as gap-finding.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] analyze() returns an `adjacent` list: one-hop graph neighbors (dependents + dependencies) of the top-ranked decisions/invariants and of any entity-id named in the query text
- [x] `adjacent` excludes ids already returned in the decisions/invariants results and ids already mentioned in the query (only surfaces what the agent has NOT connected)
- [x] Adjacency is computed from the graph index (graph/index.py / query.py), uses no embeddings, adds no runtime dependency, and is empty when no graph edges relate (honest negative)
- [x] The cz_analyze tool result and `clauderize ops` both include `adjacent`, and the analyze prompt invites gap-judgment alongside contradiction-judgment
- [x] New unit tests cover an adjacency hit, exclusion of already-surfaced ids, and the empty-graph case; full suite green (0 failed)

### Phase 2: Provenance on lessons and decisions

**Goal**: Add an optional, backward-compatible provenance/evidence field to the cz_add_lesson and cz_add_decision write paths (through markdown/writer.py per INVARIANT-02) so a lesson or decision can cite the concrete evidence that produced it (commit, file:line, phase, output id), and ensure it carries into the assembled handoff.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_add_lesson accepts an optional provenance/evidence argument; when supplied it renders in the lesson entry, and when omitted the rendered output is byte-for-byte identical to today's (backward-compatible)
- [x] cz_add_decision accepts the same optional provenance, rendered in the ADR entry, written via markdown/writer.py (INVARIANT-02)
- [x] A recorded provenance survives into the assembled handoff (cz_write_handoff)
- [x] New unit tests cover with- and without-provenance for both write paths; existing mutation and handoff tests still pass; full suite green (0 failed)

### Phase 3: Docs, CHANGELOG, and final cascade

**Goal**: Document the three new surfaces (analyze gap-finder, provenance fields, perspective-guided planning) in the affected subsystem/feature docs and CHANGELOG following the repo's existing release convention, run cascade for the touched entities and resolve it, and verify the full suite green before the gameplan closes.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] CHANGELOG.md records the gap-finder, provenance, and perspective-planning additions following the repo's existing release convention
- [x] The subsystem/feature docs covering the analyze gate and the mutation write paths reflect the new `adjacent` and provenance surfaces
- [x] Cascade has been run and resolved for every touched entity — cz_status shows zero pending cascades
- [x] Full suite green (0 failed) and cz_status shows all four phases complete
