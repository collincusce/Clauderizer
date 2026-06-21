# Memory-eval harness

The benefit-gate for gameplan `2026-06-20-empirical-memory-gains`. Every feature
in that gameplan must beat the captured baseline on a **pre-registered metric**,
or it is parked (D: empirical gain-gate). This directory is that measuring
instrument — deterministic, stdlib-only, no ML (consistent with the engine's
core constraints).

## The methodology (LongMemEval-derived)

**Five abilities** every memory system is scored on (one fixture family each):

| Ability | What it tests | Metric |
|---|---|---|
| extraction | a recorded fact is retrieved by a relevant query | recall@k, nDCG, MRR |
| multi_session | facts on different topics don't bleed together | recall@k, precision@k |
| temporal | dated facts / "as of" reasoning (bitemporal phase) | as-of correctness |
| knowledge_updates | a superseded fact must not outrank its replacement | contradiction rate |
| abstention | an absent topic must surface nothing | abstention rate |

**Three-stage ablation** — attribute a gain to a component, not a black box:

| Stage | Engine surface | Varied by |
|---|---|---|
| index | `graph.index` build over docs | corpus size / structure |
| retrieval | `analyze.rank_relevant` (lexical) | the ranker (real vs degraded) |
| reading | what gets injected (digest / handoff) | focused-vs-full context |

## The gate

- **Deterministic (CI, fully repeatable):** `pytest tests/benchmarks`. Metric
  correctness, the ranker baseline, and the load-bearing self-test
  (`test_harness_detects_ranker_regression`) that proves a relevance-blind ranker
  scores **strictly worse** — i.e. the harness can detect a regression.
- **Agent-eval (behavioral, run during a feature phase):** `agent_eval.py` builds
  a focused-vs-full ablation; the orchestrator spawns paired sub-agents (one per
  context arm, same query) and scores answers with `score_answer`. The predicted
  result (Context Rot / LongMemEval) is **focused ≥ full**; any feature that
  injects *more* context must show it does not regress this.

## Files

- `metrics.py` — pure metrics: `recall_at_k`, `precision_at_k`, `ndcg_at_k`,
  `reciprocal_rank`, `contradiction`, `abstention_correct`, `token_estimate`
  (the engine's `len // 4` convention).
- `corpora.py` — the five-ability fixtures: an in-memory ranker corpus and
  `seed_*` helpers that build a real temp repo.
- `harness.py` — runners (`run_ranker`, `run_engine_probes`,
  `measure_context_tokens`) and the two rankers (real + degraded).
- `agent_eval.py` — focused-vs-full prompt builders + deterministic scorer.
- `test_benchmarks.py` — the standing CI gate.

## Baselines

The real-repo baseline numbers (test count, digest/handoff token sizes, ranker
recall@k, supersession contradiction rate) are captured in the gameplan's
`PHASE-STATUS.md` Outputs Registry, and one-off measurement runs live under the
gameplan's `_experiments/` for provenance (not run in CI).

## How to run

```bash
pytest tests/benchmarks            # the deterministic gate
```
