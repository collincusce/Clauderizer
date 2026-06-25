"""Phase-0 self-tests for the cost harness (gameplan abstract-index-fast-retrieval).

The standing, deterministic proof that the COST gate has teeth BEFORE the feature
exists: a negative control must show ~0 saving, the real mechanism must show a
large saving at no accuracy cost, and an accuracy-trap that saves tokens by
DROPPING the answer must be rejected by the guard. If this file is green, a KEEP
in Phase 3 means a real, measured token win — not a harness that rubber-stamps.
(Mirrors test_benchmarks.test_harness_detects_ranker_regression; see L-39/L-40.)
"""
from __future__ import annotations

from tests.benchmarks import cost, metrics


def test_cost_reuses_the_engine_token_convention():
    # The cost accounting must use the engine's own len//4 proxy, not a private one.
    assert cost.token_estimate is metrics.token_estimate


def test_negative_control_shows_no_saving():
    # Injecting full bodies as 'abstracts' is the status quo — it must save nothing,
    # and therefore must NOT clear the gate.
    res = cost.evaluate(cost.COST_LOOKUPS, cost.noop_full)
    assert res["mean_saving"] < 0.02
    assert cost.verdict(res) == "DISCARD"


def test_real_mechanism_clears_the_gate_with_headroom():
    res = cost.evaluate(cost.COST_LOOKUPS, cost.abstract_then_fetch)
    assert res["mean_saving"] >= cost.MIN_SAVING       # clears the pre-registered bar
    assert res["mean_saving"] > 0.5                    # ...with real headroom (multi-x)
    assert res["candidate_accuracy"] == res["baseline_accuracy"] == 1.0
    assert res["max_round_trips_candidate"] <= cost.MAX_ROUND_TRIPS
    assert cost.verdict(res) == "KEEP"


def test_harness_discriminates_real_from_control():
    real = cost.evaluate(cost.COST_LOOKUPS, cost.abstract_then_fetch)["mean_saving"]
    ctrl = cost.evaluate(cost.COST_LOOKUPS, cost.noop_full)["mean_saving"]
    # The gap between the real mechanism and the no-op IS the harness's teeth.
    assert real - ctrl > 0.4


def test_accuracy_guard_rejects_token_cheap_but_wrong():
    # Tiny abstracts with no fetch DO save tokens — but they drop the answer body,
    # so the accuracy guard must veto the KEEP despite the saving.
    res = cost.evaluate(cost.COST_LOOKUPS, cost.starve)
    assert res["mean_saving"] > 0.5
    assert res["candidate_accuracy"] < res["baseline_accuracy"]
    assert cost.verdict(res) == "DISCARD"


def test_fixture_is_one_of_n():
    # Each lookup must need exactly one of several surfaced bodies — the structure
    # the cost win depends on (most surfaced bodies are dead weight in the baseline).
    for lk in cost.COST_LOOKUPS:
        assert len(lk.answer_ids) == 1
        assert len(lk.surfaced) >= 3
        assert lk.answer_ids[0] in {e["id"] for e in lk.surfaced}
