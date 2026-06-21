# Empirical memory gains Gameplan

> Created: 2026-06-20
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

### D1 — No memory-poisoning defenses this initiative

**Context**: Considered building memory-poisoning mitigation, but the primary supporting source (MINJA attack) was refuted under adversarial verification in the research pass.
**Decision**: Do not build poisoning-specific defenses now; track as an open question pending corroborated evidence.
**Consequences**: Avoids speculative complexity; revisit only if a credible, verified threat model emerges.
**Evidence**: MINJA memory-injection claim refuted 1-2 in the research-2 verification pass.

### D2 — Bitemporal and steering-doc are must-earn candidates

**Context**: The bitemporal schema is peer-reviewed-sound but its benefit over a simple superseded_by back-ref is unproven (Graphiti efficacy claims were refuted); a steering doc is itself always-injected context, in tension with the trim-first decision.
**Decision**: Implement both behind their gates and keep ONLY if each beats a simpler baseline (Phase 4 back-refs for bitemporal; its own token cost for steering). Park or drop otherwise with a recorded finding.
**Consequences**: Phases 5 and 6 may legitimately end in a parked/dropped state; that is an accepted, honest outcome.
**Evidence**: ADBIS 2025 bitemporal property-graph schema (sound); Graphiti temporal efficacy refuted 1-2; context-rot evidence.

### D3 — Eval methodology: LongMemEval 3-stage ablation + 5-ability fixtures; deterministic CI gate plus paired-subagent agent-eval

**Context**: We need a repeatable, decomposable way to attribute a measured gain to a specific component.
**Decision**: Adopt the index/retrieval/reading three-stage ablation and the five-ability fixture taxonomy (extraction, multi-session, temporal, knowledge-updates, abstention). Deterministic metrics gate CI; the agent-eval spawns paired with/without sub-agents scored against fixture answer keys.
**Consequences**: Phase 0 implements this harness; all feature phases reuse it for their gate.
**Evidence**: LongMemEval ICLR 2025 (arxiv 2410.10813); repo xiaowu0162/longmemeval.

### D4 — Handoff focuses project lessons under memory pressure (top-k ranked + pointer-to-canonical)

**Context**: The cumulative handoff carried ALL project lessons in full — measured at 87% of a 3137-token handoff (2737 tok across 21 lessons), and the live status digest already warned 21 > 20. Research (lost-in-the-middle 2307.03172; focused>full, LongMemEval 2410.10813) plus a focused-vs-full agent-eval on the real lessons informed the change.
**Decision**: When active project lessons exceed the relevance-pointer k, the handoff carries the top-k lessons most relevant to the phase (ranked, most-relevant first so they are not buried) plus a pointer to the canonical full set in docs/LESSONS.md, instead of dumping all. At or below k, the full list rides unchanged (propagation-safe for small sets).
**Consequences**: Handoff cut 3137->1420 tok (55%); lesson payload 2737->994 (64%) at EQUAL agent-eval accuracy (focused 5/6 == full 5/6); ranker recall@5=100% so the relevant lesson is always present in the focused set. Reconciles D-022: this is relevance-ranking + pointer-to-canonical (nothing dropped from canonical memory), NOT the tail truncation D-022 rejected. Honest scope: the eval showed a TIE, not focused>full — the win is token-cost at held accuracy; active length-harm is expected only at larger scales.
**Evidence**: _experiments/measure_baseline.py (handoff 3137->1420); _experiments/eval_focus.py + phase1-focus-eval workflow (focused 5/6 == full 5/6; recall@5 6/6); src/clauderizer/rituals/handoff.py focused_project_lessons; tests/test_handoff_focus.py

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Eval harness and baseline capture

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] tests/benchmarks/ harness exists and runs green via pytest
- [x] Deterministic metrics implemented: ranker recall@k, nDCG/MRR, injected-token count, stale-fact contradiction rate, abstention correctness, DAG validity
- [x] LongMemEval-style fixtures present for all 5 abilities (extraction, multi-session, temporal, knowledge-updates, abstention)
- [x] Harness catches a seeded regression (e.g. shuffled ranker -> recall drop is flagged)
- [x] Real baseline captured in Outputs Registry (test count, digest tokens, handoff tokens, recall@k), replacing the stale 0-tests value
- [x] Agent-eval runner (paired with/without sub-agents, focused-vs-full) is documented and runnable

### Phase 1: Context-rot trims (evidence-gated removal)

**Goal**: Cut injected-context size (session digest, cumulative handoff, lesson roll-up) to a focused, front-loaded form, proving token cost drops with no agent-accuracy loss.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Handoff and digest injection is focused (ranked top-k, front-loaded), not a full dump
- [x] Benchmark shows injected-token reduction versus the captured baseline corpus
- [x] Focused-vs-full agent-eval: accuracy on memory-dependent questions does not drop (ideally rises)
- [x] Buried-fact position fixture passes (a critical entity is not placed mid-context)
- [x] Full suite still green (400-test baseline preserved)

### Phase 2: DAG integrity validation

**Goal**: Add deterministic depends_on DAG integrity checks (dangling-edge + cycle detection), surfaced advisorily, with 100% detection on seeded broken fixtures.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Dangling-edge detection: 100% on a seeded fixture of broken depends_on edges
- [x] Cycle detection: 100% on a seeded cyclic fixture, 0 false positives on valid DAGs
- [x] Findings surfaced advisorily via status/cascade (never blocks a write)
- [x] New tests cover the detector; full suite green

### Phase 3: Edge-suggester (missing-edge surfacing)

**Goal**: Surface MISSING depends_on edges from lexical/entity-id overlap (agent confirms; rejected pairs remembered), gated on precision so it never adds noise.
**Depends on**: 0, 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Edge-suggester surfaces missing edges from lexical/entity-id overlap via an agent-confirm flow
- [x] Suggestion precision meets the pre-registered threshold on a labeled fixture (else the feature is parked) - value recorded
- [x] Rejected-pair memory: a dismissed suggestion is not re-surfaced
- [x] Advisory-only (no auto-write of edges); full suite green

### Phase 4: Decision supersession back-refs and lifecycle

**Goal**: Give decisions a navigable lifecycle: bidirectional superseded_by/supersedes back-refs, a status field, and dates, cutting stale-fact contradictions vs the flat status note.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_add_decision writes a bidirectional superseded_by back-ref on the superseded decision
- [x] Decision status lifecycle (active/superseded/deprecated) and date fields are present and parsed
- [x] Knowledge-updates fixture: a 'current decision on X' query returns the non-stale entry
- [x] Measured stale-fact contradiction rate drops versus the flat-status baseline
- [x] Back-fill is append-only (no deletion); full suite green

### Phase 5: Bitemporal valid-time (must-earn)

**Goal**: Add a deterministic bitemporal valid-from/valid-until plus as-of query model; keep ONLY if it beats Phase 4 back-refs on contradiction-rate / as-of correctness, else park.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] valid_from/valid_until plus recorded-at fields parse deterministically; as-of query implemented
- [ ] As-of-query correctness fixture passes
- [ ] Measured contradiction-rate / as-of benefit EXCEEDS Phase 4 back-refs alone, else PARK with a recorded finding
- [ ] Keep-or-park decision recorded with the measured delta

### Phase 6: Persistent steering doc (must-earn)

**Goal**: Add an optional persistent steering/constitution doc; keep ONLY if a with/without ablation shows adherence gain exceeds its always-injected token cost, else drop.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Optional steering doc supported (markdown, project-scoped, opt-in)
- [ ] With/without ablation run: adherence gain vs always-injected token-cost penalty measured
- [ ] Net-positive versus context-rot cost, else DROP with a recorded finding
- [ ] Keep-or-drop decision recorded with the measured delta

### Phase 7: Close-out: consolidate, measure, post-mortem

**Goal**: Re-distill lessons under the gauge, record the measured per-feature gains table, write the post-mortem, and run the final gameplan-wide cascade.
**Depends on**: 1, 2, 3, 4, 5, 6.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Active and project lessons re-distilled under the memory-gauge thresholds
- [ ] Measured per-feature gains table written (which landed, which parked, with deltas)
- [ ] POST-MORTEM.md written with procedure improvements
- [ ] Gameplan-wide cascade clean; every phase completed or explicitly parked
