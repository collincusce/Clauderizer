#!/usr/bin/env python3
"""Ranker-spike kill-gate experiment (gameplan 2026-06-24-ranker-spike, Phase 0).

PRE-REGISTERED HYPOTHESIS (D1): length-normalized stdlib BM25/Okapi relevance
scoring beats the current raw token-overlap-COUNT baseline of
``analyze.rank_relevant`` on the ``tests/benchmarks`` harness — meaningfully, on
extraction + multi_session recall@k / nDCG / MRR, WITH NO regression on
multi_session precision or the knowledge_updates contradiction rate.

PRE-REGISTERED RULE (D1): KEEP only on a clearly meaningful lift with no guard
regression; otherwise DISCARD. A discard is a successful outcome (L-17 / L-32):
the verdict + the numbers are the deliverable. RRF / MMR / recency /
graph-expansion stay parked unless this proves the ranker is even movable on this
corpus shape.

CONSTRAINTS (non-negotiable): deterministic, STDLIB ONLY — NO numpy / bm25s
(reaffirms D-014 / L-14). This script does NOT modify ``src/clauderizer`` — the
candidate lives here as provenance and is compared against the SHIPPED ranker on
IDENTICAL fixtures. The contradiction-rate path is measured by monkeypatching the
BM25 scorer into the real engine surface IN-PROCESS (no disk write to src).

Run:  .venv/bin/python docs/gameplans/2026-06-24-ranker-spike/_experiments/bm25_spike.py
"""
from __future__ import annotations

import math
import shutil
import sys
import tempfile
from pathlib import Path

# This script lives at docs/gameplans/<id>/_experiments/bm25_spike.py; the repo
# root is four parents up. Put it on sys.path so `clauderizer` and `tests` import
# whether or not the cwd is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from clauderizer import analyze  # noqa: E402  the SHIPPED ranker under comparison
from clauderizer import config as cfg  # noqa: E402
from clauderizer import paths as P  # noqa: E402
from tests.benchmarks import corpora, harness, metrics  # noqa: E402

# Standard Okapi BM25 defaults. Pre-committed BEFORE measuring — not tuned to the
# fixtures (a sweep is reported separately as a diagnostic, never as the gate).
K1 = 1.5
B = 0.75

# Primary gate cutoff: k=3 < corpus size (5), so recall@k is position-sensitive
# (k>=N makes recall trivially 1.0). Matches the standing baseline test's _K.
GATE_K = 3

# "Meaningful lift": at least this absolute gain on a combined LIFT metric, with
# no guard regression. Pre-registered so the verdict is mechanical, not narrated.
MEANINGFUL = 0.02


# --- BM25 scorer (stdlib only) ----------------------------------------------

def _token_list(text: str) -> list[str]:
    """Multiset of distinctive tokens — the SAME filter as ``analyze._tokens``
    (stopwords + (len>=4 or has-digit)) but WITHOUT deduping, so BM25 sees real
    term frequencies and document lengths."""
    return [w for w in analyze._WORD_RE.findall(text.lower())
            if w not in analyze._STOP and (len(w) >= 4 or any(c.isdigit() for c in w))]


def _bm25_scores(query: str, entries: list[dict], k1: float = K1, b: float = B) -> dict:
    """Okapi BM25 score per entry id over the candidate pool ``entries``.

    Corpus statistics (avgdl, document frequency) are computed over the pool that
    is being ranked — the natural BM25 corpus, and exactly the set the shipped
    ranker scores against (``parse_entries(...)`` decisions/invariants, or the
    in-memory ranker fixture). Lucene-style non-negative IDF.
    """
    docs = {e["id"]: _token_list(f"{e['title']} {e['body']}") for e in entries}
    n_docs = len(docs)
    if n_docs == 0:
        return {}
    avgdl = sum(len(d) for d in docs.values()) / n_docs
    df: dict[str, int] = {}
    for d in docs.values():
        for t in set(d):
            df[t] = df.get(t, 0) + 1

    def idf(term: str) -> float:
        n = df.get(term, 0)
        # Lucene/BM25+ non-negative IDF: log(1 + (N - n + 0.5)/(n + 0.5)).
        return math.log(1.0 + (n_docs - n + 0.5) / (n + 0.5))

    qtok = analyze._tokens(query)  # unique query terms, SAME filter as baseline
    scores: dict[str, float] = {}
    for e in entries:
        d = docs[e["id"]]
        dl = len(d)
        tf: dict[str, int] = {}
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for t in qtok:
            f = tf.get(t, 0)
            if f == 0:
                continue
            denom = f + k1 * (1.0 - b + b * (dl / avgdl if avgdl else 0.0))
            s += idf(t) * (f * (k1 + 1.0)) / denom
        scores[e["id"]] = s
    return scores


def bm25_rank_relevant(query: str, entries: list[dict], k: int = 5,
                       exclude_ids: tuple[str, ...] = ()) -> list[dict]:
    """Drop-in shape-match for ``analyze.rank_relevant`` with a BM25 score.

    Mirrors the shipped ranker EXACTLY except the score formula: same id-boost
    (+3, moot for the NL gate probes), same positive-score filter, same
    stale-demotion secondary sort key (stale entries sort after active ones at
    equal score; id breaks remaining ties). Only the primary score changes from
    raw set-overlap COUNT to length-normalized BM25 — so any delta is the score.
    """
    pool = [e for e in entries if e["id"] not in exclude_ids]
    bm = _bm25_scores(query, pool)
    qids = set(analyze._ID_RE.findall(query))
    scored = []
    for e in pool:
        score = bm.get(e["id"], 0.0) + (3.0 if e["id"] in qids else 0.0)
        if score > 0:
            status = str(e.get("status") or "active").lower()
            item = {"id": e["id"], "title": e["title"], "score": score}
            if status != "active":
                item["status"] = status
            scored.append(item)
    scored.sort(key=lambda x: (-x["score"],
                               1 if x.get("status") in analyze._STALE_STATUSES else 0,
                               x["id"]))
    return scored[:k]


# --- rank_fn wrappers for harness.run_ranker --------------------------------

def baseline_rank_ids(query: str, entries: list[dict], k: int) -> list[str]:
    """The SHIPPED raw-overlap ranker (identical to harness.rank_ids)."""
    return [r["id"] for r in analyze.rank_relevant(query, entries, k=k)]


def bm25_rank_ids(query: str, entries: list[dict], k: int) -> list[str]:
    return [r["id"] for r in bm25_rank_relevant(query, entries, k=k)]


# --- measurement helpers -----------------------------------------------------

def _ability(probes, name):
    return [p for p in probes if p.ability == name]


def ranker_metrics(rank_fn, k: int) -> dict:
    """Per-ability + combined ranker metrics on the in-memory fixture corpus."""
    ext = _ability(corpora.RANKER_PROBES, "extraction")
    ms = _ability(corpora.RANKER_PROBES, "multi_session")
    abst = _ability(corpora.RANKER_PROBES, "abstention")
    combined = ext + ms
    re_ext = harness.run_ranker(corpora.RANKER_ENTRIES, ext, k=k, rank_fn=rank_fn)
    re_ms = harness.run_ranker(corpora.RANKER_ENTRIES, ms, k=k, rank_fn=rank_fn)
    re_comb = harness.run_ranker(corpora.RANKER_ENTRIES, combined, k=k, rank_fn=rank_fn)
    re_abst = harness.run_ranker(corpora.RANKER_ENTRIES, abst, k=k, rank_fn=rank_fn)
    return {
        "extraction": re_ext,
        "multi_session": re_ms,
        "combined": re_comb,
        "abstention_rate": re_abst["abstention_rate"],
    }


def contradiction_rate(rank_impl) -> dict:
    """knowledge_updates contradiction rate via the REAL engine surface.

    Seeds the supersession pair into a throwaway copy of the sample repo, then
    monkeypatches ``rank_impl`` in as ``analyze.rank_relevant`` (restored in
    ``finally``) so ``analyze.analyze`` -> the candidate scorer drives the
    measured path. No disk write to src.
    """
    src = _REPO_ROOT / "tests" / "fixtures" / "sample_repo"
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        shutil.copytree(src, repo)
        paths = P.resolve(repo)
        cfg.Config.load(paths.config_file)  # parity with the harness ctx
        probes = corpora.seed_decisions(paths)
        orig = analyze.rank_relevant
        try:
            analyze.rank_relevant = rank_impl
            res = harness.run_engine_probes(paths, probes, k=5)
        finally:
            analyze.rank_relevant = orig
    return res


# --- reporting ---------------------------------------------------------------

def _fmt(x: float) -> str:
    return f"{x:.4f}"


def _row(label, base, cand):
    delta = cand - base
    arrow = "→" if abs(delta) < 1e-9 else ("▲" if delta > 0 else "▼")
    return f"  {label:<28} base={_fmt(base)}  bm25={_fmt(cand)}  Δ={delta:+.4f} {arrow}"


def main() -> int:
    print("=" * 78)
    print("RANKER-SPIKE: stdlib BM25/Okapi  vs  raw token-overlap baseline")
    print(f"params: k1={K1} b={B}   gate_k={GATE_K}   meaningful_lift>={MEANINGFUL}")
    print("=" * 78)

    base = {k: ranker_metrics(harness.rank_ids, k) for k in (1, 3, 5)}
    cand = {k: ranker_metrics(bm25_rank_ids, k) for k in (1, 3, 5)}

    for k in (1, 3, 5):
        print(f"\n--- k={k} -------------------------------------------------------------")
        b, c = base[k], cand[k]
        print(" extraction (recall / nDCG / MRR):")
        print(_row("recall@k", b["extraction"]["recall_at_k"], c["extraction"]["recall_at_k"]))
        print(_row("ndcg@k", b["extraction"]["ndcg_at_k"], c["extraction"]["ndcg_at_k"]))
        print(_row("mrr", b["extraction"]["mrr"], c["extraction"]["mrr"]))
        print(" multi_session (recall / nDCG / MRR / precision[GUARD]):")
        print(_row("recall@k", b["multi_session"]["recall_at_k"], c["multi_session"]["recall_at_k"]))
        print(_row("ndcg@k", b["multi_session"]["ndcg_at_k"], c["multi_session"]["ndcg_at_k"]))
        print(_row("mrr", b["multi_session"]["mrr"], c["multi_session"]["mrr"]))
        print(_row("precision@k [GUARD]", b["multi_session"]["precision_at_k"], c["multi_session"]["precision_at_k"]))
        print(" combined extraction+multi_session [LIFT metrics]:")
        print(_row("recall@k", b["combined"]["recall_at_k"], c["combined"]["recall_at_k"]))
        print(_row("ndcg@k", b["combined"]["ndcg_at_k"], c["combined"]["ndcg_at_k"]))
        print(_row("mrr", b["combined"]["mrr"], c["combined"]["mrr"]))
        print(_row("abstention_rate", b["abstention_rate"], c["abstention_rate"]))

    # knowledge_updates contradiction rate (GUARD) via the real engine surface.
    print("\n--- knowledge_updates (seeded repo, real engine path) ----------------")
    base_ku = contradiction_rate(analyze.rank_relevant)
    cand_ku = contradiction_rate(bm25_rank_relevant)
    print(_row("contradiction_rate [GUARD]", base_ku["contradiction_rate"], cand_ku["contradiction_rate"]))
    print(_row("recall@k (current retrieved)", base_ku["recall_at_k"], cand_ku["recall_at_k"]))
    print(_row("abstention_rate", base_ku["abstention_rate"], cand_ku["abstention_rate"]))

    # --- apply D1's pre-registered rule at the gate k ------------------------
    b, c = base[GATE_K], cand[GATE_K]
    lift_metrics = {
        "combined recall@k": (b["combined"]["recall_at_k"], c["combined"]["recall_at_k"]),
        "combined ndcg@k": (b["combined"]["ndcg_at_k"], c["combined"]["ndcg_at_k"]),
        "combined mrr": (b["combined"]["mrr"], c["combined"]["mrr"]),
    }
    guard_metrics = {
        "multi_session precision@k": (b["multi_session"]["precision_at_k"], c["multi_session"]["precision_at_k"]),
        "contradiction_rate": (base_ku["contradiction_rate"], cand_ku["contradiction_rate"]),
    }

    print("\n" + "=" * 78)
    print(f"VERDICT (D1 pre-registered rule, gate k={GATE_K})")
    print("=" * 78)
    best_lift = max(c - b for b, c in lift_metrics.values())
    meaningful_lift = best_lift >= MEANINGFUL
    any_lift_regressed = any(c < b - 1e-9 for b, c in lift_metrics.values())
    # Guards: precision must not drop; contradiction_rate must not rise.
    prec_b, prec_c = guard_metrics["multi_session precision@k"]
    con_b, con_c = guard_metrics["contradiction_rate"]
    guard_ok = (prec_c >= prec_b - 1e-9) and (con_c <= con_b + 1e-9)

    print(" LIFT metrics (need a meaningful gain, none regressing):")
    for name, (bv, cv) in lift_metrics.items():
        print(_row(name, bv, cv))
    print(f"   best lift = {best_lift:+.4f}  (meaningful>={MEANINGFUL}? {meaningful_lift};"
          f" any lift regressed? {any_lift_regressed})")
    print(" GUARD metrics (must NOT regress):")
    for name, (bv, cv) in guard_metrics.items():
        print(_row(name, bv, cv))
    print(f"   guards hold? {guard_ok}")

    keep = meaningful_lift and (not any_lift_regressed) and guard_ok
    verdict = "KEEP" if keep else "DISCARD"
    print("\n" + "-" * 78)
    print(f"  ==> {verdict}")
    if not keep:
        reasons = []
        if not meaningful_lift:
            reasons.append(f"no meaningful lift (best Δ={best_lift:+.4f} < {MEANINGFUL})")
        if any_lift_regressed:
            reasons.append("a LIFT metric regressed")
        if not guard_ok:
            if prec_c < prec_b - 1e-9:
                reasons.append(f"multi_session precision regressed ({prec_b:.4f}->{prec_c:.4f})")
            if con_c > con_b + 1e-9:
                reasons.append(f"contradiction_rate regressed ({con_b:.4f}->{con_c:.4f})")
        print("      reason(s): " + "; ".join(reasons))
        print("      -> change NOTHING in src/; RRF/MMR/recency/graph-expansion stay parked.")
        print("      -> a discard is a SUCCESS (L-32): the null + the numbers are the memory.")
    else:
        print("      -> KEEP: do NOT ship inline. Per O-01, rank_relevant's consumers")
        print("         (analyze gate, handoff lesson-pointer, edge-suggester) need a")
        print("         cz_cascade + an AMENDED ship phase. Stop for review.")
    print("-" * 78)

    # --- diagnostic sensitivity sweep (NOT the gate) -------------------------
    # Characterizes whether the BM25 mechanism even fires on this corpus shape,
    # across b (length-normalization strength). Reported for provenance only.
    print("\n[diagnostic, non-gating] BM25 b-sweep on combined recall/ndcg/mrr @k=3:")
    for bb in (0.0, 0.25, 0.5, 0.75, 1.0):
        def _rf(q, ents, k, _bb=bb):
            return [r["id"] for r in _sweep_rank(q, ents, k, b=_bb)]
        rc = harness.run_ranker(
            corpora.RANKER_ENTRIES,
            _ability(corpora.RANKER_PROBES, "extraction") + _ability(corpora.RANKER_PROBES, "multi_session"),
            k=3, rank_fn=_rf)
        print(f"   b={bb:<4}  recall={_fmt(rc['recall_at_k'])}  "
              f"ndcg={_fmt(rc['ndcg_at_k'])}  mrr={_fmt(rc['mrr'])}")

    print("\n(Provenance: this script does not run in CI; the gate is D1's rule above.)")
    return 0 if keep else 2  # exit 2 == DISCARD (a successful, recorded null)


def _sweep_rank(query, entries, k=5, b=B):
    """bm25_rank_relevant with a variable b, for the diagnostic sweep only."""
    pool = list(entries)
    bm = _bm25_scores(query, pool, k1=K1, b=b)
    scored = []
    for e in pool:
        score = bm.get(e["id"], 0.0)
        if score > 0:
            scored.append({"id": e["id"], "title": e["title"], "score": score})
    scored.sort(key=lambda x: (-x["score"], x["id"]))
    return scored[:k]


if __name__ == "__main__":
    raise SystemExit(main())
