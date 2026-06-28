"""Deterministic token-cost accounting for the abstract-index retrieval
experiment (gameplan 2026-06-25-abstract-index-fast-retrieval, Phase 0).

The Phase-3 gain-gate decides KEEP/DISCARD on a COST metric (D2): the mean
payload-token reduction per memory lookup, guarded by answer-accuracy
non-regression and a bounded round-trip count. This module is the deterministic
measurement substrate — no ML, no live LLM, just the engine's own ``len // 4``
token estimate (:func:`metrics.token_estimate`) over the payload each retrieval
strategy injects into the agent's context.

It mirrors the ``tests/benchmarks`` discipline (``harness.rank_ids`` vs
``harness.degraded_rank_ids``): alongside the real mechanism
(:func:`abstract_then_fetch`) it ships two deliberately broken strategies —
:func:`noop_full` (a negative control that injects full bodies and must show ~0%
saving) and :func:`starve` (abstract-only with no fetch: a big saving but a WRONG
answer, which the accuracy guard must reject) — so a self-test can prove the
harness, and the gate, have teeth BEFORE the real feature exists (L-40).

Cost model (pre-registered in ``_experiments/PRE-REGISTRATION.md``):

  baseline  — titles via ``cz_analyze``, then ONE whole-block read to obtain any
              body (there is no addressable getter today), so EVERY surfaced body
              is materialized: payload = all titles + all bodies; round-trips = 2.
  candidate — titles+abstracts via ``cz_analyze``, then one ``cz_get`` per body
              actually needed (f): payload = titles+abstracts + f bodies;
              round-trips = 1 + f. For a single-body lookup (f=1) that is 2 — the
              same as the baseline — so the win is payload, not round-trips.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .metrics import mean, token_estimate

# Pre-registered KEEP threshold (D2): a lookup must shed at least this fraction of
# its baseline payload tokens, on average, with the guards holding. Committed here
# so the verdict is mechanical and cannot be moved post hoc to manufacture a KEEP.
MIN_SAVING = 0.30
# Round-trip guard: a single-body lookup must cost no more memory round-trips than
# the baseline's analyze + bulk-read (2). Needing >1 body-fetch to answer breaches
# it — a signal the abstracts were not informative enough to target the fetch.
MAX_ROUND_TRIPS = 2


@dataclass(frozen=True)
class Lookup:
    """One retrieval episode on the cost fixture.

    ``surfaced`` is the candidate entries the ranker placed in front of the agent
    (each a ``{id, title, body}`` dict); ``answer_ids`` is the subset whose BODY is
    actually required to answer — 1-of-N on the cost fixture, so most surfaced
    bodies are dead weight the baseline pays for and the candidate does not.
    """
    query: str
    surfaced: tuple[dict, ...]
    answer_ids: tuple[str, ...]


AbstractFn = Callable[[str], str]


def head_abstract(body: str, budget: int = 80) -> str:
    """Deterministic Phase-0 abstract: the first ``budget`` chars of the body,
    collapsed to one line and cut on a word boundary. The production rule is
    decided in O-01; this placeholder only has to be small to demonstrate that the
    harness discriminates a real compression from a no-op."""
    one_line = " ".join(body.split())
    if len(one_line) <= budget:
        return one_line
    return one_line[:budget].rsplit(" ", 1)[0] + "…"


def full_abstract(body: str) -> str:
    """Negative-control 'abstract' = the full body (no compression at all)."""
    return body


def measure_baseline(lookup: Lookup) -> dict:
    """Status quo: with no addressable getter the agent reads the whole block to
    obtain any one body, materializing EVERY surfaced body. Payload = all titles +
    all bodies; 2 round-trips (analyze + one bulk read); it always answers."""
    titles = "\n".join(f"{e['id']} {e['title']}" for e in lookup.surfaced)
    bodies = "\n".join(e["body"] for e in lookup.surfaced)
    return {"payload_tokens": token_estimate(titles + "\n" + bodies),
            "round_trips": 2, "answered": True}


def measure_candidate(lookup: Lookup, abstract_fn: AbstractFn,
                      fetch_ids: Sequence[str]) -> dict:
    """Abstract + addressable fetch: every candidate surfaces ``title + abstract``;
    only ``fetch_ids`` bodies are pulled (one ``cz_get`` each). A body counts as
    present if it was fetched OR its abstract is the full body (the negative
    control). Round-trips = 1 (analyze) + one per fetched body."""
    ids = {e["id"] for e in lookup.surfaced}
    fetch = set(fetch_ids) & ids
    surfaced = "\n".join(f"{e['id']} {e['title']} {abstract_fn(e['body'])}"
                         for e in lookup.surfaced)
    fetched_bodies = "\n".join(e["body"] for e in lookup.surfaced if e["id"] in fetch)
    present = fetch | {e["id"] for e in lookup.surfaced
                       if abstract_fn(e["body"]) == e["body"]}
    payload = surfaced + ("\n" + fetched_bodies if fetched_bodies else "")
    return {"payload_tokens": token_estimate(payload),
            "round_trips": 1 + len(fetch),
            "answered": set(lookup.answer_ids) <= present}


# --- strategies: one real mechanism + two deliberately broken controls --------

def abstract_then_fetch(lookup: Lookup) -> dict:
    """The real mechanism: compact abstracts up front, fetch only the body needed."""
    return measure_candidate(lookup, head_abstract, lookup.answer_ids)


def noop_full(lookup: Lookup) -> dict:
    """Negative control: the 'abstract' IS the full body and nothing extra is
    fetched — identical content to the baseline, so the measured saving must be
    ~0. Proves the harness does not report a saving where none exists."""
    return measure_candidate(lookup, full_abstract, fetch_ids=())


def starve(lookup: Lookup) -> dict:
    """Accuracy trap: tiny abstracts and NO fetch — a large token saving, but the
    answer body is absent so ``answered`` is False. Proves the accuracy guard
    rejects a token-cheap-but-wrong strategy (the guard has teeth)."""
    return measure_candidate(lookup, head_abstract, fetch_ids=())


Strategy = Callable[[Lookup], dict]


def evaluate(lookups: Sequence[Lookup], candidate: Strategy) -> dict:
    """Aggregate ``candidate`` against the baseline over ``lookups`` — the numbers
    the Phase-3 gain-gate reads."""
    savings, base_rt, cand_rt, base_acc, cand_acc = [], [], [], [], []
    for lk in lookups:
        b = measure_baseline(lk)
        c = candidate(lk)
        bt = b["payload_tokens"]
        savings.append((bt - c["payload_tokens"]) / bt if bt else 0.0)
        base_rt.append(b["round_trips"])
        cand_rt.append(c["round_trips"])
        base_acc.append(1.0 if b["answered"] else 0.0)
        cand_acc.append(1.0 if c["answered"] else 0.0)
    return {
        "mean_saving": mean(savings),
        "baseline_accuracy": mean(base_acc),
        "candidate_accuracy": mean(cand_acc),
        "mean_round_trips_baseline": mean(base_rt),
        "mean_round_trips_candidate": mean(cand_rt),
        "max_round_trips_candidate": max(cand_rt) if cand_rt else 0,
        "n": len(lookups),
    }


def verdict(result: dict, min_saving: float = MIN_SAVING,
            max_round_trips: int = MAX_ROUND_TRIPS) -> str:
    """Apply D2's pre-registered rule. KEEP iff a meaningful payload saving AND no
    accuracy regression AND bounded round-trips; else DISCARD (a valid, recorded
    outcome — L-32)."""
    saving_ok = result["mean_saving"] >= min_saving
    accuracy_ok = result["candidate_accuracy"] >= result["baseline_accuracy"] - 1e-9
    roundtrips_ok = result["max_round_trips_candidate"] <= max_round_trips
    return "KEEP" if (saving_ok and accuracy_ok and roundtrips_ok) else "DISCARD"


# --- canonical synthetic cost fixture (1-of-N, long bodies) -------------------
# Each lookup surfaces N entries on DISTINCT topics, but the query needs exactly
# ONE body — so the baseline's "materialize every surfaced body" is mostly dead
# weight, which is the headroom the abstract+fetch mechanism converts to a saving.
# Bodies run to the length a real DECISIONS entry does (the dead weight); abstracts
# are short. This fixture is SYNTHETIC and exists only to prove the harness
# discriminates; Phase 3 swaps in the REAL corpus + the real abstract index.

_TAIL = (" This entry records the full rationale, the alternatives weighed, the "
         "constraints in play, the consequences for downstream subsystems, and the "
         "follow-up obligations, at the length a real decision log entry runs to so "
         "that the body genuinely dwarfs an 80-character abstract.")


def _e(eid: str, title: str, lead: str) -> dict:
    return {"id": eid, "title": title, "body": lead + _TAIL}


_SHELF: tuple[dict, ...] = (
    _e("D-201", "Postgres billing ledger storage",
       "Persist the invoice ledger in Postgres for durable transactional writes."),
    _e("D-202", "React frontend component hooks",
       "Render frontend components with functional hooks and local state."),
    _e("D-203", "Redis cache eviction policy",
       "Evict cache entries by a least-recently-used expiry window."),
    _e("D-204", "Kafka event streaming topics",
       "Stream domain events over partitioned append-only Kafka topics."),
    _e("D-205", "S3 object storage lifecycle",
       "Archive cold objects into tiered S3 retention buckets."),
)

COST_LOOKUPS: tuple[Lookup, ...] = (
    Lookup(query="how is the billing ledger stored",
           surfaced=_SHELF, answer_ids=("D-201",)),
    Lookup(query="how do we render frontend components",
           surfaced=_SHELF, answer_ids=("D-202",)),
    Lookup(query="what is the cache eviction policy",
           surfaced=_SHELF, answer_ids=("D-203",)),
)
