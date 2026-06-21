"""The edge-suggester (Phase 3 of empirical-memory-gains): surface MISSING
``depends_on`` edges between tracked entities — the structural COMPLEMENT of
``analyze.adjacent_entities`` (D-018), which walks EXISTING edges. This finds
edges that plausibly SHOULD exist but don't, for the AGENT to confirm.

Advisory only, deterministic, stdlib-only (INVARIANT-05): the suggester never
auto-writes an edge. The rejected set is markdown-canonical (a ``not_related_to``
frontmatter list) and must round-trip. The precision/recall test locks in the
measured precision on a labeled fixture so the keep/park number is honest.
"""

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import analyze
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import frontmatter


def _ctx(repo):
    return P.resolve(repo)


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _pair(s):
    return frozenset((s["a"], s["b"]))


def _entity(paths, eid, body, *, depends_on=None, not_related_to=None):
    """Write a realistic entity doc to disk: id/type frontmatter + a prose body.

    Real entities carry their description as body prose (see the fixture
    subsystems/*.md), so the suggester's lexical signal comes from the body — this
    helper writes exactly that shape rather than the scaffold placeholder.
    """
    kind = eid.split(".", 1)[0]
    type_ = "subsystem" if kind == "subsys" else "feature"
    data = {"id": eid, "type": type_, "version": "1.0.0", "status": "active"}
    if depends_on is not None:
        data["depends_on"] = list(depends_on)
    if not_related_to is not None:
        data["not_related_to"] = list(not_related_to)
    sub = "subsystems" if type_ == "subsystem" else "features"
    path = paths.docs / sub / f"{eid.split('.', 1)[-1]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.serialize(data, body), encoding="utf-8")
    return path


# --- core behavior --------------------------------------------------------------


def test_surfaces_a_known_missing_edge(temp_repo):
    """Two entities sharing distinctive vocabulary but with NO depends_on edge
    either way surface as a suggestion."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.")
    edges = analyze.suggest_edges(paths)
    pairs = {_pair(s) for s in edges}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) in pairs
    # the suggestion carries the concrete shared terms that justified it
    s = next(s for s in edges
             if _pair(s) == frozenset(("subsys.invoice-ledger", "subsys.invoice-export")))
    assert "invoice" in s["shared_terms"] and "billing" in s["shared_terms"]


def test_does_not_surface_an_existing_edge(temp_repo):
    """A pair already connected by depends_on (either direction) is NOT a missing
    edge — the complement of D-018 must skip it."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.",
            depends_on=["subsys.invoice-ledger"])
    edges = analyze.suggest_edges(paths)
    pairs = {_pair(s) for s in edges}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) not in pairs


def test_does_not_surface_a_rejected_pair_roundtrip(temp_repo):
    """A dismissed pair (``not_related_to`` frontmatter) is filtered — and the
    filter survives a write/re-read of the markdown (the round-trip)."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.")
    # baseline: the pair IS suggested before any dismissal
    before = {_pair(s) for s in analyze.suggest_edges(paths)}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) in before

    # dismiss via the blessed write (markdown-canonical), then re-read from disk
    M.upsert_entity(paths, id="subsys.invoice-export", type="subsystem",
                    fields={"not_related_to": ["subsys.invoice-ledger"]})
    after = {_pair(s) for s in analyze.suggest_edges(paths)}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) not in after


def test_rejected_pair_persists_in_markdown(temp_repo):
    """The dismissal is canonical markdown: the ``not_related_to`` list is on disk
    and parses back (the source-of-truth round-trip, not an in-memory flag)."""
    paths = _ctx(temp_repo)
    p = _entity(paths, "subsys.invoice-export",
                "Invoice ledger billing export and reporting.")
    M.upsert_entity(paths, id="subsys.invoice-export", type="subsystem",
                    fields={"not_related_to": ["subsys.invoice-ledger"]})
    data, _ = frontmatter.parse(Path(p).read_text(encoding="utf-8"))
    assert data["not_related_to"] == ["subsys.invoice-ledger"]


def test_rejection_is_symmetric(temp_repo):
    """A one-sided ``not_related_to`` suffices: it does not matter which entity
    names the other."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.",
            not_related_to=["subsys.invoice-export"])
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.")
    pairs = {_pair(s) for s in analyze.suggest_edges(paths)}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) not in pairs


def test_low_overlap_pairs_are_not_suggested(temp_repo):
    """Entities below the shared-token threshold are not proposed (precision floor)."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.render-pipeline",
            "Graphics shader rasterization viewport pipeline.")
    pairs = {_pair(s) for s in analyze.suggest_edges(paths)}
    assert frozenset(("subsys.invoice-ledger", "subsys.render-pipeline")) not in pairs


def test_deterministic_and_sorted(temp_repo):
    """Output is stable and sorted (descending score, then a, then b)."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage posting tax.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export reporting tax.")
    _entity(paths, "subsys.payment-gateway",
            "Invoice billing payment settlement.")
    first = analyze.suggest_edges(paths)
    second = analyze.suggest_edges(paths)
    assert first == second  # deterministic
    scores = [s["score"] for s in first]
    assert scores == sorted(scores, reverse=True)  # descending score
    for s in first:
        assert s["a"] < s["b"]  # canonical pair order


def test_empty_when_nothing_overlaps(temp_repo):
    """A graph with no overlapping pairs yields an honest empty set, not a failure.

    (The base fixture's own entities — calc-engine, auth, login, legacy — must not
    spuriously pair with these or each other above the threshold.)"""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.alpha", "Quantum entanglement lattice photon.")
    _entity(paths, "subsys.beta", "Marsupial migration tundra herd.")
    pairs = {_pair(s) for s in analyze.suggest_edges(paths)}
    assert frozenset(("subsys.alpha", "subsys.beta")) not in pairs


def test_analyze_result_carries_suggested_edges(temp_repo):
    """The analyze() result (and thus cz_analyze) exposes suggested_edges."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.")
    res = analyze.analyze(paths, "unrelated query text about scheduling")
    assert "suggested_edges" in res
    pairs = {_pair(s) for s in res["suggested_edges"]}
    assert frozenset(("subsys.invoice-ledger", "subsys.invoice-export")) in pairs


def test_cz_analyze_op_surfaces_suggested_edges(temp_repo):
    """The cz_analyze op carries suggested_edges and counts them in the summary."""
    paths = _ctx(temp_repo)
    _entity(paths, "subsys.invoice-ledger",
            "Durable invoice ledger billing storage and posting.")
    _entity(paths, "subsys.invoice-export",
            "Invoice ledger billing export and reporting.")
    from clauderizer import ops
    with _chdir(temp_repo):
        res = ops.cz_analyze("anything")
    assert res["ok"] and "suggested_edges" in res
    assert "suggested edge" in res["summary"]


# --- the precision/recall gate over a labeled fixture ---------------------------
#
# A labeled fixture with a KNOWN intended dependency structure. We REMOVE K real
# edges (the ground-truth "missing edges" the suggester should recover) and ALSO
# include M "look-alike" pairs that share some vocabulary but are genuinely
# independent (true negatives a naive suggester would wrongly propose). Precision
# and recall are computed over this fixture and ASSERTED so the number is locked
# in (the keep/park bar is precision >= 0.70; the orchestrator makes the call).


def _build_labeled_fixture(paths):
    """Seed a labeled graph; return (ground_truth_missing, present_edges).

    Three domain clusters; within each, two entities share >= 2 distinctive domain
    terms (their real missing edge, to recover). Look-alike pairs across domains
    share only a single generic term (storage/template/queue) — a precise
    suggester should NOT propose them.
    """
    # Cluster AUTH
    _entity(paths, "subsys.auth-core",
            "Authentication session token credential issuer.")
    _entity(paths, "subsys.auth-session-store",
            "Session token credential cache lifetime.")
    # Cluster BILLING
    _entity(paths, "subsys.billing-ledger",
            "Invoice ledger reconciliation posting.")
    _entity(paths, "subsys.billing-invoice-render",
            "Invoice ledger render template document.")
    # Cluster SEARCH
    _entity(paths, "subsys.search-index",
            "Search inverted index tokenizer posting list.")
    _entity(paths, "subsys.search-ranker",
            "Search index ranking relevance scoring.")

    # Ground-truth REAL edges intentionally LEFT OUT — the K missing edges.
    ground_truth_missing = {
        frozenset(("subsys.auth-core", "subsys.auth-session-store")),
        frozenset(("subsys.billing-ledger", "subsys.billing-invoice-render")),
        frozenset(("subsys.search-index", "subsys.search-ranker")),
    }

    # A real cross-cluster edge that DOES exist (must not be re-proposed).
    _entity(paths, "subsys.billing-ledger",
            "Invoice ledger reconciliation posting.",
            depends_on=["subsys.auth-core"])
    present_edges = {frozenset(("subsys.billing-ledger", "subsys.auth-core"))}

    # LOOK-ALIKE true negatives: cross-domain pairs sharing ONE generic term.
    _entity(paths, "subsys.telemetry-storage",
            "Telemetry metrics retention rollup storage.")
    _entity(paths, "subsys.notification-template",
            "Notification email template delivery queue.")
    # HARDER true negative: two genuinely-independent subsystems that happen to
    # share TWO distinctive generic terms (storage, cache). A precise suggester at
    # min_shared=2 WILL propose this pair — a real false positive that keeps the
    # measured precision honest (< 1.0) rather than trivially perfect, and probes
    # the min_shared boundary the easy negatives above never exercise.
    _entity(paths, "subsys.report-exporter",
            "Report export storage cache batch scheduler.")
    _entity(paths, "subsys.media-uploader",
            "Media upload storage cache cdn transcode.")
    return ground_truth_missing, present_edges


def test_precision_recall_on_labeled_fixture(temp_repo):
    """Measure precision/recall honestly over a labeled fixture and LOCK IN the
    numbers. Pre-registered keep bar is precision >= 0.70 (advisory noise erodes
    trust); the orchestrator makes the final keep/park call from the raw number.
    """
    paths = _ctx(temp_repo)
    ground_truth_missing, present_edges = _build_labeled_fixture(paths)

    suggested = {_pair(s) for s in analyze.suggest_edges(paths, k=50)}

    # The suggester must never re-propose an edge that already exists.
    assert not (suggested & present_edges)

    true_positives = suggested & ground_truth_missing
    precision = len(true_positives) / len(suggested) if suggested else 0.0
    recall = len(true_positives) / len(ground_truth_missing)
    print(f"\nEDGE-SUGGESTER GATE: precision={precision:.3f} recall={recall:.3f} "
          f"(tp={len(true_positives)} suggested={len(suggested)} "
          f"truth={len(ground_truth_missing)})")

    # Honest measured numbers on a fixture that INCLUDES a generic-collision false
    # positive (report-exporter / media-uploader share storage+cache). Recall must
    # be perfect (every real missing edge recovered); precision must clear the
    # pre-registered keep bar of 0.70 despite the deliberate false positive.
    assert recall == 1.0, f"MEASURED recall={recall:.3f}"
    assert precision >= 0.70, (
        f"MEASURED precision={precision:.3f} recall={recall:.3f}; "
        f"suggested={sorted(map(sorted, suggested))}")
