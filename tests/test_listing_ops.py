"""The listing read ops (PhaseKeep m0 asks O-02, O-06..O-14).

Each register's listing is tested against data written by its own blessed
mutation in the same test — writer and reader share a grammar, so every test
here is a round-trip, not a fixture-format assumption.
"""

import contextlib
import os

from clauderizer import ops
from clauderizer.paths import resolve

GID = "2026-05-01-bootstrap"


@contextlib.contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _run(op_name, **kwargs):
    return ops.REGISTRY[op_name].fn(**kwargs)


# --- open items (O-06) --------------------------------------------------------


def test_open_items_roundtrip_with_resolution(temp_repo):
    with _chdir(temp_repo):
        added = _run("cz_add_open_item", text="What color is the bikeshed?", phase="1")
        oid = added["id"]
        listed = _run("cz_list_open_items")
        item = next(i for i in listed["items"] if i["id"] == oid)
        assert item["gameplan"] == GID
        assert item["phase"] == "1"
        assert item["text"] == "What color is the bikeshed?"
        assert item["resolved"] is False

        _run("cz_resolve_open_item", id=oid,
             resolution="green (with (nested) parens)")
        relisted = _run("cz_list_open_items")
        item = next(i for i in relisted["items"] if i["id"] == oid)
        assert item["resolved"] is True
        assert item["resolution"] == "green (with (nested) parens)"
        assert item["resolved_date"]
        unresolved_only = _run("cz_list_open_items", include_resolved=False)
        assert oid not in [i["id"] for i in unresolved_only["items"]]


# --- decisions / invariants / findings (O-07, O-08) ---------------------------


def test_decisions_listing_renders_supersession_chains(temp_repo):
    with _chdir(temp_repo):
        first = _run("cz_add_decision", title="Pick blue", context="c",
                     decision="blue", consequences="paint")
        second = _run("cz_add_decision", title="Pick green instead", context="c",
                      decision="green", consequences="repaint",
                      supersedes=first["id"])
        listed = _run("cz_list_decisions")
    by_id = {d["id"]: d for d in listed["decisions"]}
    assert by_id[second["id"]]["supersedes"] == first["id"]
    assert by_id[first["id"]]["superseded_by"] == second["id"]
    assert by_id[first["id"]]["status"] == "superseded"
    assert by_id[second["id"]]["status"] == "active"
    assert by_id[second["id"]]["date"]
    assert "body" not in by_id[second["id"]]
    with_bodies = None
    with _chdir(temp_repo):
        with_bodies = _run("cz_list_decisions", include_bodies=True)
    assert any("green" in d.get("body", "") for d in with_bodies["decisions"])


def test_invariants_listing_carries_scope(temp_repo):
    with _chdir(temp_repo):
        added = _run("cz_add_invariant", text="Never do the bad thing.")
        listed = _run("cz_list_invariants")
    inv = next(i for i in listed["invariants"] if i["id"] == added["id"])
    assert inv["scope"] == "project"


def test_findings_listing(temp_repo):
    with _chdir(temp_repo):
        added = _run("cz_add_finding", title="Open port", severity="low",
                     impact="none really")
        listed = _run("cz_list_findings")
    assert added["id"] in [f["id"] for f in listed["findings"]]


# --- lessons (O-09) -----------------------------------------------------------


def test_lessons_listing_tracks_curation_state(temp_repo):
    with _chdir(temp_repo):
        _run("cz_add_lesson", text="Always measure first.", category="Process",
             evidence="phase 0 numbers")
        _run("cz_add_lesson", text="Then measure again.", category="Process")
        listed = _run("cz_list_lessons")
        actives = [l for l in listed["lessons"]
                   if l["origin"] == "gameplan" and l["state"] == "active"]
        assert {l["text"] for l in actives} >= {
            "Always measure first. *(evidence: phase 0 numbers)*",
            "Then measure again."}
        first_id = next(l["id"] for l in actives
                        if l["text"].startswith("Always measure"))
        _run("cz_obsolete_lesson", number=first_id, reason="superseded")
        relisted = _run("cz_list_lessons")
    states = {l["id"]: l["state"] for l in relisted["lessons"]
              if l["origin"] == "gameplan"}
    assert states[first_id] == "obsolete"
    ev = next(l["evidence"] for l in relisted["lessons"]
              if l["origin"] == "gameplan" and l["id"] == first_id)
    assert ev == "phase 0 numbers"


# --- corrections / amendments (O-10, O-13) ------------------------------------


def test_corrections_listing_roundtrip(temp_repo):
    with _chdir(temp_repo):
        added = _run("cz_add_correction", phase="0",
                     gameplan_said="tests were green",
                     actually="tests were red",
                     why="wrong branch")
        listed = _run("cz_list_corrections")
    rec = next(c for c in listed["corrections"] if c["id"] == added["id"])
    assert rec["gameplan"] == GID
    assert rec["phase"] == "0"
    assert rec["gameplan_said"] == "tests were green"
    assert rec["actually"] == "tests were red"
    assert rec["why"] == "wrong branch"


def test_amendments_listing_roundtrip(temp_repo):
    with _chdir(temp_repo):
        added = _run("cz_add_amendment", title="Drop phase 2",
                     affected_sections="Phase Breakdown",
                     affected_phases="2", triggered_by="scope cut",
                     what="removed it", why="not needed")
        listed = _run("cz_list_amendments")
    rec = next(a for a in listed["amendments"] if a["id"] == added["id"])
    assert rec["title"] == "Drop phase 2"
    assert rec["affected_phases"] == "2"
    assert rec["triggered_by"] == "scope cut"


# --- phase detail (O-11) ------------------------------------------------------


def test_phase_detail_serves_every_gameplan_with_criteria_state(temp_repo):
    with _chdir(temp_repo):
        _run("cz_check_exit_criterion", phase="0", criterion="files exist")
        detail = _run("cz_phase_detail")
    gp = next(g for g in detail["gameplans"] if g["gameplan"] == GID)
    assert gp["lifecycle"]
    p0 = next(p for p in gp["phases"] if p["number"] == "0")
    assert p0["goal"] == "lay down the skeleton."
    crit = next(c for c in p0["exit_criteria"] if c["text"] == "files exist")
    assert crit["checked"] is True


def test_phase_detail_surfaces_approval_staleness(temp_repo):
    artifact = temp_repo / "docs" / "spec.md"
    artifact.write_text("v1 of the spec\n", encoding="utf-8")
    with _chdir(temp_repo):
        _run("cz_set_exit_criteria", phase="0",
             criteria=["APPROVAL: docs/spec.md — human signs off the spec"])
        _run("cz_approve_gate", phase="0", criterion="APPROVAL: docs/spec.md")
        fresh = _run("cz_phase_detail", gameplan_id=GID)
        artifact.write_text("v2 — edited after approval\n", encoding="utf-8")
        stale = _run("cz_phase_detail", gameplan_id=GID)

    def approval_state(result):
        p0 = next(p for p in result["gameplans"][0]["phases"] if p["number"] == "0")
        return next(c["state"] for c in p0["exit_criteria"] if c.get("kind") == "approval")

    assert approval_state(fresh) == "approved"
    assert approval_state(stale) == "stale"


# --- cascade reports (O-12) ---------------------------------------------------


def test_cascade_reports_listing_tracks_pending_then_resolved(temp_repo):
    with _chdir(temp_repo):
        _run("cz_cascade", entity_id="subsys.calc-engine", transition="status probe")
        pending = _run("cz_list_cascade_reports")
        assert len(pending["reports"]) == 1
        report = pending["reports"][0]
        assert report["pending"] is True
        assert report["trigger"].startswith("subsys.calc-engine")
        flagged = [d for d in report["dependents"] if d["needs_review"]]
        assert flagged, "the probe cascade should flag at least one dependent"

        verdicts = {d["entity"]: "no change needed" for d in report["dependents"]}
        _run("cz_resolve_cascade", verdicts=verdicts, updates_applied="none")
        resolved = _run("cz_list_cascade_reports")
        report = resolved["reports"][0]
        assert report["pending"] is False
        assert report["updates_applied"] == "none"
        assert all(not d["needs_review"] for d in report["dependents"])
        only_pending = _run("cz_list_cascade_reports", include_resolved=False)
        assert only_pending["reports"] == []


# --- docs (O-14) --------------------------------------------------------------


def test_docs_index_and_doc_read(temp_repo):
    with _chdir(temp_repo):
        index = _run("cz_docs_index")
        names = [d["name"] for d in index["docs"]]
        assert "DECISIONS.md" in names
        assert any(n.endswith("PHASE-0-HANDOFF.md") for n in names)
        body = _run("cz_doc", name="DECISIONS")
    assert body["ok"] is True
    assert "Decisions" in body["body"]


def test_doc_read_strips_frontmatter_and_refuses_escapes(temp_repo):
    with _chdir(temp_repo):
        ent = _run("cz_doc", name="subsystems/auth.md")
        assert ent["ok"] is True
        assert not ent["body"].lstrip().startswith("---")
        escape = _run("cz_doc", name="../CLAUDE.md")
        missing = _run("cz_doc", name="NOPE.md")
    assert escape["ok"] is False
    assert missing["ok"] is False


# --- assignments (O-02) -------------------------------------------------------


def test_assignment_roundtrip_gameplan_phase_manager(temp_repo):
    with _chdir(temp_repo):
        assert _run("cz_assign", gameplan_id=GID, assignee="claude@native")["ok"]
        assert _run("cz_assign", gameplan_id=GID, phase="1",
                    assignee="kimi@wsl:Ubuntu")["ok"]
        assert _run("cz_assign", role="manager", assignee="claude@native")["ok"]
        surface = _run("cz_assignments")
        detail = _run("cz_phase_detail", gameplan_id=GID)
        status = _run("cz_status")

    assert surface["manager"] == "claude@native"
    gp = next(g for g in surface["gameplans"] if g["gameplan"] == GID)
    assert gp["assignee"] == "claude@native"
    assert gp["phases"] == [{"number": "1", "assigned": "kimi@wsl:Ubuntu"}]

    phases = {p["number"]: p for p in detail["gameplans"][0]["phases"]}
    assert phases["1"]["assigned"] == "kimi@wsl:Ubuntu"   # override
    assert phases["0"]["assigned"] == "claude@native"     # gameplan default

    card = next(c for c in status["portfolio"] if c["id"] == GID)
    assert card["assignee"] == "claude@native"


def test_assignment_clears(temp_repo):
    paths = resolve(temp_repo)
    with _chdir(temp_repo):
        _run("cz_assign", gameplan_id=GID, assignee="claude@native")
        _run("cz_assign", gameplan_id=GID, phase="1", assignee="kimi@wsl:Ubuntu")
        _run("cz_assign", role="manager", assignee="claude@native")
        _run("cz_assign", gameplan_id=GID, assignee="")
        _run("cz_assign", gameplan_id=GID, phase="1", assignee="")
        _run("cz_assign", role="manager", assignee="")
        surface = _run("cz_assignments")
    assert surface["manager"] is None
    gp = next(g for g in surface["gameplans"] if g["gameplan"] == GID)
    assert gp["assignee"] is None
    assert gp["phases"] == []
    gp_text = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "Assignee:" not in gp_text
    assert "**Assigned**" not in gp_text


def test_assignment_is_idempotent(temp_repo):
    with _chdir(temp_repo):
        first = _run("cz_assign", gameplan_id=GID, phase="1", assignee="a@native")
        second = _run("cz_assign", gameplan_id=GID, phase="1", assignee="a@native")
    assert first["changed"] is True
    assert second["changed"] is False


def test_assign_rejects_unknown_role_and_missing_phase(temp_repo):
    with _chdir(temp_repo):
        bad_role = _run("cz_assign", role="intern", assignee="x@native")
        bad_phase = _run("cz_assign", gameplan_id=GID, phase="9",
                         assignee="x@native")
    assert bad_role["ok"] is False
    assert bad_phase["ok"] is False
