"""The analyze gate (Phase 2 of spec-kit-discipline-gates, D-016): surface the
relevant existing invariants/decisions for the agent to judge contradiction —
judgment-based, read-only, relevance by keyword + entity-id overlap (no embeddings).
"""

import os
from contextlib import contextmanager

from clauderizer import analyze
from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def test_rank_relevant_scores_overlap_and_id_boost():
    entries = [
        {"id": "D-010", "title": "Postgres billing ledger", "body": "durable invoice storage"},
        {"id": "D-011", "title": "React frontend hooks", "body": "component rendering model"},
    ]
    ranked = analyze.rank_relevant("moving the billing ledger storage", entries)
    assert [r["id"] for r in ranked][:1] == ["D-010"]  # the overlapping entry ranks first
    # an explicit id mention boosts even with zero word overlap
    ranked2 = analyze.rank_relevant("revisit D-011 about something", entries)
    assert ranked2 and ranked2[0]["id"] == "D-011"


def test_analyze_surfaces_relevant_not_irrelevant(temp_repo):
    paths, _ = _ctx(temp_repo)
    d_pg = M.add_decision(paths, title="Use Postgres for the billing ledger",
                          context="durable transactional storage for invoices",
                          decision="adopt postgresql", consequences="operational overhead")["id"]
    d_react = M.add_decision(paths, title="Frontend uses React with hooks",
                             context="component rendering model",
                             decision="react functional components",
                             consequences="hooks everywhere")["id"]
    res = analyze.analyze(paths, "moving the billing ledger storage onto postgres")
    ids = [d["id"] for d in res["decisions"]]
    assert d_pg in ids       # the billing/postgres decision surfaced
    assert d_react not in ids  # the unrelated frontend decision did not


def test_add_decision_enriches_with_related(temp_repo):
    paths, _ = _ctx(temp_repo)
    d1 = M.add_decision(paths, title="Use Postgres for the billing ledger",
                        context="durable transactional storage", decision="adopt postgresql",
                        consequences="operational overhead")["id"]
    r2 = M.add_decision(paths, title="Shard the billing ledger by tenant",
                        context="billing ledger storage scaling on postgres",
                        decision="range shard the ledger", consequences="rebalancing")
    assert "related" in r2
    assert d1 in [x["id"] for x in r2["related"]]  # the prior overlapping decision surfaced


def test_cz_analyze_op_returns_candidates_and_prompt(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.add_decision(paths, title="Use Postgres for the billing ledger",
                   context="durable transactional storage", decision="adopt postgresql",
                   consequences="operational overhead")
    from clauderizer import ops
    with _chdir(temp_repo):
        res = ops.cz_analyze("billing ledger storage on postgres")
    assert res["ok"] and "prompt" in res
    assert any("Postgres" in d["title"] for d in res["decisions"])


def test_analyze_surfaces_short_identifier_overlap(temp_repo):
    """A distinctive short id (s3) is kept as a token, so it can signal overlap."""
    paths, _ = _ctx(temp_repo)
    d = M.add_decision(paths, title="Drop S3 for the object cache", context="latency",
                       decision="use local disk", consequences="ops")["id"]
    # the only meaningful overlap with the query is the short identifier "s3"
    res = analyze.analyze(paths, "revisit the s3 bucket policy")
    assert d in [x["id"] for x in res["decisions"]]
