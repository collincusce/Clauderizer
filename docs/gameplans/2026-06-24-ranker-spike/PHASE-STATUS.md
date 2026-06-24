# ranker-spike — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-24

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Measure stdlib BM25 vs baseline | ✅ COMPLETE | 2026-06-24 | 2026-06-24 | handoffs/PHASE-0-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_ranker_metrics: Shipped raw token-overlap ranker (analyze.rank_relevant) on tests/benchmarks fixtures. Combined extraction+multi_session @k=3: recall@k=1.0000, nDCG@k=1.0000, MRR=1.0000 — and identical 1.0000 at k=1 and k=5 (SATURATED at the ceiling on the deliberately disjoint-topic corpus). Guards: multi_session precision@k=0.7500; knowledge_updates contradiction_rate=0.0000; abstention_rate=1.0000.
bm25_candidate_metrics: Length-normalized stdlib BM25/Okapi (k1=1.5, b=0.75, Lucene non-neg IDF; stdlib-only, ZERO new dep) on IDENTICAL fixtures, score-formula swap only (same tokenizer, id-boost, stale-demotion secondary sort). Combined extraction+multi_session @k=3: recall@k=1.0000, nDCG@k=1.0000, MRR=1.0000 — Δ=+0.0000 vs baseline at every k. Guards held: multi_session precision@k=0.7500 (Δ=0), contradiction_rate=0.0000 (Δ=0), abstention_rate=1.0000. Diagnostic b-sweep b∈{0.0,0.25,0.5,0.75,1.0}: combined recall/nDCG/MRR flat at 1.0000 — the length-norm parameter does not move the ordering on this corpus shape.
verdict: DISCARD (script exit code 2). D1 pre-registered rule applied at gate k=3: best LIFT Δ=+0.0000 < meaningful threshold 0.02 (no lift possible — baseline already saturated at the 1.0 ceiling), and both GUARDS held (ms precision 0.75→0.75, contradiction 0.0→0.0, abstention 1.0→1.0). BM25 reproduces the baseline's perfect topic separation without regressing it, but cannot beat a saturated ceiling. Per D1/L-32 a discard is a SUCCESS: src/ unchanged, RRF/MMR/recency/graph-expansion remain parked. Provenance: docs/gameplans/2026-06-24-ranker-spike/_experiments/bm25_spike.py + RESULTS.txt (not run in CI).
suite_baseline_reconciled: Full suite green and unchanged: 624 collected = 620 passed + 4 skipped (platform/env-gated skips on Linux). Reconciles the "baseline 624" expectation — 624 collected vs 620 passing; no tests lost. tests/benchmarks 11/11 green; the load-bearing self-test test_harness_detects_ranker_regression passes. src/ and tests/ untouched (candidate lives only under the gameplan's _experiments/, which pytest does not collect — testpaths=["tests"]).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
