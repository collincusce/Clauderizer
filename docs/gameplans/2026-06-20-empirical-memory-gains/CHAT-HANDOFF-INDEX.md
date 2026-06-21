# Chat Handoff Index — Empirical memory gains

> Last updated: 2026-06-20
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 410

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
| 0 | Eval harness and baseline capture | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Context-rot trims (evidence-gated removal) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | DAG integrity validation | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Edge-suggester (missing-edge surfacing) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Decision supersession back-refs and lifecycle | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bitemporal valid-time (must-earn) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Persistent steering doc (must-earn) | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Close-out: consolidate, measure, post-mortem | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-20

Built tests/benchmarks/ - a deterministic, stdlib-only memory-eval harness (LongMemEval 5-ability taxonomy + 3-stage ablation): metrics (recall@k, precision, nDCG, MRR, contradiction, abstention, token-estimate len//4, dangling/cycle DAG primitives), an in-memory ranker corpus + repo-seeding fixtures, and a focused-vs-full agent-eval scaffolder. 11 new tests; suite 400->410 green. The load-bearing self-test proves the harness detects a degraded ranker (MRR 0.46 vs 1.0). Captured the real baseline: digest 263 tok, handoff 3137 tok of which 2737 (87%) are the 21 project lessons (Phase 1 trim target); ranker recall@3/MRR/nDCG=1.0; supersession contradiction=1.0 (Phase 4 target 0). Fixed the stale 0-tests baseline -> 410. Methodology: tests/benchmarks/README.md; baseline: _experiments/measure_baseline.py.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Testing

**1.** A retrieval-quality gate must score on a POSITION-SENSITIVE metric (MRR/nDCG), not recall@k with k >= corpus size: recall@k is trivially 1.0 when k spans the whole corpus, so a relevance-blind ranker passes it. The harness self-test caught exactly this - a degraded ranker scored recall@5=1.0 (identical to the real ranker) yet MRR 0.46 vs 1.0. Prove a measurement instrument can detect the failure it guards before trusting its verdicts. *(evidence: tests/benchmarks/test_benchmarks.py::test_harness_detects_ranker_regression; 2026-06-20-empirical-memory-gains Phase 0)*
