# Empirical memory gains — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-20

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Eval harness and baseline capture | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Context-rot trims (evidence-gated removal) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-1-HANDOFF.md |
| 2 | DAG integrity validation | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Edge-suggester (missing-edge surfacing) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Decision supersession back-refs and lifecycle | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bitemporal valid-time (must-earn) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Persistent steering doc (must-earn) | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Close-out: consolidate, measure, post-mortem | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests: 400 passing / 404 collected / 4 skipped (pytest, 2026-06-20). Corrects the stale "0 tests" baseline; refreshed in tracker via cz_preflight.
context_token_baseline: digest=263 tok; handoff(Phase 0)=3137 tok; lesson payload=2737 tok across 21 project lessons (= 87% of the handoff). Phase 1 trim target is the lesson payload; the digest is small (confirms D-020), not a target. Measured via _experiments/measure_baseline.py.
ranker_baseline: In-memory 6-probe corpus @k=3: recall=1.0, precision=0.8, nDCG=1.0, MRR=1.0, abstention=1.0. The degraded-ranker self-test confirms the harness detects a regression (blind ranker scores strictly worse on MRR/nDCG/recall).
supersession_contradiction_baseline: 1.0 (1/1 knowledge-update probe): the flat-status decision model surfaces a superseded decision at/above the current one. Phase 4 (supersession back-refs + status) target = 0.0.
harness: tests/benchmarks/ — 10 deterministic tests (metrics, ranker baseline, regression self-test, supersession+abstention, token measurement). Agent-eval (focused-vs-full) scaffolding in agent_eval.py. Methodology: tests/benchmarks/README.md. Baseline capture: _experiments/measure_baseline.py.
```

### Phase 1 Outputs

```
phase1_trim_result: handoff 3137->1420 tok (-55%); project-lesson payload 2737->994 tok (-64%); agent-eval focused 5/6 == full 5/6 (tie, accuracy held); ranker recall@5 = 6/6 = 100%. Change (D4): the handoff focuses project lessons to top-k ranked-to-phase + a pointer to canonical docs/LESSONS.md when count > k; <= k rides full. Suite 415 green.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
