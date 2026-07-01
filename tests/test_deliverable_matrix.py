"""Deliverable-matrix campaigns (gameplan 2026-07-01, decision D2).

Deliverables are tracked entities (type=deliverable, gameplan field) moving
through the kind's [lifecycle] statuses; the board renders in detail views only
and the digest carries at most one rollup line — a repo without deliverables
behaves byte-identically to 1.3.1.
"""

from clauderizer import config as cfg
from clauderizer import kinds
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import status_bundle


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_campaign_kind_has_lifecycle_driven_and_loop_do_not():
    assert kinds.resolve("campaign").lifecycle == [
        "concept", "spec-approved", "produced", "assembled", "qa", "shipped"]
    assert kinds.resolve("driven").lifecycle == []
    assert kinds.resolve("loop").lifecycle == []


def test_deliverables_for_and_matrix_render(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign",
                            today="2026-07-01")["gameplan_id"]
    M.upsert_entity(paths, id="deliv.flagship-film", type="deliverable",
                    status="produced", fields={"gameplan": gid})
    M.upsert_entity(paths, id="deliv.pillar-short-1", type="deliverable",
                    status="concept", fields={"gameplan": gid})
    M.upsert_entity(paths, id="deliv.other", type="deliverable",
                    status="concept", fields={"gameplan": "some-other-campaign"})
    delivs = status_bundle.deliverables_for(paths, gid)
    assert [d["id"] for d in delivs] == ["deliv.flagship-film", "deliv.pillar-short-1"]
    md = status_bundle.deliverable_matrix_md(
        delivs, kinds.resolve("campaign").lifecycle)
    assert "| deliverable | concept |" in md
    assert md.count("●") == 2
    assert "deliv.other" not in md
    # no lifecycle -> plain list fallback
    flat = status_bundle.deliverable_matrix_md(delivs, [])
    assert "- deliv.flagship-film: produced" in flat


def test_unknown_lifecycle_status_warns_advisory_never_blocks(temp_repo):
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign",
                            today="2026-07-01")["gameplan_id"]
    res = M.upsert_entity(paths, id="deliv.card", type="deliverable",
                          status="rendering", fields={"gameplan": gid})
    assert res["ok"] and "lifecycle" in res.get("advisory", "")
    ok = M.upsert_entity(paths, id="deliv.card2", type="deliverable",
                         status="produced", fields={"gameplan": gid})
    assert "advisory" not in ok
    missing = M.upsert_entity(paths, id="deliv.card3", type="deliverable",
                              status="concept")
    assert "gameplan" in missing.get("advisory", "")


def test_transition_status_advisory_on_deliverable(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign",
                            today="2026-07-01")["gameplan_id"]
    M.upsert_entity(paths, id="deliv.film", type="deliverable", status="concept",
                    fields={"gameplan": gid})
    res = M.transition_status(paths, config, id="deliv.film",
                              to_status="uploading", run_cascade=False)
    assert res["ok"] and "lifecycle" in res.get("advisory", "")
    res2 = M.transition_status(paths, config, id="deliv.film",
                               to_status="shipped", run_cascade=False)
    assert res2["ok"] and "advisory" not in res2


def test_digest_rollup_line_only_with_deliverables(temp_repo):
    paths, config = _ctx(temp_repo)
    before = status_bundle.render_digest(status_bundle.compute(paths, config))
    assert "Deliverables:" not in before  # untouched repo: no new line (INVARIANT-07)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign",
                            today="2026-07-01")["gameplan_id"]
    config.active_gameplan = gid
    M.upsert_entity(paths, id="deliv.a", type="deliverable", status="shipped",
                    fields={"gameplan": gid})
    M.upsert_entity(paths, id="deliv.b", type="deliverable", status="concept",
                    fields={"gameplan": gid})
    digest = status_bundle.render_digest(status_bundle.compute(paths, config))
    assert "Deliverables: 1/2 shipped." in digest
