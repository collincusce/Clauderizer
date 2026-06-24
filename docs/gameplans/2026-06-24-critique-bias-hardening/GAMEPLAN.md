# critique-bias-hardening Gameplan

> Created: 2026-06-24
> Status: Planning
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

### D1 — cz_critique adopts CALM anti-bias checklist items (self-enhancement, authority); deterministic-surfacing only

**Context**: cz_critique (D-019) is a reference-free judge over Coverage/Coherence/Grounding that, in practice, grades the agent's OWN phase/gameplan/handoff output — the textbook trigger for self-enhancement bias (CALM, Ye et al. arXiv:2410.02736: even GPT-4-Turbo judge robustness collapses under injected bias). Authority bias (deference to unverifiable citations) maps onto the D-017 evidence field. Surfaced by the 2026-06-24 deep-research of awesome-generative-ai-guide.
**Decision**: Extend the cz_critique rubric with CALM-derived ADVISORY checklist items, prioritized to (1) self-enhancement — always applicable, since the critique target is self-authored — and (2) authority — flag deference to citations that don't resolve against the evidence field. Enters as deterministic engine-surfacing + rubric prose, never a runtime dependency (follows D-017's STORM precedent). Advisory only: the agent grades (INVARIANT-05), no enable/disable flag (D-015). Out of scope: position bias (applies to multi-candidate judging, not single-target critique) and a full 12-bias port — add only what demonstrably fires on real critiques.
**Consequences**: Strengthens an existing advisory gate at low cost and no new dependency. Risk: checklist verbosity — mitigate by surfacing only the biases applicable to the target. Verification needs a small labeled critique-eval fixture (the LongMemEval ranking harness does not cover critique quality) — tracked as an open item. Gain-gate: the additions must surface a degenerate/self-enhanced critique the prior rubric scored clean, or they are parked (a discard is a success — L-32).
**Evidence**: deep-research 2026-06-24 (CALM: Ye et al. arXiv:2410.02736, 12-bias taxonomy; self-enhancement + authority definitions verified 3-0); paired with the genai-guide-ranking-research memory note.
**Status**: active (2026-06-24)

## Open Items

**O-01.** _(phase 0)_ Define the labeled critique-eval fixture: a small set of degenerate/self-enhanced critiques vs sound ones (the LongMemEval ranking harness does NOT cover critique quality), so the anti-bias additions can be gain-gated on whether they surface what the prior rubric missed.

## Phase Breakdown

### Phase 0: CALM self-enhancement + authority checks

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Self-enhancement + authority checklist items added to the cz_critique reference-free rubric (rituals/critique.py), surfaced advisorily in the tool result
- [ ] Deterministic surfacing only — no new runtime dependency added; no enable/disable config flag (INVARIANT-05 / D-015 honored)
- [ ] A small labeled critique-eval fixture demonstrates the new items surface a degenerate/self-enhanced critique that the prior rubric scored clean
- [ ] Full suite green (baseline 624 tests; no regression) and benchmarks unaffected
