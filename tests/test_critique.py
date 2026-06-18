"""The self-critique gate (D-019): a reference-free Coverage/Coherence/Grounding
rubric assembled from the engine's existing deterministic signals and surfaced
for the agent to grade — advisory, read-only, stdlib-only."""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import critique


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _fresh(paths):
    """Create a gameplan (Phase 0) and return (gid, a config pointed at it).

    mutations.create_gameplan scaffolds the gameplan but does NOT flip
    active_gameplan — that is the ops/CLI layer's job (ops.cz_create_gameplan sets
    config.active_gameplan in memory) — so point the config at it explicitly here.
    """
    gid = M.create_gameplan(paths, "Critique Test", today="2026-06-18")["gameplan_id"]
    config = cfg.Config.load(paths.config_file)
    config.active_gameplan = gid
    return gid, config


def test_critique_has_three_dimensions_and_prompt(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    res = critique.critique(paths, config, target="gameplan")
    assert res["ok"]
    assert [d["name"] for d in res["dimensions"]] == ["Coverage", "Coherence", "Grounding"]
    assert "rubric" in res["prompt"].lower()
    assert isinstance(res["gap_count"], int)


def test_coverage_flags_open_items_and_unchecked_criteria(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    M.add_open_item(paths, gameplan_id=gid, text="a real blocker")
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0", criteria=["the thing is verifiable"])
    res = critique.critique(paths, config, target="gameplan")
    coverage = next(d for d in res["dimensions"] if d["name"] == "Coverage")
    assert not coverage["clean"]
    assert any("open item" in g and "unresolved" in g for g in coverage["gaps"])
    assert any("exit criterion unchecked" in g for g in coverage["gaps"])


def test_coverage_clears_when_criterion_checked(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    M.set_exit_criteria(paths, gameplan_id=gid, phase="0", criteria=["ship it"])
    M.check_exit_criterion(paths, gameplan_id=gid, phase="0", criterion="ship it")
    res = critique.critique(paths, config, target="0")  # phase target ignores other phases
    coverage = next(d for d in res["dimensions"] if d["name"] == "Coverage")
    assert not any("exit criterion unchecked" in g for g in coverage["gaps"])


def test_grounding_flags_lessons_without_evidence(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    M.add_lesson(paths, gameplan_id=gid, text="alpha lacks a citation")
    M.add_lesson(paths, gameplan_id=gid, text="beta carries a citation", evidence="commit deadbeef")
    res = critique.critique(paths, config, target="gameplan")
    grounding = next(d for d in res["dimensions"] if d["name"] == "Grounding")
    assert any("alpha" in g for g in grounding["gaps"])       # un-evidenced -> flagged
    assert not any("beta" in g for g in grounding["gaps"])    # evidence-bearing -> not flagged
