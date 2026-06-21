# Empirical memory gains — Post-Mortem

> Author: Claude (Opus 4.8) coordinator session
> Date: 2026-06-20
> Scope: Full retrospective on Phases 0–7, planned and executed 2026-06-20 on branch `claude/empirical-memory-gains`.

## Executive Summary

A research-driven initiative to improve Clauderizer's memory workflow under one hard
rule: **every feature must empirically prove a measurable gain or it is parked** (the
gain-gate, D-026). Two deep-research passes fed a gain-gated gameplan; Phase 0 built a
deterministic + agent-eval harness, and each later phase pre-registered a hypothesis,
implemented, ran the gate, and landed only on a measured win. Of six candidate features,
**four landed with measured gains, one was parked, and one was split (drop the bloat form,
keep the focused adaptation)** — exactly the discipline the user asked for: synthesize
only what brings gains, and trim what doesn't. Test suite **400 → 446**, green throughout.

## The measured gains (the deliverable)

| Phase | Feature | Verdict | Measured result |
|---|---|---|---|
| 0 | Eval harness + baseline | shipped | 11 tests; regression self-test proves it catches a degraded ranker (MRR 0.46 vs 1.0); fixed stale `0 tests` baseline → 410 |
| 1 | Focus project lessons in handoff | **KEEP** | handoff **3137 → 1420 tok (−55%)** at **equal** agent-eval accuracy (focused 5/6 = full 5/6); ranker recall@5 = 100% |
| 2 | DAG integrity validation | **KEEP** | dangling + cycle detection (iterative Tarjan); **100% detection, 0 false positives**; filled a real gap (`pin_violations` skipped unknown targets) |
| 3 | Edge-suggester (missing edges) | **KEEP** | **precision 0.75, recall 1.0** on a fixture incl. a generic-collision false positive (bar 0.70); advisory + rejected-pair memory |
| 4 | Supersession back-refs + lifecycle | **KEEP** | stale-fact **contradiction rate 1.0 → 0.0** (measured via the unchanged harness) |
| 5 | Bitemporal valid-time | **PARK** | Phase 4 already saturated the gate metric (contradiction = 0, the floor); valid-time adds no measurable gain for project decisions, at a trim cost |
| 6 | Persistent steering doc | **DROP** (bloat form) / **KEEP** (focused adaptation) | dropped the redundant always-injected doc; kept focused invariant surfacing (fills a real gap — invariants were never surfaced during phase work) |

## What the gameplan got right

1. **The gain-gate caught real problems before they shipped.** The edge-suggester's first
   implementation scored precision **0.103** — boilerplate tokens (`subsys`, `subsystem`)
   made it propose every pair, the textbook over-retrieval failure. The gate forced the
   boilerplate-stripping fix to 0.75. Without the gate it would have shipped as noise.
2. **The harness's own regression self-test had teeth.** Building it surfaced that
   `recall@k` with `k ≥ corpus size` is trivially 1.0 — so the gate scores on
   position-sensitive metrics (MRR/nDCG). A measurement instrument unproven against a
   known regression is decoration.
3. **Dogfooding paid off immediately.** Executing the gameplan *in Clauderizer* surfaced
   prior decisions `D-020`/`D-021`/`D-022` and lesson `L-17`, which pre-shaped Phase 1:
   the digest was already known-small (don't trim it), and "don't truncate lessons" was
   already settled — steering Phase 1 to relevance-focus + pointer-to-canonical instead.
4. **Honest parks keep the system lean.** Two must-earn candidates did not earn their
   place. Parking them is the *point* — for a memory system, less-but-focused beats more
   (the context-rot evidence that motivated the whole trim-first stance).

## What we got wrong / honest caveats

1. **Phase 1 was a Pareto win, not an accuracy win.** The focused-vs-full agent-eval was a
   **tie** (5/6 each), not focused > full — at the current 21-lesson scale the length-harm
   the literature predicts has not yet bitten. The gain is token-cost at held accuracy; it
   grows with lesson count. Stated honestly in `D4`, not oversold.
2. **Phase 6's adherence gain is inherited, not freshly measured.** The focused-invariant
   pointer passes a deterministic *capability* gate (surfaces relevant / skips irrelevant)
   and reuses Phase 1's validated focused-surfacing mechanism, but a dedicated
   invariant-*adherence* agent-eval was not run (recorded as an open item).
3. **Edge-suggester precision (0.75) is fixture-measured.** Real-world precision will vary;
   the advisory + agent-confirm + rejected-pair design absorbs false positives.

## Procedure improvements

- **`tests/benchmarks/` is now a reusable asset.** Future memory-feature work should
  pre-register its hypothesis against this harness (3-stage ablation + 5-ability fixtures)
  rather than reinventing measurement. Consider referencing it from GAMEPLAN-PROCEDURE.
- **Evaluate "must-earn" candidates by analysis when their gate metric is already
  saturated** (Phase 5): building a feature only to measure zero marginal gain burns
  effort to reach a verdict the prior phase's number already implies.
- **A subagent may need to edit a fenced-off baseline-witness test** when a later phase
  closes the gap that test witnessed (Phase 4 flipped `..._is_visible_at_baseline` →
  `..._is_resolved`). The fence should be on the *measurement core* (corpora/metrics), not
  the baseline-witness assertions.

## Open threads (follow-ups, non-blocking)

- **Re-distill the 21 project lessons** (the `> 20` gauge warning predates this gameplan).
  A focused consolidation pass over `docs/LESSONS.md` is its own judgment-heavy task.
- **Dedicated invariant-adherence agent-eval** for the Phase 6 focused-invariant pointer
  (open item recorded).
- **Monitor edge-suggester real-world precision**; tune `min_shared` if noise appears.
- **Bitemporal** remains parked; revisit only if a concrete as-of query need emerges.
