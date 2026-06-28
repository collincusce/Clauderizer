<!-- Pre-registered BEFORE the feature exists (Phase 0). Do not edit the thresholds
     after measuring — that is the whole point. The verdict is mechanical. -->

# Cost gain-gate — pre-registration (D2)

**Hypothesis.** A deterministic per-entry *abstract index* plus an addressable
`cz_get(id)` lets the agent resolve a memory lookup from compact abstracts +
one targeted body fetch, instead of loading every surfaced body (or a whole
corpus file). This sheds payload tokens **without losing answer accuracy**.

**Why this escapes the L-39 trap.** The 2026-06-24 ranker spike died because its
KPI (recall/nDCG/MRR on disjoint topics) was saturated at 1.0 — no lift was
possible. This KPI is **cost**, which has real headroom: a long body dwarfs an
80-char abstract, so a 1-of-N lookup wastes most of its baseline payload. Cost
can move; recall could not.

## The metric

Per lookup, measured deterministically with the engine's own token proxy
(`metrics.token_estimate`, `len // 4` — no live LLM):

- **saving** = `(baseline_payload_tokens − candidate_payload_tokens) / baseline_payload_tokens`
- **accuracy** = the candidate still has every answer body in context
- **round-trips** = memory tool calls that return content into context

### Cost model

| arm | what it injects | round-trips |
|-----|-----------------|-------------|
| baseline (status quo) | titles, then a whole-block read → **every** surfaced body | 2 (analyze + bulk read) |
| candidate | titles + **abstracts**, then one `cz_get` per body needed (f) | 1 + f |

For the common single-body lookup (f = 1) round-trips are **2 = 2** — equal to
the baseline — so the win is payload, not round-trips. (When an abstract alone
suffices, f = 0 and the candidate is also *fewer* round-trips; the Phase-0 model
conservatively assumes the agent fetches every needed body, understating the win.)

## Pre-registered KEEP rule (frozen)

KEEP **iff all three hold** (else DISCARD — a valid, recorded outcome, L-32):

1. **LIFT** — `mean_saving ≥ 0.30` (`cost.MIN_SAVING`)
2. **GUARD — accuracy** — `candidate_accuracy ≥ baseline_accuracy`
3. **GUARD — round-trips** — `max_round_trips_candidate ≤ 2` (`cost.MAX_ROUND_TRIPS`)

The thresholds live in `tests/benchmarks/cost.py` as constants so the gate is
code, not prose, and cannot drift.

## The fixture has teeth (L-40)

Alongside the real mechanism the harness ships two broken strategies, asserted in
`tests/benchmarks/test_cost.py` (CI-permanent):

- **`noop_full`** (negative control) — abstracts = full bodies → `mean_saving ≈ 0`
  → **DISCARD**. Proves the harness reports no saving where none exists.
- **`starve`** (accuracy trap) — tiny abstracts, no fetch → large saving but the
  answer body is gone → `candidate_accuracy < baseline_accuracy` → **DISCARD**.
  Proves the accuracy guard vetoes a token-cheap-but-wrong strategy.

A KEEP is credible only because these two are rejected on the SAME fixture.

## Phase 3 wiring

Phase 0 fixture is **synthetic** (proves discrimination). Phase 3 replaces
`cost.COST_LOOKUPS` with lookups drawn from the **real** corpus and replaces
`head_abstract` / the fetch with the **real** abstract index + `cz_get`, then
runs `cost.evaluate(...)` → `cost.verdict(...)`. The numbers are recorded as
phase outputs and the KEEP/DISCARD becomes a decision.

Run the Phase-0 discrimination demo:

```
.venv/bin/python docs/gameplans/2026-06-25-abstract-index-fast-retrieval/_experiments/run_cost_harness.py
```
