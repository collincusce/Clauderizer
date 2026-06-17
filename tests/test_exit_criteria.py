"""The exit-criteria gate (Phase 1 of spec-kit-discipline-gates, D-015):
machine-checkable - [ ] criteria, surfaced advisorily on completion (never
blocking — INVARIANT-05).
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import sections
from clauderizer.rituals import status_bundle


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _fresh(paths, name="Criteria Plan"):
    return M.create_gameplan(paths, name, today="2026-06-08")["gameplan_id"]


def _breakdown(paths, gid):
    gp = paths.gameplan_dir(gid) / "GAMEPLAN.md"
    return sections.get_section(gp.read_text(encoding="utf-8"), "Phase Breakdown")


def test_set_exit_criteria_replaces_placeholder(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    r = M.set_exit_criteria(paths, gameplan_id=gid, phase="0",
                            criteria=["tools on the registry", "suite stays green"])
    assert r["ok"] and r["count"] == 2
    body = _breakdown(paths, gid)
    assert "- [ ] tools on the registry" in body
    assert "- [ ] suite stays green" in body
    assert "_(verifiable" not in body  # template placeholder gone
    crit = status_bundle.exit_criteria(paths.gameplan_dir(gid), "0")
    assert [c["text"] for c in crit] == ["tools on the registry", "suite stays green"]
    assert all(not c["checked"] for c in crit)


def test_check_exit_criterion_toggles_and_is_idempotent(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0",
                        criteria=["registry parity green", "docs updated"])
    r1 = M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="parity")
    assert r1["ok"] and r1["changed"] is True
    body = _breakdown(paths, gid)
    assert "- [x] registry parity green" in body
    assert "- [ ] docs updated" in body
    # idempotent: checking again is a no-op
    r2 = M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="parity")
    assert r2["changed"] is False and r2["files_changed"] == []
    # uncheck works too
    r3 = M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="parity",
                                checked=False)
    assert r3["changed"] is True
    assert "- [ ] registry parity green" in _breakdown(paths, gid)


def test_set_exit_criteria_preserves_checked_state_on_unchanged_text(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0", criteria=["alpha", "beta"])
    M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="alpha")
    # re-set with alpha unchanged + a new gamma: alpha stays checked, gamma fresh
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0", criteria=["alpha", "gamma"])
    crit = {c["text"]: c["checked"]
            for c in status_bundle.exit_criteria(paths.gameplan_dir(gid), "0")}
    assert crit == {"alpha": True, "gamma": False}


def test_check_unknown_criterion_fails(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0", criteria=["something"])
    assert M.check_exit_criterion(paths, gameplan_id=gid, phase="0",
                                  criterion="nope")["ok"] is False


def test_transition_complete_surfaces_unchecked_criteria_without_blocking(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0",
                        criteria=["criterion A", "criterion B"])
    M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="criterion A")
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="complete", today="2026-06-08")
    assert r["ok"] is True  # advisory NEVER blocks (INVARIANT-05)
    ec = [a for a in r.get("advisories", []) if a["kind"] == "exit_criteria"]
    assert len(ec) == 1
    assert ec[0]["items"] == ["criterion B"]  # only the unchecked one


def test_exit_criteria_advisory_auto_links_test_criterion_to_baseline(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = _fresh(paths)
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    idx.write_text(idx.read_text(encoding="utf-8")
                   + "\n**Current baseline test count**: 273\n", encoding="utf-8")
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0",
                        criteria=["full test suite green", "README updated"])
    r = M.transition_phase(paths, gameplan_id=gid, phase_n="0",
                           to_status="complete", today="2026-06-08")
    ec = next(a for a in r["advisories"] if a["kind"] == "exit_criteria")
    items = ec["items"]
    # the test-ish criterion is annotated with the measured baseline; the doc one is not
    assert any("[measured: baseline" in it for it in items if "suite" in it)
    assert all("[measured" not in it for it in items if "README" in it)
