# Empirical self-improvement loop - telemetry-gated curator and loop-gameplan primitive — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-21

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Telemetry substrate & baseline | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Utility & failure-risk scoring (advisory) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The Curator - propose-confirm maintenance pass | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Empirical-gated promotion & typed-edge risk surfacing | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | The loop-gameplan primitive | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, dogfood & ship | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests: 548 preflight-stamped (pytest, +4 skipped); 554 passing after Phase 0 added 6 telemetry tests; suite green (exit 0)
baseline_corpus_health: pre-loop snapshot: 20 active project lessons, 0 redundant pairs (Jaccard>=0.6), 20 never-surfaced, 0 telemetry events, pass_rate null
telemetry_substrate: .clauderizer/telemetry.jsonl (append-only); src/clauderizer/telemetry.py = record_surfaced/record_outcome/read_events/corpus_health; written only by cz_write_handoff (surfaced) + cz_transition_phase complete|failed (outcome), both under the H-05 lock; never from a hook (INVARIANT-06)
new_read_op: cz_corpus_health (writes=False); MCP/CLI tool surface 31 -> 32; tests/test_telemetry.py = 6 tests incl. the cz_write_handoff->surfaced and cz_transition_phase->outcome wiring proof
```

### Phase 1 Outputs

```
scoring_op: cz_lesson_health (writes=False; tool surface 32->33): per-lesson utility = passed/resolved surfacings, failure_risk = 1-utility, surfaced/resolved counts, last_surfaced (recency/time-decay input), and an advisory signal (never-surfaced | low-utility-review | promotion-candidate). Join key = (gameplan, phase) across surfaced + outcome telemetry events.
validation: deterministic labeled-sample held-out-judgment eval (tests/test_lesson_health.py, 5 tests): a good lesson (surfaced -> always passed) scores utility 1.0 + 'promotion candidate'; a bad one (-> always failed) 0.0 + 'review'; an unused one 'never-surfaced'; window-recency confirmed (full 0.5 vs window=2 1.0). This is more reproducible than an LLM agent-eval, which the Phase 2 A/B adds.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
