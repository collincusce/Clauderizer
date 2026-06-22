# Empirical self-improvement loop - telemetry-gated curator and loop-gameplan primitive — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-21

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Telemetry substrate & baseline | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Utility & failure-risk scoring (advisory) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The Curator - propose-confirm maintenance pass | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Empirical-gated promotion & typed-edge risk surfacing | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-3-HANDOFF.md |
| 4 | The loop-gameplan primitive | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-4-HANDOFF.md |
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

### Phase 2 Outputs

```
curator_op: cz_curate (writes=False; tool surface 33->34): read-only, propose-only (like cz_mine_failures). From lesson_health + lexical redundancy it proposes 4 action kinds, each with evidence + the blessed cz_* op to apply it: consolidate (redundant project-lesson pair -> cz_obsolete_lesson the dup into the higher-utility kept one), obsolete (never-surfaced, or utility<=0.2 over >=2 resolved -> cz_obsolete_lesson), flag (0.2<utility<=0.5 -> review, no auto-op), promote (high-utility gameplan lesson -> cz_promote_lesson).
ab_validation: A/B (tests/test_curator.py): seed a 4-lesson corpus (1 redundant pair + 1 never-surfaced + 1 healthy); corpus_health redundant_pairs=1 before. Apply the curator's consolidate+obsolete proposals via the blessed cz_obsolete_lesson; after: redundant_pairs=0 and fewer active lessons (health improved), and the KEPT lesson still ranks top-k for its topic via the handoff ranker (recall@k preserved, no regression). 6 curator tests; suite 559->565 passing green.
```

### Phase 3 Outputs

```
typed_edges: analyze.suggest_edges labels each suggestion with kind: redundant (shared/min distinctive-tokens >= 0.8, near-duplicate purpose) or related (plausible depends_on). alternative stays agent-assignable (D-018; amendment A-001). Carried through cz_analyze.
risk_cascade: cascade.render_report adds a 'Preemptive risk' section when the cascaded entity's status is shaky (superseded/deprecated/blocked): it flags each direct + transitive dependent to verify - the cascade-walk analogue of SkillOps risk propagation. Deterministic, advisory (INVARIANT-05).
promotion_gate: Curator promote requires empirical recurrence (>=2 resolved surfacings) AND correlation with passing (utility>=0.8) - Darwin-Godel-style validation. Tested: a single surfacing, or utility 0.5, is gated out; two passing surfacings -> promote.
```

### Phase 4 Outputs

```
loop_step_op: cz_loop_step (writes=False; tool surface 34->35): one loop iteration = corpus_health convergence metric + cz_curate proposals + converged flag (no actionable consolidate/obsolete/promote left) + spawn_gameplan escape hatch (>=3 review-flags -> suggest a driven gameplan). Read-only; the agent applies actionable proposals via blessed writes and re-calls until converged.
kind_loop: cz_create_gameplan(kind='driven'|'loop'); kind rendered as '> Kind: <kind>' in GAMEPLAN.md. A loop gameplan is the standing iterative maintenance type; a driven gameplan is the finite phase DAG.
convergence_proof: K-iteration test (tests/test_loop_gameplan.py): seed redundant + never-surfaced + healthy lessons; drive loop_step -> apply obsolete proposals -> repeat; proposals converge to 0 and the corpus-health metric is monotone-improving (redundant_pairs/never_surfaced non-increasing), ending redundant_pairs=0. Escape-hatch + read-only also tested.
procedure_doc: GAMEPLAN-PROCEDURE.md bumped 1.2.1 -> 1.3.0 (MINOR) in BOTH the bundled template and the repo copy (L-21 sweep): new 'Loop Gameplans (kind: loop)' section - trigger / iteration body / per-iteration exit (the /goal triad) / convergence metric / spawn-driven escape hatch; driven and loop gameplans interlock.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
