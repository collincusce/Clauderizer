"""Persistent proposal triage (D-052): stable ids + a per-user ledger that hides
dismissed/deferred modernize proposals — proven to hide the dismissed one AND keep
showing a materially-different or fresh one (L-25: a filter checked both ways)."""

from clauderizer import config as cfg
from clauderizer import modernize
from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer import proposals
from clauderizer.tools_list import TOOL_NAMES


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_proposal_id_is_stable_and_content_sensitive():
    a = proposals.proposal_id("unwired_gates", "gp1", "manifest", "bible")
    assert a == proposals.proposal_id("unwired_gates", "gp1", "manifest", "bible")   # stable
    assert a != proposals.proposal_id("unwired_gates", "gp1", "manifest")            # a gate removed -> new id
    assert a != proposals.proposal_id("unwired_gates", "gp2", "manifest", "bible")   # other gameplan -> new id
    assert a.startswith("unwired_gates:")                                            # legible prefix


def test_dismiss_hides_but_a_fresh_proposal_still_shows(temp_repo):
    paths, _ = _ctx(temp_repo)
    keep = {"kind": "unwired_gates", "id": proposals.proposal_id("unwired_gates", "gpA", "g1")}
    drop = {"kind": "no_deliverables", "id": proposals.proposal_id("no_deliverables", "gpA")}
    proposals.dismiss(paths, drop["id"])
    pending = proposals.filter_pending([keep, drop], proposals.load_ledger(paths))
    assert drop not in pending                       # dismissed -> hidden
    assert keep in pending                           # an unrelated proposal still shows (L-25)
    # a materially-changed version of the dismissed proposal is a NEW id -> re-surfaces
    changed = {"kind": "no_deliverables", "id": proposals.proposal_id("no_deliverables", "gpA", "unit-2")}
    assert changed in proposals.filter_pending([changed], proposals.load_ledger(paths))


def test_defer_snoozes_until_its_date_then_returns(temp_repo):
    paths, _ = _ctx(temp_repo)
    pid = proposals.proposal_id("unseeded_docs", "docs/TESTING.md")
    until = proposals.defer(paths, pid, days=7)["until"]
    led = proposals.load_ledger(paths)
    assert proposals.is_suppressed(led, pid, today="2026-07-16")   # before the date -> snoozed
    assert not proposals.is_suppressed(led, pid, today=until)       # on the date -> back
    assert not proposals.is_suppressed(led, pid, today="2099-01-01")


def test_dismiss_then_defer_moves_between_tables(temp_repo):
    paths, _ = _ctx(temp_repo)
    pid = proposals.proposal_id("no_deliverables", "gpZ")
    proposals.dismiss(paths, pid)
    assert pid in proposals.load_ledger(paths)["dismissed"]
    proposals.defer(paths, pid, days=3)                            # re-triage moves it, no duplication
    led = proposals.load_ledger(paths)
    assert pid in led["deferred"] and pid not in led["dismissed"]


def test_report_proposals_all_carry_stable_ids(temp_repo):
    paths, config = _ctx(temp_repo)
    M.create_gameplan(paths, "Ad Push", kind="campaign", today="2026-07-01")
    rep = modernize.report(paths, config)
    assert rep["proposals"], "a campaign gameplan should surface proposals"
    assert all(p.get("id") for p in rep["proposals"])              # every proposal is triageable


def test_cheap_report_omits_the_expensive_near_dup_scan(temp_repo):
    paths, config = _ctx(temp_repo)
    M.add_invariant(paths, text="The logo is never AI-generated; only the real brand-kit logo asset is used.")
    M.add_invariant(paths, text="logo never AI-generated — only the real brand-kit logo asset is used")
    full = modernize.report(paths, config)
    cheap = modernize.report(paths, config, cheap=True)
    assert any(p["kind"] == "near_dup_invariants" for p in full["proposals"])
    assert not any(p["kind"] == "near_dup_invariants" for p in cheap["proposals"])


def test_triage_tools_registered_as_writers():
    for name in ("cz_dismiss_proposal", "cz_defer_proposal"):
        assert name in TOOL_NAMES
        assert name in ops.REGISTRY
        assert ops.REGISTRY[name].writes is True


def test_init_gitignores_the_per_user_ledger(empty_python_repo):
    from clauderizer.scaffold.init import init
    init(empty_python_repo, spawn_test=False)
    assert ".clauderizer/proposals.local.toml" in \
        (empty_python_repo / ".gitignore").read_text(encoding="utf-8")


# --- Phase 2: digest surfacing + terse upgrade CLI -------------------------------

def _fresh_campaign(repo):
    paths = P.resolve(repo)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign", today="2026-07-01")["gameplan_id"]
    config = cfg.Config.load(paths.config_file)
    config.active_gameplan = gid
    return paths, config


def test_digest_surfaces_pending_proposal_count(temp_repo):
    from clauderizer.rituals import status_bundle as S
    paths, config = _fresh_campaign(temp_repo)
    bundle = S.compute(paths, config)
    assert bundle.get("pending_proposals", 0) >= 1
    assert "awaiting triage" in S.render_digest(bundle)          # surfaced (D-052)


def test_digest_goes_quiet_once_all_proposals_triaged(temp_repo):
    from clauderizer.rituals import status_bundle as S
    paths, config = _fresh_campaign(temp_repo)
    for p in modernize.report(paths, config, cheap=True)["proposals"]:
        proposals.dismiss(paths, p["id"])                        # triage them all
    bundle = S.compute(paths, config)
    assert not bundle.get("pending_proposals")                   # other direction (L-25)
    assert "awaiting triage" not in S.render_digest(bundle)


def test_digest_pending_line_rides_the_single_digest(temp_repo):
    # INVARIANT-08: the nudge is part of the one digest string, not a 2nd injection
    from clauderizer.rituals import status_bundle as S
    paths, config = _fresh_campaign(temp_repo)
    digest = S.render_digest(S.compute(paths, config))
    assert digest.count("[Clauderizer]") <= 1                    # one header, one injection


def test_upgrade_cli_is_terse(temp_repo, monkeypatch, capsys):
    from clauderizer import cli
    _fresh_campaign(temp_repo)
    monkeypatch.chdir(temp_repo)
    assert cli.main(["upgrade"]) == 0
    out = capsys.readouterr().out
    assert "advisory proposal(s) awaiting triage" in out         # count + pointer
    assert "clauderizer-modernize skill" in out
    assert "record each execution unit" not in out              # NOT the full proposal wall
