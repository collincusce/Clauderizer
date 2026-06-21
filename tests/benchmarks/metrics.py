"""Deterministic, stdlib-only metrics for the memory-eval harness.

No ML, no embeddings, no third-party deps (INVARIANT: no-ML core; D: trim-first).
Every function is a pure, deterministic computation over ranked id lists or text
— the repeatable substrate each feature phase scores against.

The token estimate follows the engine's own convention (``len // 4``) so harness
numbers line up with the SessionStart digest's "~N tok" figure
(``status_bundle.compute``: ``handoff_est_tokens = len(handoff_md) // 4``).
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def token_estimate(text: str) -> int:
    """Approximate token count, matching the engine's ``len // 4`` convention."""
    return len(text) // 4


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Fraction of the relevant ids present in the top-``k`` of ``ranked_ids``.

    Returns 1.0 when there are no relevant ids (vacuously complete): an
    abstention probe, where the correct answer is "nothing relevant", is scored
    by :func:`abstention_correct`, not penalized as a recall miss here.
    """
    rel = set(relevant_ids)
    if not rel:
        return 1.0
    top = list(ranked_ids)[:k]
    return sum(1 for r in rel if r in top) / len(rel)


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Fraction of the top-``k`` that are relevant. 0.0 when there are no results."""
    rel = set(relevant_ids)
    top = list(ranked_ids)[:k]
    if not top:
        return 0.0
    return sum(1 for r in top if r in rel) / len(top)


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def dcg_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    rel = set(relevant_ids)
    dcg = 0.0
    for i, rid in enumerate(list(ranked_ids)[:k]):
        if rid in rel:
            dcg += 1.0 / math.log2(i + 2)  # i=0 -> rank 1 -> log2(2) == 1
    return dcg


def ndcg_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Normalized DCG with binary relevance (ideal = all relevant ranked first)."""
    rel = set(relevant_ids)
    if not rel:
        return 1.0
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel), k)))
    if ideal == 0:
        return 0.0
    return dcg_at_k(ranked_ids, relevant_ids, k) / ideal


def reciprocal_rank(ranked_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    """1/rank of the first relevant id (1-based); 0.0 if none are present."""
    rel = set(relevant_ids)
    for i, rid in enumerate(ranked_ids):
        if rid in rel:
            return 1.0 / (i + 1)
    return 0.0


def abstention_correct(ranked_ids: Sequence[str], k: int) -> bool:
    """For an absent-info probe, correct behavior is surfacing nothing in top-``k``.

    The lexical ranker returns only positive-overlap entries, so a genuinely
    absent topic yields an empty ranking — the deterministic "I don't know".
    """
    return len(list(ranked_ids)[:k]) == 0


def contradiction(ranked_ids: Sequence[str], relevant_ids: Iterable[str],
                  stale_ids: Iterable[str]) -> bool:
    """True if a stale (superseded) id is surfaced at or above the current one.

    Models the stale-fact failure mode: the memory hands the agent an outdated
    decision as if current. Used by the knowledge-updates ability; the
    flat-status baseline exhibits this, and Phase 4 (supersession back-refs) must
    drive the rate to zero.
    """
    rel = set(relevant_ids)
    stale = set(stale_ids)
    first_rel = next((i for i, r in enumerate(ranked_ids) if r in rel), None)
    first_stale = next((i for i, r in enumerate(ranked_ids) if r in stale), None)
    if first_stale is None:
        return False  # no stale surfaced -> no contradiction
    if first_rel is None:
        return True  # only the stale one surfaced
    return first_stale <= first_rel


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


# --- DAG-validity primitives (Phase 2 builds engine surfacing on these) -------

def dangling_edges(adjacency: dict[str, list[str]],
                   known_ids: Iterable[str]) -> list[tuple[str, str]]:
    """``depends_on`` edges whose target is not a known entity. ``adjacency`` maps
    ``{id: [target ids]}``; returns ``(src, missing_target)`` pairs, sorted."""
    known = set(known_ids)
    out = [(src, tgt) for src, deps in adjacency.items()
           for tgt in deps if tgt not in known]
    return sorted(out)


def has_cycle(adjacency: dict[str, list[str]]) -> bool:
    """True if the directed graph contains a cycle (deterministic 3-color DFS).

    Edges to unknown ids (dangling) are ignored here — that is a separate failure
    mode reported by :func:`dangling_edges`, not a cycle.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adjacency}

    def visit(n: str) -> bool:
        color[n] = GREY
        for m in adjacency.get(n, []):
            if m not in color:
                continue  # dangling, not a cycle
            if color[m] == GREY:
                return True
            if color[m] == WHITE and visit(m):
                return True
        color[n] = BLACK
        return False

    return any(color[n] == WHITE and visit(n) for n in list(adjacency))
