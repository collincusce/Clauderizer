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
    assert "Payments Revamp" in (gdir / "GAMEPLAN.md").read_text()


def test_add_project_decision_autonumbers(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.add_decision(paths, title="Use TS", context="c", decision="d", consequences="x")
    r2 = M.add_decision(paths, title="Use CDK", context="c", decision="d", consequences="x")
    # fixture already has D-001
    assert r1["id"] == "D-002"
    assert r2["id"] == "D-003"
    text = paths.doc("DECISIONS").read_text()
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
    assert "Never call trade APIs" in paths.doc("INVARIANTS").read_text()


def test_add_lesson_new_and_existing_category(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.add_lesson(paths, gameplan_id=GID, text="run preflight first", category="Process")
    assert r1["number"] == 4  # fixture has lessons 1-3
    r2 = M.add_lesson(paths, gameplan_id=GID, text="pin your deps", category="Security")
    assert r2["number"] == 5
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text()
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
    status = (paths.gameplan_dir(GID) / "PHASE-STATUS.md").read_text()
    assert "### C-02 — Phase 1" in status


def test_add_phase_appends_and_rows(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_phase(paths, gameplan_id=GID, name="Polish", goal="make it shine")
    assert r["phase"] == 2  # fixture has Phase 0 and 1
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text()
    assert "### Phase 2: Polish" in gp
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text()
    assert "| 2 | Polish |" in idx


def test_add_amendment(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_amendment(
        paths, gameplan_id=GID, title="add task", affected_sections="Phase 1",
        affected_phases="Phase 1", triggered_by="discovery", what="added a task",
        why="missed it", today="2026-06-02",
    )
    assert r["id"] == "A-001"
    gp = (paths.gameplan_dir(GID) / "GAMEPLAN.md").read_text()
    assert "### A-001 — add task" in gp


def test_upsert_entity_create_then_update_preserves_body(temp_repo):
    paths, _ = _ctx(temp_repo)
    r1 = M.upsert_entity(paths, id="subsys.billing", type="subsystem",
                         version="0.1.0", status="planned", today="2026-06-01")
    assert r1["created"] is True
    path = paths.docs / "subsystems" / "billing.md"
    # add human prose to the body
    text = path.read_text()
    path.write_text(text + "\nHand-written prose.\n")
    r2 = M.upsert_entity(paths, id="subsys.billing", type="subsystem",
                         status="active", today="2026-06-02")
    assert r2["created"] is False
    data, body = frontmatter.parse(path.read_text())
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
