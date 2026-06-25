# critique-bias-hardening — Post-Mortem

> Gameplan: 2026-06-24-critique-bias-hardening (driven, single-phase)
> Closed: 2026-06-24
> Verdict: **KEEP** (a measured, pre-registered positive — the inverse of the ranker-spike null)
> Shipped: `cz_critique` CALM anti-bias axes, released in 1.1.0

## Verdict (one line)

Two CALM-derived advisory axes (Self-enhancement, Authority) added to the `cz_critique`
reference-free rubric **caught 100% (17/17) of planted biases the prior rubric scored
clean, with zero false-positives on 15 sound cases**, and — the property that makes the
result credible — **beat a deliberately naive strawman on 6 of 7 adversarial near-misses**.
⇒ **KEEP** per D1's pre-registered gain-gate. Deterministic, stdlib-only, no new
dependency, advisory.

## What was tested (the pre-registration — D1)

`cz_critique` is a reference-free judge over Coverage / Coherence / Grounding that, in
practice, grades the agent's OWN output — the textbook trigger for self-enhancement bias
(CALM, Ye et al.). D1 pre-registered extending the rubric with two CALM-derived ADVISORY
axes — self-enhancement (always applicable; the target is self-authored) and authority
(deference to a citation that doesn't resolve against the evidence field) — as deterministic
engine-surfacing + rubric prose, never a runtime dependency (the D-017 / STORM precedent).
Binding gain-gate:

- **KEEP** only if the additions surface a degenerate/self-enhanced critique the PRIOR
  rubric scored clean, **without** flagging sound critiques.
- Otherwise **PARK/DISCARD** (a discard is a success — L-32).
- Hard constraints: deterministic, **stdlib-only**, ZERO new dependency, advisory (the
  agent grades — INVARIANT-05), no enable/disable flag (D-015).

## Method

Built the measuring stick FIRST (O-01; the L-39 discipline). Three pure classifiers in
`rituals/critique.py` — `_evidence_is_authority`, `_resolution_is_hollow`, `_overclaims` —
each pairing a fingerprint (an external-authority appeal / a filler closure / a completion
intensifier) with an **in-repo-anchor precision guard** (presence of a commit, path, test
count, metric, phase/date, or run ratio). Wired as two appended advisory dimensions; the
existing Coverage / Coherence / Grounding dimensions and their order are unchanged. Measured
on a 32-case labeled fixture (`_experiments/fixture.json`) via `_experiments/measure.py`,
which scores the shipped classifiers against (a) a deliberately NAIVE strawman
(fingerprint-only, no anchor guard / a length threshold) and (b) the prior rubric (no bias
axis — detection 0 by construction).

## Measured results (`_experiments/results.json`)

| Axis | Principled (shipped) | Naive strawman | Prior rubric |
|---|---|---|---|
| authority | 100% det / 0% FP / 100% prec | 100% det / **33% FP** | 0% (no check) |
| hollow resolution | 100% det / 0% FP / 100% prec | **67% det** / 20% FP | 0% |
| overclaim | 100% det / 0% FP / 100% prec | 100% det / **50% FP** | 0% |
| **aggregate** | **17/17 detected, 0 FP on 15 sound** | — | 0/17 |

On the **7 adversarial near-misses** the naive strawman is wrong on **6**; the shipped
detector is wrong on **0**. Full suite **626 passed** (620 baseline + 6 new critique tests),
0 failures; live `cz_critique` returns 5 dimensions and stays clean on the real gameplan.

## Root cause — why the positive (and why it's not the ranker-spike null)

The ranker-spike DISCARD came from a **saturated** fixture (baseline at the 1.0 ceiling, no
headroom — no change could ever show lift). This fixture is the opposite: it has
**discriminating power**. It FAILS a naive detector (20–50% FP on the near-misses) while the
principled one passes. A measuring stick that can tell a good detector from a bad one is what
makes a 100% / 0% result evidence rather than a self-fulfilling artifact. The prior rubric
genuinely missed these biases — they hide behind an evidence marker (authority) or a checked
box (hollow closure), exactly where the old Coverage / Grounding checks look clean.

## What worked (process)

- **Fixture first, with a strawman.** Building the labeled fixture and a naive baseline
  before tuning the detector turned "does it work?" into a number, and the near-miss-vs-
  strawman contrast made the KEEP defensible instead of teaching-to-the-test.
- **Anchor-guard mechanism.** Pairing each fingerprint with an in-repo-anchor check is what
  buys precision — it is the difference between the 0% and 33–50% false-positive columns.
- **Purely additive integration.** Existing dimensions untouched; the only test that changed
  asserted the old three-dimension contract. Suite delta was +6, zero regressions.

## What didn't / limitations (honest)

- **Single-author fixture.** I wrote both the fixture and the detector, so the 100% / 0% is
  partly correlated by construction. The near-miss-vs-strawman contrast mitigates this but
  does not eliminate it: the real validation is whether these axes fire usefully (and
  quietly) on REAL critiques over future sessions. Captured as L-40.
- **Overclaim is the weakest axis.** It only fires in integration when a completion claim
  COEXISTS with a live objective gap, and it scans only the explicit completion-summary
  section to avoid boilerplate false positives — so a self-congratulatory note written
  elsewhere would be missed. Acceptable for an advisory surface.
- **No real-corpus base rate yet.** We know the checks are precise on crafted cases; we do
  not yet know how OFTEN they fire on genuine work (could be rarely). An observation to
  collect, not a blocker.

## Procedure improvements

- Promoted **L-40** (Eval methodology): when you author both the fixture and the detector,
  give the fixture discriminating power — adversarial near-misses + a naive strawman the
  fixture must DEFEAT — or a 100% result is confirmation bias. Extends L-39 (build the
  adversarial fixture first) with the strawman corollary.

## Open threads (parked, not lost)

1. **Real-critique validation.** Over the next handful of real `cz_critique` runs, watch
   whether Self-enhancement / Authority fire on genuine biases without noise; if they never
   fire or fire noisily, refine the patterns in `rituals/critique.py`.
2. **The rest of CALM's 12-bias taxonomy** stays parked (per D1): position bias applies to
   multi-candidate judging, not single-target critique; add others only when one demonstrably
   fires on real critiques.
3. **`docs/LESSONS.md` re-distillation** — now 25 active project lessons (> 20) after L-40;
   `cz_corpus_health` reported 0 redundant pairs at last check, so it needs a deliberate
   utility-based pass (the ranker-spike post-mortem named 5 never-surfaced candidates:
   L-23, L-03, L-05, L-36, L-04 — review, don't blindly obsolete).

## Provenance

- `_experiments/fixture.json` — 32 labeled cases (authority / hollow-resolution / overclaim)
  with adversarial near-misses; the ground-truth measuring stick, authored before the detector.
- `_experiments/measure.py` — principled vs naive-strawman vs prior harness (writes results.json).
- `_experiments/results.json` — captured numbers + the gate verdict.
- `PHASE-STATUS.md` Outputs Registry — `detection_result`, `fixture_and_harness`,
  `suite_after_change`, `verdict`.
- `src/clauderizer/rituals/critique.py` — the shipped classifiers + two advisory dimensions.
- `tests/test_critique.py` — wiring + the near-miss precision contracts (+6 tests).
- `docs/LESSONS.md` — **L-40** (Eval methodology), promoted from this gameplan's lesson #1.
- D1 (this gameplan's Decisions) — the pre-registration record (left as written).
