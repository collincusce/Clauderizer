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


# --- gap-finder: one-hop graph adjacency (D-018) ---------------------------------


def _seed_chain(paths):
    """core <- mid <- top: mid's dependency is core, mid's dependent is top."""
    M.upsert_entity(paths, id="subsys.core", type="subsystem", version="1.0.0",
                    status="active")
    M.upsert_entity(paths, id="subsys.mid", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.core"])
    M.upsert_entity(paths, id="subsys.top", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.mid"])


def test_adjacent_surfaces_one_hop_neighbors(temp_repo):
    """An entity named in the text surfaces its graph neighbors, never itself."""
    paths, _ = _ctx(temp_repo)
    _seed_chain(paths)
    res = analyze.analyze(paths, "a change to subsys.mid behavior")
    adj = {a["id"] for a in res["adjacent"]}
    assert "subsys.core" in adj   # the seed's dependency
    assert "subsys.top" in adj    # the seed's dependent
    assert "subsys.mid" not in adj  # the seed itself is never a gap


def test_adjacent_excludes_already_named(temp_repo):
    """An entity the text already names is connected, not a gap."""
    paths, _ = _ctx(temp_repo)
    _seed_chain(paths)
    res = analyze.analyze(paths, "change subsys.mid and subsys.core together")
    adj = {a["id"] for a in res["adjacent"]}
    assert "subsys.core" not in adj  # named -> already connected
    assert "subsys.top" in adj        # still an unnamed neighbor of mid


def test_adjacent_empty_when_nothing_relates(temp_repo):
    """No named entity and no decision bridge -> an honest empty set, not a failure."""
    paths, _ = _ctx(temp_repo)
    res = analyze.analyze(paths, "lorem ipsum dolor sit amet consectetur")
    assert res["adjacent"] == []


def test_adjacent_bridges_via_introduced_by(temp_repo):
    """A keyword-surfaced decision bridges (via introduced_by) to the entity it
    created, whose unnamed neighbor then surfaces as a gap."""
    paths, _ = _ctx(temp_repo)
    d = M.add_decision(paths, title="Adopt the widget pipeline",
                       context="widget throughput budget",
                       decision="build a widget pipeline",
                       consequences="more widgets")["id"]
    M.upsert_entity(paths, id="subsys.widget", type="subsystem", version="1.0.0",
                    status="active", fields={"introduced_by": d})
    M.upsert_entity(paths, id="subsys.widget-store", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.widget"])
    res = analyze.analyze(paths, "revisit the widget pipeline throughput")
    assert d in [x["id"] for x in res["decisions"]]      # surfaced by keyword
    adj = {a["id"] for a in res["adjacent"]}
    assert "subsys.widget-store" in adj  # reached through the introduced_by bridge
    assert "subsys.widget" not in adj    # the bridged seed itself is not a gap


def test_cz_analyze_op_surfaces_adjacent(temp_repo):
    """The cz_analyze op — shared by the MCP tool and `clauderize ops` — carries
    the adjacent gap set and reports its count in the summary."""
    paths, _ = _ctx(temp_repo)
    _seed_chain(paths)
    from clauderizer import ops
    with _chdir(temp_repo):
        res = ops.cz_analyze("a change to subsys.mid behavior")
    assert res["ok"] and "adjacent" in res
    adj = {a["id"] for a in res["adjacent"]}
    assert "subsys.core" in adj and "subsys.top" in adj
    assert "adjacent" in res["summary"]


def test_adjacent_matches_entity_id_ending_a_sentence(temp_repo):
    """An entity id that ends a sentence (trailing '.') is still a mention — the
    boundary lookahead must not treat the period as an id continuation."""
    paths, _ = _ctx(temp_repo)
    _seed_chain(paths)  # subsys.core <- subsys.mid <- subsys.top
    res = analyze.analyze(paths, "we are changing subsys.mid.")
    adj = {a["id"] for a in res["adjacent"]}
    assert "subsys.core" in adj and "subsys.top" in adj  # subsys.mid was seeded despite the '.'


# --- abstract surfacing on cz_analyze (Phase 2) -----------------------------------


def test_analyze_hits_carry_abstract_equal_to_the_index(temp_repo):
    """Each ranked hit gains a one-line `abstract`, and it is exactly the abstract
    index's abstract for that id — the shortcut (cap-the-title, no index build on
    the hot hook path) must not drift from the canonical record."""
    from clauderizer.graph import abstract_index as A

    paths, _ = _ctx(temp_repo)
    M.add_decision(paths, title="Use Postgres for the billing ledger",
                   context="durable transactional storage", decision="adopt postgresql",
                   consequences="operational overhead")
    res = analyze.analyze(paths, "billing ledger storage on postgres")
    assert res["decisions"], "expected the postgres decision to surface"
    built = A.build(paths)["entries"]
    for hit in res["decisions"]:
        assert hit["abstract"] == built[hit["id"]]["abstract"]
        assert "\n" not in hit["abstract"]


def test_cz_analyze_op_hits_include_abstract(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.add_decision(paths, title="Use Postgres for the billing ledger",
                   context="durable transactional storage", decision="adopt postgresql",
                   consequences="operational overhead")
    from clauderizer import ops
    with _chdir(temp_repo):
        res = ops.cz_analyze("billing ledger storage on postgres")
    assert res["ok"] and res["decisions"]
    assert all("abstract" in d for d in res["decisions"])


# --- cz_get / get_entry: addressable single-entry fetch (Phase 2) -----------------

_DECISIONS = ("# Decisions\n\n## Decisions\n\n"
              "### D-001 — Use Postgres for the billing ledger\n\n"
              "**Status**: active\n\n**Context**: durable writes.\n")
_INVARIANTS = ("# Invariants\n\n## Invariants\n\n"
               "### INVARIANT-01 — Markdown is canonical\n\nMarkdown always wins.\n")
_HARDENING = ("# Hardening\n\n## Risks\n\n### H-01 — A concurrency race\n\n"
              "- **Severity**: high\n- **Status**: resolved (2026-01-01)\n"
              "- **Impact**: data loss under contention.\n")
_LESSONS = ("# Lessons\n\n## Lessons\n\n"
            "**L-01.** Measure before shipping. A discard is a success. *(from x)*\n")


def _seed_corpora(tmp_path):
    (tmp_path / "docs").mkdir(exist_ok=True)
    paths = P.resolve(tmp_path)
    paths.doc("DECISIONS").write_text(_DECISIONS, encoding="utf-8")
    paths.doc("INVARIANTS").write_text(_INVARIANTS, encoding="utf-8")
    paths.doc("HARDENING").write_text(_HARDENING, encoding="utf-8")
    paths.doc("LESSONS").write_text(_LESSONS, encoding="utf-8")
    return paths


def test_get_entry_returns_body_for_each_of_the_four_corpora(tmp_path):
    paths = _seed_corpora(tmp_path)
    d = analyze.get_entry(paths, "D-001")
    assert d and d["kind"] == "decision" and "durable writes" in d["body"]
    assert d["anchor"].startswith("docs/DECISIONS.md:")
    inv = analyze.get_entry(paths, "INVARIANT-01")
    assert inv and inv["kind"] == "invariant" and "Markdown always wins" in inv["body"]
    h = analyze.get_entry(paths, "H-01")
    assert h and h["kind"] == "finding" and "data loss" in h["body"]
    assert h["status"] == "resolved"   # index status parser handles the `- **Status**` form
    lsn = analyze.get_entry(paths, "L-01")
    assert lsn and lsn["kind"] == "lesson"
    assert lsn["title"] == "Measure before shipping."   # first sentence is the title
    assert "discard is a success" in lsn["body"]


def test_get_entry_unknown_id_returns_none(tmp_path):
    paths = _seed_corpora(tmp_path)
    assert analyze.get_entry(paths, "D-999") is None


def test_get_entry_kind_hint_mismatch_is_a_miss(tmp_path):
    paths = _seed_corpora(tmp_path)
    assert analyze.get_entry(paths, "D-001", kind="lesson") is None
    assert analyze.get_entry(paths, "D-001", kind="decision")["id"] == "D-001"


def test_cz_get_op_fetches_from_each_corpus_and_is_read_only(temp_repo):
    paths = P.resolve(temp_repo)
    # the fixture ships DECISIONS (D-001) + INVARIANTS (INVARIANT-01); add the rest
    paths.doc("HARDENING").write_text(_HARDENING, encoding="utf-8")
    paths.doc("LESSONS").write_text(_LESSONS, encoding="utf-8")
    from clauderizer import ops
    with _chdir(temp_repo):
        for eid, kind in [("D-001", "decision"), ("INVARIANT-01", "invariant"),
                          ("H-01", "finding"), ("L-01", "lesson")]:
            res = ops.cz_get(eid)
            assert res["ok"] and res["id"] == eid and res["kind"] == kind
            assert res["body"], f"{eid} returned an empty body"
        miss = ops.cz_get("D-404")
        assert miss["ok"] is False and "no corpus entry" in miss["error"]
    assert ops.REGISTRY["cz_get"].writes is False
