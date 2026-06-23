from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.graph import index
from clauderizer.markdown import frontmatter, sections

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_create_gameplan(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.create_gameplan(paths, "Payments Revamp", today="2026-06-01")
    assert r["gameplan_id"] == "2026-06-01-payments-revamp"
    gdir = paths.gameplan_dir("2026-06-01-payments-revamp")
    assert (gdir / "GAMEPLAN.md").exists()
    assert (gdir / "CHAT-HANDOFF-INDEX.md").exists()
    assert (gdir / "_cascade-reports").is_dir()
    assert "Payments Revamp" in (gdir / "GAMEPLAN.md").read_text(encoding="utf-8")


def test_add_project_decision_autonumbers(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.add_decision(paths, title="Use TS", context="c", decision="d", consequences="x")
    r2 = M.add_decision(paths, title="Use CDK", context="c", decision="d", consequences="x")
    # fixture already has D-001
    assert r1["id"] == "D-002"
    assert r2["id"] == "D-003"
    text = paths.doc("DECISIONS").read_text(encoding="utf-8")
    assert "### D-002 — Use TS" in text and "### D-003 — Use CDK" in text


def test_add_gameplan_decision_uses_bare_numbering(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_decision(
        paths, scope="gameplan", gameplan_id=GID,
        title="tactic", context="c", decision="d", consequences="x",
    )
    # fixture GAMEPLAN has D1 already
    assert r["id"] == "D2"


def test_add_invariant_autonumbers(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_invariant(paths, text="Never call trade APIs server-side", introduced_by="D-002")
    assert r["id"] == "INVARIANT-02"  # fixture has INVARIANT-01
    assert "Never call trade APIs" in paths.doc("INVARIANTS").read_text(encoding="utf-8")


def test_add_finding_autonumbers_and_renders_fields(temp_repo):
    paths, _ = _ctx(temp_repo)
    # fixture has no HARDENING.md yet -> created from template, first id is H-01
    r1 = M.add_finding(
        paths, title="Sample finding one", severity="HIGH",
        impact="example impact text", invariant="INVARIANT-02",
        affected="src/example.py:handler", recommendation="apply the documented fix",
        today="2026-06-05",
    )
    assert r1["id"] == "H-01"
    r2 = M.add_finding(paths, title="Sample finding two", severity="MEDIUM",
                       impact="another example impact", today="2026-06-05")
    assert r2["id"] == "H-02"
    text = paths.doc("HARDENING").read_text(encoding="utf-8")
    assert "### H-01 — Sample finding one" in text
    assert "### H-02 — Sample finding two" in text
    assert "**Severity**: HIGH" in text
    assert "**Status**: open (2026-06-05)" in text
    assert "**Affected**: src/example.py:handler" in text
    assert "**Invariant violated**: INVARIANT-02" in text
    # optional fields are omitted when not supplied
    assert "**Root cause**" not in text
    h2_block = text.split("### H-02")[1]
    assert "**Affected**" not in h2_block  # H-02 supplied no affected code


def test_add_finding_is_aliased_as_add_risk(temp_repo):
    paths, _ = _ctx(temp_repo)
    assert M.add_risk is M.add_finding
    r = M.add_risk(paths, title="x", severity="LOW", impact="y", today="2026-06-05")
    assert r["id"] == "H-01"


def test_add_lesson_new_and_existing_category(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.add_lesson(paths, gameplan_id=GID, text="run preflight first", category="Process")
    assert r1["number"] == 4  # fixture has lessons 1-3
    r2 = M.add_lesson(paths, gameplan_id=GID, text="pin your deps", category="Security")
    assert r2["number"] == 5
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    sec = sections.get_section(idx, "Accumulated Lessons")
    assert "### Category: Security" in sec
    assert "run preflight first" in sec and "pin your deps" in sec


def test_add_correction_promotes_lesson(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_correction(
        paths, gameplan_id=GID, phase="1",
        gameplan_said="do X", actually="do Y", why="z",
        lesson="prefer Y", category="Process",
    )
    assert r["id"] == "C-02"  # fixture has C-01
    assert r["lesson"]["number"] == 4
    status = (paths.gameplan_dir(GID) / "PHASE-STATUS.md").read_text(encoding="utf-8")
    assert "### C-02 — Phase 1" in status


def test_resolve_cascade_records_verdicts_and_unpends(temp_repo):
    from pathlib import Path

    from clauderizer.rituals.status_bundle import pending_cascades

    paths, config = _ctx(temp_repo)
    r = M.transition_status(paths, config, id="subsys.auth", to_status="completed")
    report = Path(r["cascade"]["report_path"])
    reports_dir = report.parent
    assert report.name in pending_cascades(reports_dir)

    res = M.resolve_cascade(
        paths, gameplan_id=GID,
        verdicts={"feat.login": "no change needed (login does not pin a version)"},
        updates_applied="None required — verified feat.login docs still accurate.",
    )
    assert res["ok"] and res["resolved"] == ["feat.login"]
    assert res["pending"] is False
    assert report.name not in pending_cascades(reports_dir)
    text = report.read_text(encoding="utf-8")
    assert "_needs review_" not in text
    assert "no change needed (login does not pin a version)" in text
    assert "_(fill in concrete edits" not in text


def test_resolve_cascade_partial_resolution_stays_pending(temp_repo):
    from clauderizer.rituals.status_bundle import pending_cascades

    paths, config = _ctx(temp_repo)
    r = M.transition_status(paths, config, id="subsys.auth", to_status="completed")
    reports_dir = paths.gameplan_dir(GID) / "_cascade-reports"

    # verdict recorded but Updates applied still a placeholder -> pending
    res1 = M.resolve_cascade(paths, gameplan_id=GID,
                             verdicts={"feat.login": "no change needed"})
    assert res1["ok"] and res1["pending"] is True
    assert pending_cascades(reports_dir)

    # second call finishes the job; the verdict is reported as already resolved
    res2 = M.resolve_cascade(paths, gameplan_id=GID,
                             verdicts={"feat.login": "no change needed"},
                             updates_applied="nothing to edit")
    assert res2["already_resolved"] == ["feat.login"]
    assert res2["pending"] is False
    assert not pending_cascades(reports_dir)


def test_resolve_cascade_unknown_ids_and_missing_report(temp_repo):
    paths, config = _ctx(temp_repo)
    assert M.resolve_cascade(paths, gameplan_id=GID, report="nope")["ok"] is False
    # no pending reports at all
    assert M.resolve_cascade(paths, gameplan_id=GID)["ok"] is False
    M.transition_status(paths, config, id="subsys.auth", to_status="completed")
    res = M.resolve_cascade(paths, gameplan_id=GID,
                            verdicts={"feat.ghost": "n/a"},
                            updates_applied="none")
    assert res["unknown_ids"] == ["feat.ghost"]
    assert res["resolved"] == []


def test_obsolete_lesson_marks_prunes_and_is_idempotent(temp_repo):
    from clauderizer.rituals import handoff

    paths, _ = _ctx(temp_repo)
    idx_path = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    _, before_count = handoff.collect_lessons(idx_path.read_text(encoding="utf-8"))
    assert before_count == 3  # fixture has lessons 1-3

    r1 = M.obsolete_lesson(paths, gameplan_id=GID, number=2,
                           reason="cascade is now tool-resolved", today="2026-06-09")
    assert r1["ok"] and r1["already_obsolete"] is False
    text = idx_path.read_text(encoding="utf-8")
    # the line is marked, not deleted
    assert "**2.** Cascade is post-hoc, not predictive. (obsolete 2026-06-09: cascade is now tool-resolved)" in text
    rolled, after_count = handoff.collect_lessons(text)
    assert after_count == 2
    assert "post-hoc, not predictive" not in rolled

    r2 = M.obsolete_lesson(paths, gameplan_id=GID, number=2)
    assert r2["already_obsolete"] is True and r2["files_changed"] == []
    assert M.obsolete_lesson(paths, gameplan_id=GID, number=99)["ok"] is False


def test_consolidate_lessons_shrinks_rollup_keeps_log(temp_repo):
    from clauderizer.rituals import handoff

    paths, _ = _ctx(temp_repo)
    idx_path = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    r = M.consolidate_lessons(
        paths, gameplan_id=GID, numbers=[1, 2],
        text="Markdown is canonical and cascade reconciles it post-hoc.",
        category="Process", today="2026-06-09",
    )
    assert r["ok"] and r["number"] == 4 and r["consolidated"] == [1, 2]
    text = idx_path.read_text(encoding="utf-8")
    # sources stay in the log, marked with the trail
    assert "**1.** Markdown is canonical; the index is disposable. (obsolete 2026-06-09: consolidated into #4)" in text
    assert "consolidated into #4" in text.split("**2.**")[1].splitlines()[0]
    # roll-up shrank: 3 originals -> 1 survivor (#3) + 1 synthesized (#4)
    rolled, count = handoff.collect_lessons(text)
    assert count == 2
    assert "cascade reconciles it post-hoc" in rolled


def test_consolidate_lessons_validates_before_writing(temp_repo):
    paths, _ = _ctx(temp_repo)
    idx_path = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    before = idx_path.read_text(encoding="utf-8")
    # missing source
    r = M.consolidate_lessons(paths, gameplan_id=GID, numbers=[1, 99], text="x")
    assert r["ok"] is False and "#99 not found" in r["summary"]
    # fewer than two distinct sources (duplicates collapse)
    r = M.consolidate_lessons(paths, gameplan_id=GID, numbers=[1, 1], text="x")
    assert r["ok"] is False
    assert idx_path.read_text(encoding="utf-8") == before  # nothing was written
    # already-consolidated source is rejected on a second pass
    M.consolidate_lessons(paths, gameplan_id=GID, numbers=[1, 2], text="merged")
    r = M.consolidate_lessons(paths, gameplan_id=GID, numbers=[2, 3], text="again")
    assert r["ok"] is False and "already obsolete/promoted" in r["summary"]


def test_promote_lesson_round_trip(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.promote_lesson(paths, gameplan_id=GID, number=3, today="2026-06-09")
    assert r["ok"] and r["id"] == "L-01"
    assert r["category"] == "Testing"  # derived from the source category block
    ldoc = paths.doc("LESSONS").read_text(encoding="utf-8")
    assert "# Distilled Lessons" in ldoc  # created on demand from the template
    assert "**L-01.** Keep fixtures small and hand-verifiable. *(from 2026-05-01-bootstrap)*" in ldoc
    assert "### Category: Testing" in ldoc
    # source line marked, not deleted
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "**3.** Keep fixtures small and hand-verifiable. (promoted 2026-06-09: L-01)" in idx
    # re-promoting or promoting a marked lesson is rejected
    assert M.promote_lesson(paths, gameplan_id=GID, number=3)["ok"] is False
    assert M.promote_lesson(paths, gameplan_id=GID, number=42)["ok"] is False


def test_promote_lesson_with_distilled_text_and_category(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.promote_lesson(paths, gameplan_id=GID, number=1,
                         text="Markdown is the source of truth; caches are disposable.",
                         category="Architecture", today="2026-06-09")
    assert r["id"] == "L-01" and r["category"] == "Architecture"
    ldoc = paths.doc("LESSONS").read_text(encoding="utf-8")
    assert "**L-01.** Markdown is the source of truth; caches are disposable." in ldoc


def test_obsolete_project_lesson_by_l_id(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.promote_lesson(paths, gameplan_id=GID, number=3, today="2026-06-09")
    r = M.obsolete_lesson(paths, gameplan_id=GID, number="L-01",
                          reason="superseded by testing guide", today="2026-06-10")
    assert r["ok"] and r["number"] == "L-01"
    ldoc = paths.doc("LESSONS").read_text(encoding="utf-8")
    assert "(obsolete 2026-06-10: superseded by testing guide)" in ldoc
    assert "Keep fixtures small" in ldoc  # never deleted
    assert M.obsolete_lesson(paths, gameplan_id=GID, number="L-01")["already_obsolete"] is True
    assert M.obsolete_lesson(paths, gameplan_id=GID, number="L-09")["ok"] is False


def test_add_phase_appends_and_rows(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_phase(paths, gameplan_id=GID, name="Polish", goal="make it shine")
    assert r["phase"] == 2  # fixture has Phase 0 and 1
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "### Phase 2: Polish" in gp
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "| 2 | Polish |" in idx


def test_add_amendment(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_amendment(
        paths, gameplan_id=GID, title="add task", affected_sections="Phase 1",
        affected_phases="Phase 1", triggered_by="discovery", what="added a task",
        why="missed it", today="2026-06-02",
    )
    assert r["id"] == "A-001"
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "### A-001 — add task" in gp
    # Ritual disabled (the default): no cascade-report line at all. Until 0.7.0
    # every amendment cited `_cascade-reports/<date>-A-NNN.md` — a file no code
    # path creates under any setting (A-001's dangling pointer).
    assert "Cascade report" not in gp


def test_add_amendment_cascade_line_only_under_ritual(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_amendment(
        paths, gameplan_id=GID, title="add task", affected_sections="Phase 1",
        affected_phases="Phase 1", triggered_by="discovery", what="added a task",
        why="missed it", amendments_ritual=True, today="2026-06-02",
    )
    assert r["id"] == "A-001"
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text(encoding="utf-8")
    assert "- **Cascade**: if this amendment changed a tracked entity" in gp
    assert "cz_cascade" in gp
    # Never a per-amendment filename promise — cascade reports are per-entity.
    assert "_cascade-reports/2026-06-02-A-001.md" not in gp


def test_upsert_entity_create_then_update_preserves_body(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.upsert_entity(paths, id="subsys.billing", type="subsystem",
                         version="0.1.0", status="planned", today="2026-06-01")
    assert r1["created"] is True
    path = paths.docs / "subsystems" / "billing.md"
    # add human prose to the body
    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\nHand-written prose.\n", encoding="utf-8")
    r2 = M.upsert_entity(paths, id="subsys.billing", type="subsystem",
                         status="active", today="2026-06-02")
    assert r2["created"] is False
    data, body = frontmatter.parse(path.read_text(encoding="utf-8"))
    assert data["status"] == "active"
    assert "Hand-written prose." in body


def test_transition_status_runs_cascade(temp_repo):
    paths, config = _ctx(temp_repo)
    r = M.transition_status(paths, config, id="subsys.auth", to_status="completed")
    assert r["from"] == "active" and r["to"] == "completed"
    assert "cascade" in r
    assert r["cascade"]["direct"] == ["feat.login"]
    # entity file updated
    g = index.build(paths.docs)
    assert g.get("subsys.auth").status == "completed"
    # report written
    reports = list((paths.gameplan_dir(GID) / "_cascade-reports").glob("*.md"))
    assert reports
