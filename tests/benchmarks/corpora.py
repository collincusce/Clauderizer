"""Fixture corpora for the memory-eval harness, organized by the LongMemEval
five-ability taxonomy (D: eval methodology).

  extraction         — a recorded fact is retrieved by a relevant query
  multi_session      — facts on different topics do not bleed into each other
  temporal           — dated facts (exercised by the bitemporal phase)
  knowledge_updates  — a superseded fact must not outrank its replacement
  abstention         — an absent topic must surface nothing

The ranker corpus is in-memory (entries shaped for ``analyze.rank_relevant``) so
the ranking metrics need no repo. The ``seed_*`` helpers build into a real temp
repo for engine-level abilities (supersession via decisions, DAG validity via
entities).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Probe:
    """One scored question. ``relevant_ids`` is the answer key; empty means an
    abstention probe (the correct answer is "nothing relevant"). ``stale_ids``
    are ids that would be WRONG to surface as current (knowledge-updates)."""
    ability: str
    query: str
    relevant_ids: tuple[str, ...] = ()
    stale_ids: tuple[str, ...] = ()
    note: str = ""


# --- in-memory ranker corpus (entries shaped as analyze.rank_relevant wants) ---
# Deliberately distinct, non-overlapping topics: a correct lexical ranker
# separates them cleanly, so recall/nDCG/MRR have a real ceiling to hit.
RANKER_ENTRIES: list[dict] = [
    {"id": "D-101", "title": "Postgres billing ledger storage",
     "body": "durable transactional invoice ledger persistence"},
    {"id": "D-102", "title": "React frontend component hooks",
     "body": "browser rendering functional components local state"},
    {"id": "D-103", "title": "Redis cache eviction policy",
     "body": "in-memory expiry least-recently-used cache entries"},
    {"id": "D-104", "title": "Kafka event streaming topics",
     "body": "partitioned append-only event log downstream consumers"},
    {"id": "D-105", "title": "S3 object storage lifecycle",
     "body": "bucket archival cold object retention tiers"},
]

RANKER_PROBES: list[Probe] = [
    Probe("extraction", "moving the billing ledger storage onto a new database",
          ("D-101",)),
    Probe("extraction", "rendering frontend components with hooks", ("D-102",)),
    Probe("extraction", "cache entry expiry and eviction", ("D-103",)),
    Probe("multi_session", "event streaming partitioned log consumers", ("D-104",)),
    Probe("multi_session", "object storage archival retention tiers", ("D-105",)),
    # No token overlap with any entry -> a correct ranker returns nothing.
    Probe("abstention", "photosynthesis chloroplast thylakoid membrane", ()),
]


def seed_decisions(paths) -> list[Probe]:
    """Seed a supersession pair plus a distractor into the repo's DECISIONS log;
    return the knowledge-updates and abstention probes that score against it.

    The old decision is later superseded by the new one. At the flat-status
    baseline the ranker cannot tell which is current (they tie on query overlap
    and id order surfaces the older first), so the knowledge-updates probe
    exhibits a contradiction that Phase 4 must remove.
    """
    from clauderizer import mutations as M

    old = M.add_decision(
        paths, title="Use REST for the public API",
        context="public API transport choice",
        decision="expose a REST JSON API",
        consequences="simple clients")["id"]
    new = M.add_decision(
        paths, title="Switch the public API to GraphQL",
        context="public API transport choice; the REST approach is superseded",
        decision="expose a GraphQL API",
        consequences="flexible typed queries", supersedes=old)["id"]
    M.add_decision(
        paths, title="Adopt Stripe for payment processing",
        context="payment vendor selection",
        decision="integrate Stripe Billing",
        consequences="per-transaction fees")
    return [
        Probe("knowledge_updates",
              "what is the current public API transport choice",
              relevant_ids=(new,), stale_ids=(old,),
              note="GraphQL (new) must not be outranked by the superseded REST (old)"),
        Probe("abstention",
              "tardigrade cryptobiosis desiccation tolerance",
              note="never recorded -> the engine must surface nothing"),
    ]


def seed_valid_graph(paths) -> list[str]:
    """Seed a small valid DAG (core <- mid <- top). Returns the entity ids.

    The DAG-integrity phase injects dangling/cyclic edges against this baseline;
    here it just establishes a clean graph the validator must pass without
    false positives.
    """
    from clauderizer import mutations as M

    M.upsert_entity(paths, id="subsys.core", type="subsystem",
                    version="1.0.0", status="active")
    M.upsert_entity(paths, id="subsys.mid", type="subsystem",
                    version="1.0.0", status="active", depends_on=["subsys.core"])
    M.upsert_entity(paths, id="subsys.top", type="subsystem",
                    version="1.0.0", status="active", depends_on=["subsys.mid"])
    return ["subsys.core", "subsys.mid", "subsys.top"]
