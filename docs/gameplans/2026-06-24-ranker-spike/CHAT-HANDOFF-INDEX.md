# Chat Handoff Index — ranker-spike

> Last updated: 2026-06-24
> Status: All 1 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 620

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Measure stdlib BM25 vs baseline | ✅ COMPLETE | 2026-06-24 | 2026-06-24 | handoffs/PHASE-0-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-24

Phase 0 ran the pre-registered BM25-vs-baseline kill-gate (D1) as a self-contained, isolated experiment on branch experiment/ranker-spike. Implemented a length-normalized stdlib Okapi BM25 scorer (k1=1.5, b=0.75, Lucene non-negative IDF; ZERO new runtime dependency) under _experiments/bm25_spike.py — a faithful score-formula swap over the shipped analyze.rank_relevant (same tokenizer, same id-boost, same stale-demotion secondary sort), scored against the IDENTICAL tests/benchmarks fixtures + harness via harness.run_ranker and (for the contradiction guard) an in-process monkeypatch of the real analyze.analyze path over a seeded temp repo. src/ was never touched.

Measured result: the raw-overlap baseline is ALREADY SATURATED at the 1.0 ceiling on extraction+multi_session recall@k/nDCG/MRR (at k=1, 3, 5), so BM25 ties it exactly (Δ=+0.0000 everywhere) with both guards flat — multi_session precision@k=0.75, knowledge_updates contradiction_rate=0.0, abstention_rate=1.0; a diagnostic b-sweep across length-normalization strengths stays pinned at 1.0. Per D1's pre-registered rule, best lift +0.0000 << the 0.02 meaningful threshold ⇒ DISCARD (a successful null — L-32). RRF/MMR/recency/graph-expansion remain parked; the direction is parked with the measured null + captured baseline as provenance. Full suite green (620 passed / 624 collected; benchmarks 11/11; the load-bearing test_harness_detects_ranker_regression passes). O-01 (KEEP-only cascade + amended ship phase) did not trigger.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Eval methodology

**1.** A deterministic relevance kill-gate can only conclude what its fixtures permit. When the eval corpus is built to be cleanly separable (disjoint, non-overlapping topics — as tests/benchmarks RANKER_ENTRIES is), the raw-overlap baseline already saturates at the 1.0 recall/nDCG/MRR ceiling, so NO scoring change can show lift: the gate can only return DISCARD/break-even by construction, and a green result proves "no regression," never "no value." To actually FALSIFY "richer scorer X helps," the fixtures must first contain the failure mode X targets — for BM25/Okapi: length-bias confounds, term-frequency skew, near-duplicate topics. This extends L-32 (saturated target ⇒ predict the null) with a fixture-design corollary: a saturated fixture can't even falsify the hypothesis, so build the adversarial fixture BEFORE the scorer. Corollary risk for any future ranker swap: BM25 length-normalization only breaks the stale-vs-current SECONDARY-sort tie that supersession-demotion relies on (analyze.rank_relevant), so a length-asymmetric stale/current pair could invert ordering — it did NOT fire here only because the knowledge_updates fixture isn't length-adversarial (a fixture gap, not a safety proof). *(evidence: docs/gameplans/2026-06-24-ranker-spike/_experiments/bm25_spike.py + RESULTS.txt; stdlib BM25 (k1=1.5,b=0.75) tied baseline at 1.0000 on every extraction+multi_session metric and across b-sweep b∈{0,0.25,0.5,0.75,1.0}; guards flat (ms precision 0.75, contradiction 0.0); verdict DISCARD (exit 2). Suite 620 passed/624 collected green.)* (promoted 2026-06-24: L-39)
