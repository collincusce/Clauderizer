# ranker-spike — Post-Mortem

> Gameplan: 2026-06-24-ranker-spike (driven, single-phase)
> Closed: 2026-06-24
> Verdict: **DISCARD** (a successful, pre-registered null — L-32 / L-39)

## Verdict (one line)

Length-normalized stdlib BM25/Okapi **tied** the shipped raw-overlap baseline at
the **1.0000 ceiling** on every gate metric, with both guards flat ⇒ **DISCARD**
per D1's pre-registered rule. Nothing shipped to `src/`; RRF / MMR / recency /
graph-expansion remain parked.

## What was tested (the pre-registration — D1)

`analyze.rank_relevant` scores by **raw token-overlap COUNT** — no IDF, no length
normalization — so a verbose entry can win on token volume alone. The 2026-06-24
deep-research surfaced length-normalized **stdlib BM25/Okapi** as the deterministic
fix. D1 pre-registered ONE measured experiment with a binding keep/discard rule:

- **KEEP** only on a *clearly meaningful lift* on extraction + multi_session
  recall@k / nDCG / MRR, **with no regression** on multi_session precision or the
  knowledge_updates contradiction rate.
- Otherwise **DISCARD** (a discard is a success — L-17 / L-32).
- Hard constraints: deterministic, **stdlib-only**, ZERO new runtime dependency
  (reaffirms D-014 / L-14). Do NOT pre-build RRF/MMR/recency/graph-expansion.

**Method.** A faithful score-formula swap, built off shipped code under
`_experiments/bm25_spike.py`: same tokenizer (`analyze._tokens` / `_STOP` /
`_WORD_RE`), same id-boost, same stale-demotion secondary sort — only the primary
score changed from `len(qtok & dtok)` to Okapi BM25 (k1=1.5, b=0.75, Lucene
non-negative IDF). Scored on the **identical** `tests/benchmarks` fixtures + harness
(`harness.run_ranker`); the knowledge_updates contradiction guard was measured on the
**real** engine path (`analyze.analyze` over a seeded temp repo) by an in-process
monkeypatch — so `src/` was never modified on disk.

## Measured results (gate k=3; identical at k=1 and k=5)

| Metric (group) | Baseline | BM25 | Δ |
|---|---|---|---|
| **LIFT** — combined extraction+multi_session recall@k | 1.0000 | 1.0000 | +0.0000 |
| **LIFT** — combined nDCG@k | 1.0000 | 1.0000 | +0.0000 |
| **LIFT** — combined MRR | 1.0000 | 1.0000 | +0.0000 |
| **GUARD** — multi_session precision@k | 0.7500 | 0.7500 | +0.0000 |
| **GUARD** — knowledge_updates contradiction_rate | 0.0000 | 0.0000 | +0.0000 |
| abstention_rate | 1.0000 | 1.0000 | +0.0000 |

Diagnostic (non-gating) BM25 `b`-sweep over {0.0, 0.25, 0.5, 0.75, 1.0}: combined
recall/nDCG/MRR pinned at **1.0000** at every length-normalization strength — the
mechanism's defining parameter does not move the ordering on this corpus.

Best LIFT Δ = **+0.0000**, far below the pre-registered **0.02** meaningful
threshold; guards held. ⇒ **DISCARD** (script exit code 2). Full suite green:
**620 passed / 624 collected** (4 platform skips), benchmarks 11/11, and the
load-bearing `test_harness_detects_ranker_regression` still passes.

## Root cause — why the null

The gate fixture (`RANKER_ENTRIES`) is **deliberately disjoint**: five entries on
non-overlapping topics (Postgres / React / Redis / Kafka / S3). On such a corpus the
raw-overlap count ranker already separates every query's single relevant entry
cleanly, so the baseline is **saturated at the 1.0 ceiling** — there is *no
headroom* for any scorer to improve. BM25's IDF and length normalization change the
score *magnitudes* but not the *ordering* when each query has exactly one
multi-token match and the rest have zero. This is precisely D1's pre-registered
skepticism confirmed: on a tiny, structured corpus IDF is near-uniform and the
transfer of published large-corpus IR gains **did not occur**.

## What worked (process)

- **Pre-registration made the verdict mechanical.** With D1's rule and threshold
  fixed before measuring, the DISCARD fell out of the numbers — no room to "talk
  myself into a keep" (L-32).
- **Clean isolation.** Branch `experiment/ranker-spike`; the candidate lived only
  under `_experiments/` (pytest `testpaths=["tests"]` never collects it); `src/` and
  `tests/` were untouched, so the suite count was invariant by construction.
- **Faithful single-variable swap.** Reusing the engine's exact tokenizer and
  mirroring `rank_relevant`'s structure meant any delta was attributable to the
  score formula alone — and the delta was zero.
- **Real-path guard measurement.** The contradiction rate was measured through the
  actual `analyze.analyze` surface via an in-process monkeypatch over a seeded temp
  repo — no disk write to `src/`, yet the genuine engine path.

## What didn't / limitations (honest)

- **The fixtures cannot falsify the hypothesis.** A saturated corpus can only prove
  *no regression*; it can never demonstrate *lift*. So this experiment establishes
  "BM25 is harmless here", **not** "BM25 has no value on realistic Clauderizer
  corpora" (dense, longer, overlapping entries). That stronger claim is unproven.
- **The knowledge_updates guard held only because the fixture isn't
  length-adversarial.** The seeded supersession pair did not exercise BM25's real
  risk: length normalization breaks the stale-vs-current *secondary-sort tie* that
  supersession-demotion relies on, so a length-asymmetric stale/current pair could
  in principle invert the order. The 0.0→0.0 result is a **fixture gap, not a safety
  proof** (captured in L-39's watch-out).

## Procedure improvements

- When a gain-gate's existing fixtures are **saturated**, build the **adversarial
  fixture targeting the new mechanism FIRST**, then measure — otherwise the gate can
  only ever return DISCARD/break-even (promoted as **L-39**, extending L-32's
  saturated-target corollary with a fixture-design corollary).
- For any future ranker scoring change, add a **length-adversarial knowledge_updates
  fixture** before trusting the contradiction guard.

## Open threads (parked, not lost)

1. **RRF / MMR / recency / graph-expansion** — parked per D1 until the ranker is
   proven movable on this corpus shape. It was not. Revisit only with realistic /
   adversarial fixtures in hand.
2. **If the ranker is ever revisited**: first add length-bias, near-duplicate, and
   term-frequency-skew fixtures (and the length-adversarial supersession fixture
   above), then re-run this exact gate. The `_experiments/bm25_spike.py` harness is
   reusable as-is.
3. **`docs/LESSONS.md` re-distillation** — now 24 active project lessons (> 20), but
   `cz_corpus_health` reports **0 redundant pairs**, so there is no quick
   consolidation win; it needs a deliberate utility-based pass (5 never-surfaced:
   L-23, L-03, L-05, L-36, L-04 — candidates to review, not blindly obsolete).
4. **Next initiative**: the queued `2026-06-24-critique-bias-hardening` gameplan
   (CALM self-enhancement / authority for `cz_critique`) — another empirical gate
   that L-39 directly informs. `active_gameplan` is cleared on close; activate it in
   a future session.

## Provenance

- `_experiments/bm25_spike.py` — the candidate scorer + comparison harness (exit
  code 2 = DISCARD). Does not run in CI.
- `_experiments/RESULTS.txt` — captured run output (the full per-k tables + sweep).
- `PHASE-STATUS.md` Outputs Registry — `baseline_ranker_metrics`,
  `bm25_candidate_metrics`, `verdict`, `suite_baseline_reconciled`.
- `docs/LESSONS.md` — **L-39** (Eval methodology), promoted from this gameplan's
  lesson #1.
- D1 (this gameplan's Decisions) — the pre-registration record (left as written).
