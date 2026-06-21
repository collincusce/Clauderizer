"""Runners for the memory-eval harness: rank a corpus, score it, and measure the
size of what the engine injects. Pure orchestration over the deterministic
metrics in :mod:`metrics` and the fixtures in :mod:`corpora`.

Two ranking functions are provided so the self-test can prove the harness has
teeth: :func:`rank_ids` (the real lexical ranker) and :func:`degraded_rank_ids`
(a relevance-blind one that MUST score strictly worse).
"""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from . import metrics


def rank_ids(query: str, entries: list[dict], k: int) -> list[str]:
    """The real ranker under test: the engine's lexical keyword + id-overlap rank."""
    from clauderizer import analyze

    return [r["id"] for r in analyze.rank_relevant(query, entries, k=k)]


def degraded_rank_ids(query: str, entries: list[dict], k: int) -> list[str]:
    """A relevance-blind ranker (ignores the query) — the regression the harness
    must catch. Deterministic: reverse id order, so it is stable but useless."""
    return [e["id"] for e in sorted(entries, key=lambda e: e["id"], reverse=True)][:k]


def run_ranker(entries: list[dict], probes: Sequence, k: int = 5,
               rank_fn: Callable[[str, list[dict], int], list[str]] = rank_ids) -> dict:
    """Score ``rank_fn`` over the in-memory ``probes``; return aggregate metrics."""
    recs, precs, ndcgs, rrs = [], [], [], []
    abst_hits = abst_total = 0
    con_hits = con_total = 0
    for p in probes:
        ranked = rank_fn(p.query, entries, k)
        if p.ability == "abstention":
            abst_total += 1
            abst_hits += int(metrics.abstention_correct(ranked, k))
            continue
        recs.append(metrics.recall_at_k(ranked, p.relevant_ids, k))
        precs.append(metrics.precision_at_k(ranked, p.relevant_ids, k))
        ndcgs.append(metrics.ndcg_at_k(ranked, p.relevant_ids, k))
        rrs.append(metrics.reciprocal_rank(ranked, p.relevant_ids))
        if p.stale_ids:
            con_total += 1
            con_hits += int(metrics.contradiction(ranked, p.relevant_ids, p.stale_ids))
    return {
        "recall_at_k": metrics.mean(recs),
        "precision_at_k": metrics.mean(precs),
        "ndcg_at_k": metrics.mean(ndcgs),
        "mrr": metrics.mean(rrs),
        "abstention_rate": abst_hits / abst_total if abst_total else 1.0,
        "contradiction_rate": con_hits / con_total if con_total else 0.0,
        "k": k,
        "n_probes": len(list(probes)),
    }


def run_engine_probes(paths, probes: Sequence, k: int = 5) -> dict:
    """Score probes against the real engine surface (``analyze.analyze`` over the
    repo's decision log) — the path the agent actually sees. Used for
    knowledge-updates and abstention abilities that need a seeded repo."""
    from clauderizer import analyze

    recs = []
    abst_hits = abst_total = 0
    con_hits = con_total = 0
    for p in probes:
        ranked = [d["id"] for d in analyze.analyze(paths, p.query, k=k)["decisions"]]
        if p.ability == "abstention":
            abst_total += 1
            abst_hits += int(metrics.abstention_correct(ranked, k))
            continue
        recs.append(metrics.recall_at_k(ranked, p.relevant_ids, k))
        if p.stale_ids:
            con_total += 1
            con_hits += int(metrics.contradiction(ranked, p.relevant_ids, p.stale_ids))
    return {
        "recall_at_k": metrics.mean(recs),
        "abstention_rate": abst_hits / abst_total if abst_total else 1.0,
        "contradiction_rate": con_hits / con_total if con_total else 0.0,
        "n_probes": len(list(probes)),
    }


def measure_context_tokens(paths, config) -> dict:
    """Estimate the token size of what the engine injects: the SessionStart
    digest (with the real tool list) and, when a gameplan is active, the
    cumulative handoff and its project-lessons tail. The baseline the
    context-rot trim phase must shrink without losing accuracy."""
    from clauderizer.rituals import status_bundle, handoff

    try:
        from clauderizer.tools_list import TOOL_NAMES as tools
    except Exception:  # pragma: no cover - tools list is optional context
        tools = None

    bundle = status_bundle.compute(paths, config)
    digest = status_bundle.render_digest(bundle, tools)
    out = {"digest_tokens": metrics.token_estimate(digest)}

    gid = config.active_gameplan
    target = bundle.get("current_phase") or bundle.get("next_phase")
    if gid and target:
        ctx = handoff.assemble(paths, config, gid, target["number"], write=False)
        hmd = ctx["handoff_md"]
        out["handoff_tokens"] = metrics.token_estimate(hmd)
        # The lesson payload is what the trim phase targets. Measure it by line
        # pattern (**N.** and **L-NN.**), robust to the decorative section heading.
        lesson_lines = [ln for ln in hmd.splitlines()
                        if re.match(r"\s*\*\*(?:L-)?\d+\.\*\*", ln)]
        out["lesson_lines"] = len(lesson_lines)
        out["lessons_tokens"] = metrics.token_estimate("\n".join(lesson_lines))
    return out
