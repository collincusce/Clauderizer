# abstract-index-fast-retrieval — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Branch, baseline &amp; cost-harness (fixture-first) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Abstract index builder (data structure, dual parser, invalidation) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Addressable fetch (cz_get) and abstract surfacing on cz_analyze | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cost experiment and gain-gate verdict (KEEP/DISCARD) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Realize the win in injected surfaces (handoff/status) and re-measure | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Write-time lesson-synthesis advisory (own fixture, own mini gain-gate) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Upgrade path (init/reindex build, doctor detect) and dogfood on an isolated repo copy | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Release readiness: CI 9-cell, docs sweep, cross-platform, merge-ready | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests: 632 passed, 4 skipped (green via .venv/bin/python -m pytest). Was 626 before this phase added 6 cost-harness tests. 632 is the new green baseline for all later phases.
cost_harness: tests/benchmarks/cost.py — measure_baseline / measure_candidate / evaluate / verdict; token proxy reuses metrics.token_estimate (len//4), no live LLM. Strategies: abstract_then_fetch (real) + noop_full + starve (controls). Phase 3 wires the real abstract index + cz_get into evaluate().
gain_gate_thresholds: Pre-registered in docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/PRE-REGISTRATION.md and frozen as cost.py constants: MIN_SAVING=0.30, accuracy non-regression, MAX_ROUND_TRIPS=2. KEEP iff all three hold; else DISCARD (L-32).
discrimination_demo: real mechanism 51.3% saving -> KEEP; noop control 0.0% -> DISCARD; starve trap 69.5% saving but accuracy 0.00 -> DISCARD (accuracy guard vetoes). Gap 51.3pp. CI-locked in tests/benchmarks/test_cost.py (6 tests). Run via _experiments/run_cost_harness.py; provenance in _experiments/RESULTS.txt.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: D4 point (2) prescribes merging main->feature at EVERY phase close-out to keep the branch a clean fast-forward.
**What was actually correct**: Sync main->feature only at final close-out (or if/when main actually advances) — NOT per phase. O-04's final merge-back checklist covers it.
**Why**: User feedback: "that's a bit much, just do it on closeout not each phase... I'm only working on one feature right now." With no competing branches landing on main, the fast-forward invariant holds without per-phase merges, so they are pure overhead.
