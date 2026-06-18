# STORM self-critique gate Gameplan

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

### D1 — Scope: rubric gate + two skill refinements; defer the staleness counter and mind-map cleanup

**Context**: The deep-research second-check ranked five post-upgrade candidates. Two carry real risk: the consecutive-same-intent staleness counter (the research's own open question warns it may conflate STORM's conversational turn cadence with Clauderizer's phase cadence and produce noise) and the mind-map deterministic cleanup (collapse-singleton may be unsafe on a RETENTION graph — it could collapse meaningful decision/invariant chains, unlike a discovered concept tree).
**Decision**: This gameplan implements the reference-free self-critique gate (D-019), an outline-before-synthesize skill refinement for handoff/post-mortem synthesis, and a perspective-from-related-entities refinement to the new-gameplan skill. It DEFERS the staleness counter and the mind-map cleanup, each tracked as an open item pending validation of its risk.
**Consequences**: Tight, low-risk, completable scope (one new advisory tool composed from existing signals + two markdown skill edits). The two deferred items are tracked as open items, not dropped. All work ships under the unreleased 0.12.0 version (folded into its CHANGELOG entry), released at the end of this effort.

## Open Items

**O-01.** Deferred candidate (STORM): consecutive-same-intent staleness counter as an advisory nudge (e.g. N phases/edits with no new decision or invariant -> nudge to run cz_analyze). Trivial stdlib, but the deep-research open question flags noise risk (conflating conversational turn cadence with phase cadence). Validate the signal is useful before building.

**O-02.** Deferred candidate (Co-STORM): the mind-map's embedding-free deterministic cleanup (trim_empty_leaf_nodes, merge_single_child_nodes) applied to the derived dependency graph. OPEN RISK from the deep-research: collapse-singleton may be unsafe on a retention graph — it could collapse meaningful decision/invariant chains. Validate semantic safety before adopting; pairs with the deferred mind-map (O-01 of the prior gameplan).

## Phase Breakdown

### Phase 0: Synthesis-quality skill refinements

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Outline-before-synthesize guidance is added to the close-gameplan and do-phase skills (draft a section/coverage outline before writing a handoff or post-mortem)
- [x] A perspective-from-related-entities clause is added to the new-gameplan skill (derive interrogation lenses from related graph entities, not only the fixed lens list)
- [x] Every edited skill's .claude mirror is byte-identical to its src/clauderizer/skills source (L-16)
- [x] pytest green, 0 failed (baseline 300 preserved — Phase 0 changes no engine code)

### Phase 1: Self-critique rubric gate (cz_critique)

**Goal**: Add cz_critique (D-019): a read-only, advisory tool that assembles a reference-free dimensional rubric — Coverage / Coherence / Grounding — for a target (phase, gameplan, or handoff) by composing existing deterministic signals plus the analyze gate, and surfaces it with a grading prompt for the agent. Stdlib only, never scores or blocks (INVARIANT-05), reachable via MCP and clauderize ops.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_critique(target) assembles a reference-free dimensional rubric — Coverage (unresolved open items, unchecked exit criteria, phases missing outputs/summary), Coherence (drift, pending cascades, analyze-surfaced contradictions), Grounding (lessons/decisions lacking evidence) — for a phase, the gameplan, or a handoff
- [x] cz_critique is read-only and advisory: returns the rubric + a grading prompt, never scores or blocks (INVARIANT-05), named by effect (L-03)
- [x] Stdlib only: composes existing status_bundle signals + the analyze gate; no embeddings, no new runtime dependency
- [x] cz_critique is reachable via the MCP tool surface AND clauderize ops (registry parity test updated)
- [x] New unit tests cover each dimension firing on a gap and staying empty on a clean target; full suite green with new tests, 0 failed

### Phase 2: Docs, CHANGELOG, cascade, and close

**Goal**: Document cz_critique and the skill refinements: extend the unreleased 0.12.0 CHANGELOG entry, add cz_critique to ARCHITECTURE's discipline-gate section, bump the touched subsystem version(s) and run + resolve cascade, and verify the full suite green with all phases complete — leaving the tree ready for the release ritual.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] The CHANGELOG [0.12.0] entry is extended with cz_critique and the skill refinements
- [x] ARCHITECTURE.md documents cz_critique in the discipline-gates section
- [x] Touched subsystem version(s) bumped; cascade run and resolved; cz_status shows zero pending cascades
- [x] Full suite green (0 failed) and cz_status shows all three phases complete
