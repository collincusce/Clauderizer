"""Phase 5 dogfood, as a permanent test: two concurrent gameplans — a driven
"code" axis and a "campaign" axis — advancing INDEPENDENTLY through the whole
new stack at once: focus + portfolio (Feature 1), kinds + display-only lexicon
(Feature 2), per-kind preflight (Feature 3a), and cross-gameplan cascade
(Feature 3b). If concurrent multi-axis operation regresses, this fails.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.profiles.detect import Profile
from clauderizer.rituals import preflight


@contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def test_two_concurrent_axes_end_to_end(temp_repo):
    with _chdir(temp_repo):
        # Two axes alongside the fixture's bootstrap gameplan: a code (driven) axis
        # that steals focus, and a campaign axis created WITHOUT stealing it (O-04).
        code = ops.cz_create_gameplan("build the tool", kind="driven")["gameplan_id"]
        camp = ops.cz_create_gameplan("launch campaign", kind="campaign",
                                      focus=False)["gameplan_id"]
        assert ops.cz_status()["active_gameplan"] == code  # campaign did not steal focus

        # Portfolio: all open axes with their kinds; focus marked.
        gps = ops.cz_gameplans()["gameplans"]
        kind_by_id = {g["id"]: g["kind"] for g in gps}
        assert kind_by_id[code] == "driven" and kind_by_id[camp] == "campaign"
        assert next(g for g in gps if g["is_focus"])["id"] == code

        # Cross-gameplan: the campaign consumes a subsystem the code axis owns.
        ops.cz_upsert_entity(id="subsys.tool", type="subsystem", status="active")
        ops.cz_consumes(["subsys.tool"], gameplan_id=camp)

        # Change the shared entity from the code axis -> cascade fans out to the
        # campaign axis, which now shows a pending cascade in the portfolio.
        ops.cz_transition_status("subsys.tool", "deprecated")
        camp_card = next(g for g in ops.cz_gameplans()["gameplans"] if g["id"] == camp)
        assert camp_card["pending_cascades"] >= 1

        # Switch focus to the campaign: the digest reads in campaign vocabulary.
        ops.cz_focus(camp)
        st = ops.cz_status()
        assert st["active_gameplan"] == camp
        assert st["kind"] == "campaign" and "stage" in st["summary"]

    # Per-kind preflight: with the campaign in focus, preflight runs ITS QA gates
    # (wired in preflight.campaign.toml), not pytest; an unwired gate skips.
    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)  # focus persisted as the campaign
    (paths.clauderizer_dir / "preflight.campaign.toml").write_text(
        '[gates]\nvirality = "run-vir"\nbrand_lint = "run-bl"\n', encoding="utf-8")
    result = preflight.run(paths, config,
                           Profile(name="python", commands={"test": "pytest"}),
                           runner=lambda cmd, cwd: (0, ""))
    names = {c.name: c.status for c in result.checks}
    assert "virality" in names and "tests" not in names   # campaign gates, not pytest
    assert names["virality"] == "pass" and names["duration"] == "skip"  # unwired skips

    # The axes are independent: refocus the code axis; the campaign is untouched.
    with _chdir(temp_repo):
        ops.cz_focus(code)
        assert ops.cz_status()["active_gameplan"] == code
        still = {g["id"]: g for g in ops.cz_gameplans()["gameplans"]}
        assert still[camp]["kind"] == "campaign" and still[code]["is_focus"]
