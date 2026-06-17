# spec-kit-discipline-gates Gameplan

> Created: 2026-06-17
> Status: Executing
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

### D1 — Gates reuse existing markdown conventions, not new schemas

**Context**: Each gate needs a home in the markdown. The GAMEPLAN template already has a prose "Open Items" section and `- [ ]` exit-criteria checkboxes. Introducing new frontmatter, tables, or entity kinds would churn templates, complicate the parser, and split human-readability.
**Decision**: Open items extend the existing "Open Items" section as auto-numbered O-NN entries (modeled on cz_add_decision's D-NNN allocation via next_numbered_id). Exit criteria reuse the existing `- [ ]` checkboxes, made machine-trackable in place — a blessed write toggles them; transition surfaces unchecked ones. No new frontmatter schema, no new DAG entity kind.
**Consequences**: Minimal template churn; existing gameplans stay valid. Writers reuse markdown/writer.py primitives (append_to_section; checkbox toggling may need one small new writer helper). Preserves the "markdown is human-readable source of truth" invariant. Keeps the parser surface small.

### D2 — Analyze-gate relevance = lexical overlap (keyword + entity-id), not embeddings

**Context**: O-01 asked how cz_analyze should rank candidate invariants/decisions: keyword/entity-id/scope overlap vs. heavier semantic similarity. L-14 and D-014 (the LEANN no-go) say stay dependency-light.
**Decision**: Relevance is lexical: token overlap (4+ char content words, ADR boilerplate stopped) plus a boost when the query names an entity id (D-NNN / INVARIANT-NN); ranked descending, capped at top-k. No embeddings, no new dependency. Implemented in src/clauderizer/analyze.py.
**Consequences**: cz_analyze and the cz_add_decision enrichment carry zero new dependencies and stay fast. Good enough for the curated, distinctive vocabulary of DECISIONS/INVARIANTS (proven by the seeded-fixture test). The ranker is a single pure function to swap if recall ever proves insufficient, but per L-14 the bar for a semantic dependency is high.

## Open Items

**O-01.** _(phase 2)_ Phase 2 analyze gate: pick the candidate-relevance method for surfacing invariants/decisions (keyword / entity-id / scope overlap vs. heavier semantic similarity). Must stay dependency-light (L-14) — keyword+ID+scope overlap is the likely default; record the call as a Phase 2 decision. _(resolved 2026-06-17: Decided as gameplan D2: lexical overlap (keyword + entity-id), no embeddings (L-14).)_

## Phase Breakdown

### Phase 0: Clarify gate: structured open items (O-NN) + judgment-based surfacing

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable assertion)_

### Phase 1: Exit-criteria gate: machine-checkable phase criteria + surfacing at completion

**Goal**: Make phase exit criteria machine-trackable by reusing the existing `- [ ]` checkboxes (D1): a blessed write toggles a criterion; cz_status and cz_transition_phase surface unchecked criteria when completing a phase (advisory, never blocking, per D-015 / INVARIANT-05); criteria that map to a measured signal (e.g. the preflight test count) auto-link to it. Reuses Phase 0's surfacing convention. Exit: a blessed write checks/unchecks a criterion idempotently with MCP+CLI registry parity (test_blessed_surfaces); transitioning a phase to complete surfaces any unchecked criteria in the result WITHOUT blocking; at least one criterion auto-links to the preflight test-count signal; tests cover toggle idempotency and the surfacing path; suite green.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 2: Analyze gate: surface conflicting invariants/decisions for agent judgment

**Goal**: Add the consistency gate (D-016, judgment-based like cascade): a read-op cz_analyze that, given a proposed/active decision or phase, assembles the most relevant existing invariants and decisions (by entity/keyword/scope) and returns them for the agent to rule on contradiction; plus result-enrichment on cz_add_decision that surfaces related/possibly-superseded entries at write time. The engine surfaces candidates only — never decides (D-015 / INVARIANT-05). Reuses Phase 0's surfacing convention. Exit: cz_analyze returns a ranked, relevant candidate set (NOT the whole file) plus a verdict prompt, on the MCP+CLI registry with parity; cz_add_decision surfaces related entries (incl. supersedes hints) in its result; relevance is tested against seeded fixtures (right entries surfaced, irrelevant ones not); suite green.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_analyze returns a ranked, relevant candidate set of invariants/decisions (not the whole file) plus a verdict prompt, on the MCP+CLI registry with parity
- [x] cz_add_decision surfaces related and possibly-superseded entries in its result (judgment-based, D-016)
- [x] relevance is tested against seeded fixtures (right entries surfaced, irrelevant ones not)
- [x] full suite green

### Phase 3: Integration & docs: wire gates into rituals/skills/digest, document to code

**Goal**: Land the three gates as something the do-phase/new-gameplan flows actually use and a maintainer can reason about. Surface pending open items + unchecked exit criteria in the cz_status / SessionStart digest; have the do-phase and new-gameplan skills invoke the clarify and analyze gates at the right moments; update ARCHITECTURE.md, the rituals/mutations subsystem docs, and DECISIONS/INVARIANTS to cite the implementation (claims-cite-code discipline); CHANGELOG/version as appropriate. Exit: digest shows pending open items + unchecked criteria; the skills reference the gates; docs are code-accurate; full suite green; close-out ready (handoff written, any cascade resolved).
**Depends on**: 0, 1, 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
