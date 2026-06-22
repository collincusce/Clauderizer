"""Phase 3 — typed edge suggestions (redundant vs related), the preemptive-risk
cascade section for a shaky upstream entity, and the empirical recurrence gate on
promotion. All deterministic, advisory, no-write (INVARIANT-05 / D-018)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from clauderizer import analyze, ops, telemetry
from clauderizer import paths as P
from clauderizer.graph import cascade, index
from clauderizer.markdown import frontmatter

FIXED = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)


def _entity(paths, eid, body, *, status="active", depends_on=None):
    type_ = "subsystem" if eid.startswith("subsys") else "feature"
    data = {"id": eid, "type": type_, "version": "1.0.0", "status": status}
    if depends_on is not None:
        data["depends_on"] = list(depends_on)
    sub = "subsystems" if type_ == "subsystem" else "features"
    path = paths.docs / sub / f"{eid.split('.', 1)[-1]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.serialize(data, body), encoding="utf-8")


def _pair(s):
    return frozenset((s["a"], s["b"]))


def test_suggest_edges_labels_redundant_and_related(temp_repo):
    paths = P.resolve(temp_repo)
    _entity(paths, "subsys.ledger-core", "invoice ledger billing posting reconciliation")
    _entity(paths, "subsys.ledger-cache", "invoice ledger billing posting reconciliation cache")
    _entity(paths, "subsys.ledger-export", "invoice ledger export reporting dashboard")
    by_pair = {_pair(s): s for s in analyze.suggest_edges(paths, k=50)}
    red = by_pair[frozenset(("subsys.ledger-cache", "subsys.ledger-core"))]
    rel = by_pair[frozenset(("subsys.ledger-core", "subsys.ledger-export"))]
    assert red["kind"] == "redundant"     # near-duplicate purpose
    assert rel["kind"] == "related"       # shares some vocab, not a near-dup


def test_cascade_flags_dependents_of_shaky_upstream(temp_repo):
    paths = P.resolve(temp_repo)
    _entity(paths, "subsys.foundation", "shared core primitive everything builds upon",
            status="superseded")
    _entity(paths, "subsys.consumer", "feature built atop the foundation primitive",
            depends_on=["subsys.foundation"])
    g = index.build(paths.docs)
    report = cascade.render_report(g, "subsys.foundation",
                                   "status active -> superseded", now=FIXED)
    assert "### Preemptive risk" in report
    risk = report.split("### Preemptive risk", 1)[1]
    assert "superseded" in risk and "subsys.consumer" in risk


def test_cascade_no_risk_section_for_healthy_upstream(temp_repo):
    paths = P.resolve(temp_repo)
    _entity(paths, "subsys.foundation-ok", "shared core primitive", status="active")
    _entity(paths, "subsys.consumer-ok", "built atop the foundation-ok primitive",
            depends_on=["subsys.foundation-ok"])
    g = index.build(paths.docs)
    report = cascade.render_report(g, "subsys.foundation-ok",
                                   "version 1.0.0 -> 1.1.0", now=FIXED)
    assert "### Preemptive risk" not in report   # an active upstream is not shaky


def _surface(paths, phase, gameplan):
    telemetry.record_surfaced(paths.telemetry_file, gameplan="g", phase=phase,
                              lessons=[], invariants=[], gameplan_lessons=gameplan,
                              today="2026-06-21")


def _outcome(paths, phase, status):
    telemetry.record_outcome(paths.telemetry_file, gameplan="g", phase=phase,
                             status=status, criteria_total=1,
                             criteria_checked=1 if status == "complete" else 0,
                             today="2026-06-21")


def test_promotion_gate_requires_recurrence_and_correlation(temp_repo):
    """Darwin-Godel-style gate: promote a gameplan lesson only on empirical
    recurrence (>= 2 resolved surfacings) AND correlation with passing (utility
    >= 0.8). One surfacing, or a mixed record, is gated out."""
    GID = "2026-05-01-bootstrap"
    cwd = os.getcwd(); os.chdir(temp_repo)
    try:
        res, ok = ops.run_batch([
            {"op": "cz_add_lesson", "args": {"text": "gate lesson alpha one", "gameplan_id": GID}},
            {"op": "cz_add_lesson", "args": {"text": "gate lesson beta two", "gameplan_id": GID}},
            {"op": "cz_add_lesson", "args": {"text": "gate lesson gamma three", "gameplan_id": GID}},
        ])
        assert ok, res
        n1, n2, n3 = (str(res[i]["result"]["number"]) for i in range(3))
        paths = P.resolve(temp_repo)
        _surface(paths, "1", [n1]); _outcome(paths, "1", "complete")      # 1 pass only
        _surface(paths, "2", [n2]); _outcome(paths, "2", "complete")      # 2 passes
        _surface(paths, "3", [n2]); _outcome(paths, "3", "complete")
        _surface(paths, "4", [n3]); _outcome(paths, "4", "complete")      # 1 pass + 1 fail
        _surface(paths, "5", [n3]); _outcome(paths, "5", "failed")
        promotes = {p["lessons"][0]
                    for p in telemetry.curate_proposals(paths, GID)["proposals"]
                    if p["action"] == "promote"}
    finally:
        os.chdir(cwd)
    assert n2 in promotes        # recurrence + correlation -> promote
    assert n1 not in promotes    # only one surfacing -> gated by recurrence
    assert n3 not in promotes    # utility 0.5 -> gated by correlation
