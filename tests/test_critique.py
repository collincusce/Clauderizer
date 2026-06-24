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


def test_critique_has_storm_and_calm_dimensions_and_prompt(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    res = critique.critique(paths, config, target="gameplan")
    assert res["ok"]
    names = [d["name"] for d in res["dimensions"]]
    # STORM rubric first, order preserved; CALM anti-bias axes appended (D1).
    assert names[:3] == ["Coverage", "Coherence", "Grounding"]
    assert names[3:] == ["Self-enhancement", "Authority"]
    assert "rubric" in res["prompt"].lower()
    assert "calm" in res["prompt"].lower()
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


# --- CALM anti-bias axes (D1) ------------------------------------------------

def _dim(res, name):
    return next(d for d in res["dimensions"] if d["name"] == name)


def test_authority_axis_flags_unverifiable_citation_prior_missed(temp_repo):
    """A lesson WITH an evidence marker but only an external-authority citation:
    the prior Grounding check passes it (marker present); the new Authority axis
    catches it — exactly the gap the old rubric scored clean."""
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    M.add_lesson(paths, gameplan_id=gid, text="leans on a paper",
                 evidence="arXiv:2410.02736")                          # authority-only
    M.add_lesson(paths, gameplan_id=gid, text="cites provenance",
                 evidence="commit a1b2c3d, tests/test_critique.py:69")  # anchored
    res = critique.critique(paths, config, target="gameplan")
    assert _dim(res, "Grounding")["clean"]                  # prior axis: both have markers
    authority = _dim(res, "Authority")
    assert not authority["clean"]
    assert len(authority["gaps"]) == 1
    assert any("unverifiable authority" in g for g in authority["gaps"])


def test_self_enhancement_flags_hollow_resolution_prior_missed(temp_repo):
    """A resolved-but-hollow open item: prior Coverage flags only UNRESOLVED
    items (clean here); the Self-enhancement axis catches the fiat closure."""
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    r = M.add_open_item(paths, gameplan_id=gid, text="a real blocker")
    M.resolve_open_item(paths, gameplan_id=gid, id=r["id"],
                        resolution="done", today="2026-06-24")          # hollow
    res = critique.critique(paths, config, target="gameplan")
    coverage = _dim(res, "Coverage")
    selfenh = _dim(res, "Self-enhancement")
    assert not any("open item" in g and "unresolved" in g for g in coverage["gaps"])
    assert not selfenh["clean"]
    assert any(r["id"] in g and "hollow" in g for g in selfenh["gaps"])


def test_bias_axes_quiet_on_sound_gameplan(temp_repo):
    """Precision guard: a substantive resolution + anchored evidence raise no
    false flags on either CALM axis."""
    paths, _ = _ctx(temp_repo)
    gid, config = _fresh(paths)
    r = M.add_open_item(paths, gameplan_id=gid, text="a real blocker")
    M.resolve_open_item(paths, gameplan_id=gid, id=r["id"],
                        resolution="fixed in critique.py:130; covered by test_x",
                        today="2026-06-24")
    M.add_lesson(paths, gameplan_id=gid, text="grounded",
                 evidence="suite 620 green, commit a1b2c3d")
    res = critique.critique(paths, config, target="gameplan")
    assert _dim(res, "Self-enhancement")["clean"]
    assert _dim(res, "Authority")["clean"]


# --- pure classifier precision contracts (the adversarial near-misses) -------

def test_evidence_is_authority_precision():
    f = critique._evidence_is_authority
    assert f("arXiv:2410.02736")                                   # bare paper
    assert f("verified 3-0 by the review panel")                   # bare appeal
    assert not f("commit a1b2c3d; tests/test_critique.py:69")      # anchored
    # near-miss: paper citation that is ALSO anchored in-repo -> sound
    assert not f("arXiv:2410.02736, validated in tests/test_critique.py against commit deadbeef")
    # near-miss: appeal word 'confirmed' but anchored by a pinned CI run
    assert not f("confirmed green on windows-3.11 CI, run 9/9")


def test_resolution_is_hollow_precision():
    f = critique._resolution_is_hollow
    assert f("done")
    assert f("looks good")
    # near-miss: LONG but entirely hollow -> still hollow (length is not the signal)
    assert f("this has been fully taken care of and everything is now completely fine")
    # near-miss: terse but anchored -> not hollow
    assert not f("see commit a1b2c3d")
    assert not f("added _authority_flags in critique.py:130")


def test_overclaims_precision():
    f = critique._overclaims
    assert f("Everything passes, fully verified, ready to ship.")
    assert f("no gaps remain; production-ready")
    assert not f("Phase 0 done: added two helpers, 622 tests green.")
    # near-miss: factual 'all criteria' with substantiation, no intensifier
    assert not f("All 4 exit criteria were checked off after verification against the fixture.")
