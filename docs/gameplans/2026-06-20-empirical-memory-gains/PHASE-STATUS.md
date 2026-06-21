# Empirical memory gains — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-20

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Eval harness and baseline capture | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Context-rot trims (evidence-gated removal) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-1-HANDOFF.md |
| 2 | DAG integrity validation | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Edge-suggester (missing-edge surfacing) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Decision supersession back-refs and lifecycle | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Bitemporal valid-time (must-earn) | ✅ COMPLETE | 2026-06-20 | 2026-06-20 | handoffs/PHASE-5-HANDOFF.md |
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

### Phase 2 Outputs

```
phase2_result: src/clauderizer/graph/validate.py: deterministic dangling-edge + cycle (iterative Tarjan SCC) detection over the project DAG, surfaced advisorily via the existing status drift channel (never blocks; INVARIANT-05/06). Gap filled: pin_violations skipped unknown targets, so dangling edges were undetected. 12 tests: 100% detection on seeded dangling+cycle fixtures, 0 false positives on valid DAGs. Suite 415->427 green.
```

### Phase 3 Outputs

```
phase3_result: KEPT. analyze.suggest_edges surfaces MISSING depends_on edges from distinctive-token overlap (>=2, boilerplate stripped) - the structural complement of D-018 (which walks EXISTING edges). Gate: precision=0.75, recall=1.0 on a labeled fixture that INCLUDES a generic-collision false positive (bar >=0.70). Advisory: extends cz_analyze result with suggested_edges (no new tool; test_ops parity green); never auto-writes an edge. Rejected-pair memory = not_related_to frontmatter (symmetric, round-trips via cz_upsert_entity). +11 tests; suite 438. Honest caveat: 0.75 is fixture-measured; real-world precision varies; advisory + agent-confirm + reject-memory absorbs false positives.
```

### Phase 4 Outputs

```
phase4_result: Decision supersession lifecycle SHIPPED. add_decision(supersedes=X) now writes a 'Superseded by' back-ref + flips X's Status to superseded (idempotent; append-only - X is annotated, never deleted, INVARIANT-03) and stamps the new decision Status: active + date. analyze demotes superseded/deprecated below active peers via a secondary sort key (score untouched). GATE: harness supersession contradiction_rate 1.0 -> 0.0, measured via the UNCHANGED corpora/harness (only the Phase-0 baseline-witness test flipped to assert the now-closed gap; verified corpora.py/harness.py/metrics.py untouched). +6 tests; suite 444 green.
```

### Phase 5 Outputs

```
phase5_result: PARKED (no code shipped). Bitemporal valid-time cannot beat Phase 4: the contradiction-rate gate is already at its 0.0 floor, valid!=transaction time is irrelevant for project decisions (effective when made), and as-of queries have no demonstrated need while costing always-injected schema fields (anti D-027). Evidence-based must-earn park per D2.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
