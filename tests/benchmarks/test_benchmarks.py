"""Phase 0 self-tests for the memory-eval harness.

The standing, deterministic gate: metric correctness, a ranker baseline, and the
load-bearing self-test that the harness DETECTS a regression (a relevance-blind
ranker must score strictly worse). If this file is green, the harness has teeth
and later phases can trust its verdicts.
"""
from __future__ import annotations

import os
from contextlib import contextmanager

from clauderizer import config as cfg
from clauderizer import paths as P
from tests.benchmarks import corpora, harness, metrics


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- metric correctness (pure, no engine) -----------------------------------

def test_recall_at_k():
    assert metrics.recall_at_k(["a", "b", "c"], ["a", "c"], 3) == 1.0
    assert metrics.recall_at_k(["a", "b", "c"], ["a", "z"], 3) == 0.5
    assert metrics.recall_at_k(["b", "c", "a"], ["a"], 2) == 0.0  # a is below k
    assert metrics.recall_at_k(["x"], [], 3) == 1.0  # vacuous for abstention


def test_precision_at_k():
    assert metrics.precision_at_k(["a", "b"], ["a"], 2) == 0.5
    assert metrics.precision_at_k([], ["a"], 2) == 0.0


def test_ndcg_rewards_top_rank():
    top = metrics.ndcg_at_k(["a", "x", "y"], ["a"], 3)
    low = metrics.ndcg_at_k(["x", "y", "a"], ["a"], 3)
    assert top == 1.0
    assert low < top


def test_mrr():
    assert metrics.reciprocal_rank(["x", "a"], ["a"]) == 0.5
    assert metrics.reciprocal_rank(["a", "x"], ["a"]) == 1.0
    assert metrics.reciprocal_rank(["x", "y"], ["a"]) == 0.0


def test_token_estimate_matches_engine_convention():
    assert metrics.token_estimate("a" * 8) == 2  # len // 4


def test_contradiction_detects_stale_over_current():
    assert metrics.contradiction(["old", "new"], ["new"], ["old"]) is True
    assert metrics.contradiction(["new", "old"], ["new"], ["old"]) is False
    assert metrics.contradiction(["new"], ["new"], ["old"]) is False


def test_dag_validity_primitives():
    clean = {"a": ["b"], "b": ["c"], "c": []}
    assert metrics.dangling_edges(clean, ["a", "b", "c"]) == []
    assert metrics.has_cycle(clean) is False
    # an edge to an unknown id is dangling, not a cycle
    assert metrics.dangling_edges({"a": ["z"]}, ["a"]) == [("a", "z")]
    assert metrics.has_cycle({"a": ["z"]}) is False
    # a -> b -> a is a cycle
    assert metrics.has_cycle({"a": ["b"], "b": ["a"]}) is True


# --- ranker baseline (in-memory corpus) -------------------------------------

# k < corpus size, so recall@k is position-sensitive (k >= N makes it trivially 1.0).
_K = 3


def test_ranker_baseline_meets_threshold():
    res = harness.run_ranker(corpora.RANKER_ENTRIES, corpora.RANKER_PROBES, k=_K)
    assert res["recall_at_k"] >= 0.9
    assert res["mrr"] >= 0.9
    assert res["ndcg_at_k"] >= 0.9
    assert res["abstention_rate"] == 1.0


# --- the load-bearing self-test: the harness catches a regression -----------

def test_harness_detects_ranker_regression():
    good = harness.run_ranker(corpora.RANKER_ENTRIES, corpora.RANKER_PROBES, k=_K,
                              rank_fn=harness.rank_ids)
    bad = harness.run_ranker(corpora.RANKER_ENTRIES, corpora.RANKER_PROBES, k=_K,
                             rank_fn=harness.degraded_rank_ids)
    # A relevance-blind ranker MUST score strictly worse on every position-aware
    # metric — proof the gate has teeth and can catch a real regression.
    assert bad["mrr"] < good["mrr"]
    assert bad["ndcg_at_k"] < good["ndcg_at_k"]
    assert bad["recall_at_k"] < good["recall_at_k"]
    assert bad["abstention_rate"] < good["abstention_rate"]


# --- engine-level abilities: knowledge-updates + abstention -----------------

def test_supersession_contradiction_is_visible_at_baseline(temp_repo):
    paths, _ = _ctx(temp_repo)
    probes = corpora.seed_decisions(paths)
    res = harness.run_engine_probes(paths, probes, k=5)
    # Baseline weakness the harness must SEE: the flat-status model lets the
    # superseded decision outrank the current one. Phase 4's target is 0.0.
    assert res["contradiction_rate"] > 0.0
    # The current decision is still retrieved (recall intact); only ordering is wrong.
    assert res["recall_at_k"] == 1.0
    # An absent topic surfaces nothing — deterministic abstention.
    assert res["abstention_rate"] == 1.0


# --- context-token measurement works (real numbers captured as outputs) -----

def test_context_token_measurement_runs(temp_repo):
    paths, config = _ctx(temp_repo)
    out = harness.measure_context_tokens(paths, config)
    assert out["digest_tokens"] > 0
