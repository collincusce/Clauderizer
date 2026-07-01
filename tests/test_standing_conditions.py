"""Standing conditions (gameplan 2026-07-01, decision D3) + consumes surfacing.

Conditions are shell probes declared in .clauderizer/conditions.<gid>.toml,
evaluated only inside tool calls (never the hook path — compute() defaults to
no evaluation), surfacing "iteration proposed" when met. Cross-gameplan
consumes render in the handoff with status/version and pending cross-refs
reach the portfolio card.
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import conditions, handoff, preflight, status_bundle

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _declare(paths, gid, body):
    p = paths.clauderizer_dir / f"conditions.{gid}.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_loader_tolerates_missing_and_malformed(temp_repo):
    paths, _ = _ctx(temp_repo)
    assert conditions.load_conditions(paths, GID) == {}
    _declare(paths, GID, "not [ valid toml")
    assert conditions.load_conditions(paths, GID) == {}
    assert conditions.load_conditions(paths, "") == {}


def test_evaluate_met_and_unmet(temp_repo):
    paths, _ = _ctx(temp_repo)
    _declare(paths, GID, '[conditions]\nbacklog_low = "exit 0"\nweekly_due = "exit 1"\n')
    got = {c["name"]: c["met"] for c in conditions.evaluate(paths, GID)}
    assert got == {"backlog_low": True, "weekly_due": False}


def test_compute_default_never_evaluates_hook_safety(temp_repo):
    paths, config = _ctx(temp_repo)
    _declare(paths, config.active_gameplan,
             '[conditions]\nalways = "exit 0"\n')
    bundle = status_bundle.compute(paths, config)  # the hook's exact call shape
    assert "standing_conditions" not in bundle
    digest = status_bundle.render_digest(bundle)
    assert "Standing condition" not in digest


def test_compute_with_conditions_surfaces_proposal(temp_repo):
    paths, config = _ctx(temp_repo)
    _declare(paths, config.active_gameplan,
             '[conditions]\nbacklog_low = "exit 0"\n')
    bundle = status_bundle.compute(paths, config, conditions=True)
    assert bundle["standing_conditions"][0]["met"] is True
    digest = status_bundle.render_digest(bundle)
    assert "⏰ Standing condition met: backlog_low — iteration proposed" in digest


def test_preflight_conditions_check_only_when_declared(temp_repo):
    paths, config = _ctx(temp_repo)
    config.preflight_checks = ["clean_tree"]
    profile = _stub_profile()
    res = preflight.run(paths, config, profile, runner=_ok_runner).to_dict()
    assert all(c["name"] != "standing_conditions" for c in res["checks"])
    _declare(paths, config.active_gameplan, '[conditions]\ndue = "exit 0"\n')
    res2 = preflight.run(paths, config, profile, runner=_ok_runner).to_dict()
    gate = next(c for c in res2["checks"] if c["name"] == "standing_conditions")
    assert gate["status"] == "pass" and "iteration proposed" in gate["detail"]


def test_consumes_renders_with_status_and_version_and_fans_out(temp_repo):
    paths, config = _ctx(temp_repo)
    if "cascade" not in (config.rituals or []):
        config.rituals = list(config.rituals or []) + ["cascade"]
    M.upsert_entity(paths, id="subsys.render", type="subsystem",
                    status="active", version="1.0.0")
    gid_b = M.create_gameplan(paths, "Campaign B", kind="campaign",
                              today="2026-07-02")["gameplan_id"]
    # what cz_consumes sugars over: the gameplan node's depends_on edge
    M.upsert_entity(paths, id=f"gameplan.{gid_b}", type="gameplan",
                    depends_on=["subsys.render"])
    bundle = handoff.assemble(paths, config, gid_b, "0", write=False)
    md = bundle["handoff_md"]
    assert "Consumes (Cross-Gameplan)" in md
    assert "subsys.render" in md and "status: active" in md and "v1.0.0" in md
    # a status change on the OTHER axis fans a pending cross-ref into B
    config.active_gameplan = GID
    M.transition_status(paths, config, id="subsys.render", to_status="superseded")
    card = status_bundle.gameplan_card(paths.gameplan_dir(gid_b), config.focus,
                                       paths.kinds_dir)
    assert card["pending_cascades"] >= 1


def _stub_profile():
    from clauderizer.profiles.detect import Profile

    return Profile(name="generic", commands={}, baseline_test_regex="")


def _ok_runner(cmd, cwd):
    return 0, ""
