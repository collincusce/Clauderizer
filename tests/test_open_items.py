"""The clarify gate (Phase 0 of spec-kit-discipline-gates, D-015): structured
open items (O-NN), resolved in place, surfaced advisorily — never blocking
(INVARIANT-05).
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import sections
from clauderizer.rituals import status_bundle


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _fresh(paths, name="Gate Plan"):
    return M.create_gameplan(paths, name, today="2026-06-08")["gameplan_id"]


def _open_body(paths, gid):
    gp = paths.gameplan_dir(gid) / "GAMEPLAN.md"
    return sections.get_section(gp.read_text(encoding="utf-8"), "Open Items")


def test_add_open_item_autonumbers_and_replaces_placeholder(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    r1 = M.add_open_item(paths, gameplan_id=gid, text="Which embedding backend?")
    r2 = M.add_open_item(paths, gameplan_id=gid, text="Confirm the index path")
    assert r1["id"] == "O-01" and r2["id"] == "O-02"
    body = _open_body(paths, gid)
    assert body.lstrip().startswith("**O-01.**")  # scaffold placeholder replaced
    assert "**O-01.** Which embedding backend?" in body
    assert "**O-02.** Confirm the index path" in body


def test_add_open_item_phase_tag(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    r = M.add_open_item(paths, gameplan_id=gid, text="blocks phase 1", phase="1")
    assert r["id"] == "O-01"
    assert "**O-01.** _(phase 1)_ blocks phase 1" in _open_body(paths, gid)


def test_resolve_open_item_marks_and_is_idempotent(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.add_open_item(paths, gameplan_id=gid, text="needs answer")
    r1 = M.resolve_open_item(paths, gameplan_id=gid, id="O-01",
                             resolution="decided X", today="2026-06-08")
    assert r1["ok"] and r1["already_resolved"] is False
    assert "_(resolved 2026-06-08: decided X)_" in _open_body(paths, gid)
    # idempotent: re-resolving is a no-op — no second marker, no write
    r2 = M.resolve_open_item(paths, gameplan_id=gid, id="O-01",
                             resolution="decided again", today="2026-06-09")
    assert r2["already_resolved"] is True and r2["files_changed"] == []
    body = _open_body(paths, gid)
    assert body.count("_(resolved") == 1 and "decided again" not in body


def test_resolve_unknown_open_item_fails_cleanly(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    assert M.resolve_open_item(paths, gameplan_id=gid, id="O-99", resolution="x")["ok"] is False


def test_status_reports_only_unresolved_open_items(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = _fresh(paths)
    M.add_open_item(paths, gameplan_id=gid, text="one")
    M.add_open_item(paths, gameplan_id=gid, text="two")
    M.resolve_open_item(paths, gameplan_id=gid, id="O-01", resolution="done",
                        today="2026-06-08")
    config.active_gameplan = gid
    bundle = status_bundle.compute(paths, config)
    assert bundle["open_items"] == ["O-02"]
    assert "Open items: 1 unresolved (O-02)." in status_bundle.render_digest(bundle)


def test_transition_complete_surfaces_relevant_open_items_without_blocking(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.add_open_item(paths, gameplan_id=gid, text="general blocker")           # O-01 untagged
    M.add_open_item(paths, gameplan_id=gid, text="phase-1 thing", phase="1")  # O-02
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="complete", today="2026-06-08")
    assert r["ok"] is True  # advisory NEVER blocks (INVARIANT-05)
    adv = r.get("advisories") or []
    assert len(adv) == 1
    assert adv[0]["kind"] == "open_items"
    assert adv[0]["ids"] == ["O-01"]  # untagged is relevant to phase 0; O-02 (phase 1) is not


def test_transition_complete_no_advisory_when_all_resolved(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.add_open_item(paths, gameplan_id=gid, text="blocker")
    M.resolve_open_item(paths, gameplan_id=gid, id="O-01", resolution="done",
                        today="2026-06-08")
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="complete", today="2026-06-08")
    assert "advisories" not in r  # nothing unresolved → no advisory noise
