# ranker-spike Gameplan

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

### D1 — ranker-spike is a pre-registered kill-gate: stdlib BM25 must beat the raw-overlap baseline on the harness or the direction is parked

**Context**: analyze.rank_relevant scores by raw token-overlap COUNT — no IDF, no length normalization — so a verbose entry can outrank a tighter one on token volume alone. The 2026-06-24 deep-research of awesome-generative-ai-guide surfaces length-normalized stdlib BM25/Okapi as the deterministic fix (and the semantic-recall POST-MORTEM already named lexical/BM25 the carried-forward path). BUT every published IR gain is from large corpora; Clauderizer's corpus is tiny and structured (dozens-to-hundreds of dense entities), where IDF may be near-uniform — so transfer is UNPROVEN. rank_relevant is shared by the analyze gate, the handoff lesson-pointer, and the edge-suggester.
**Decision**: Run ONE measured experiment: length-normalized stdlib BM25/Okapi relevance scoring vs the current count baseline on tests/benchmarks (extraction + multi_session recall@k / nDCG / MRR), stdlib-only — NO NumPy / bm25s (reaffirms D-014 / L-14). Pre-register the keep/discard rule: KEEP only on a meaningful lift WITH no regression on multi_session precision or the knowledge_updates contradiction rate; otherwise DISCARD (a discard is a success — L-17/L-32). Do NOT pre-build RRF / MMR / recency / graph-expansion — they are parked until this proves the ranker is even movable on this corpus shape.
**Consequences**: A cheap, fast verdict that gates the whole retrieval direction before any investment. On KEEP, shipping to rank_relevant ripples to its shared consumers (analyze gate, handoff lesson-pointer, edge-suggester) — handle via a cascade + an AMENDED ship phase recorded at that point, not pre-planned (don't build phases for an outcome that may not occur). On DISCARD, park the direction with the measured null and the captured baseline as provenance.
**Evidence**: deep-research 2026-06-24 (RRF: Cormack SIGIR'09; BM25: bm25s arXiv:2407.03618; Generative-Agents additive score: Park UIST'23) + the 2026-06-17-semantic-recall POST-MORTEM "lexical/BM25 carried-forward" note; paired with the genai-guide-ranking-research memory note.
**Status**: active (2026-06-24)

## Open Items

**O-01.** _(phase 0)_ On a KEEP verdict only: rank_relevant's shared consumers (the analyze gate, the handoff lesson-pointer, the edge-suggester) need a cz_cascade + review before shipping the new scoring. Record an AMENDED ship phase at that point — do NOT pre-plan it (no phases for an outcome that may not occur).

## Phase Breakdown

### Phase 0: Measure stdlib BM25 vs baseline

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Current baseline ranker metrics (recall@k / nDCG / MRR on extraction + multi_session) captured in the Outputs Registry
- [ ] Length-normalized stdlib BM25/Okapi scoring implemented as a measurable alternative path (stdlib-only — verified no new import / runtime dependency added)
- [ ] Harness comparison run; the pre-registered keep/discard metric evaluated against the captured baseline
- [ ] KEEP/DISCARD verdict recorded with the measured number (a discard is a success — L-32); RRF / MMR / recency / graph-expansion remain parked unless KEEP
- [ ] Full suite (baseline 624) + benchmarks green; the harness ranker-regression self-test (test_harness_detects_ranker_regression) still passes
