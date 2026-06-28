"""Phase 1 of concurrent-multi-axis-gameplans: focus + the derived portfolio.

Covers the new behavior the back-compat golden gate (test_back_compat_focus.py)
does NOT: switching focus, the multi-open portfolio, the cz_focus / cz_gameplans
ops, and creating a second axis without stealing focus (O-04).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.rituals import status_bundle as S

GID = "2026-05-01-bootstrap"  # the fixture's single gameplan (focus by default)


@contextmanager
def _chdir(path: Path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _pc(repo: Path):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- the derived portfolio / open-set -----------------------------------------


def test_portfolio_marks_focus_and_excludes_complete(temp_repo):
    paths, config = _pc(temp_repo)
    # mutations.create_gameplan does NOT steal focus (only the ops layer does), so
    # this builds a genuine 2-open repo with focus still on GID.
    g2 = M.create_gameplan(paths, "second axis", today="2026-06-02")["gameplan_id"]
    cards = S.portfolio(paths, config)
    assert {c["id"] for c in cards} == {GID, g2}
    assert cards[0]["is_focus"] and cards[0]["id"] == GID  # focus sorts first
    assert all(c["open"] for c in cards)

    # finish the second gameplan -> it drops out of the open portfolio
    M.transition_phase(paths, gameplan_id=g2, phase_n="0", to_status="complete",
                       today="2026-06-02")
    assert {c["id"] for c in S.portfolio(paths, config)} == {GID}
    allc = {c["id"]: c for c in S.portfolio(paths, config, include_closed=True)}
    assert allc[g2]["open"] is False and allc[g2]["lifecycle"] == "complete"


def test_portfolio_reads_kind_from_header(temp_repo):
    paths, config = _pc(temp_repo)
    g2 = M.create_gameplan(paths, "loopy", kind="loop", today="2026-06-02")["gameplan_id"]
    card = next(c for c in S.portfolio(paths, config) if c["id"] == g2)
    assert card["kind"] == "loop"


# --- digest expansion ----------------------------------------------------------


def test_digest_expands_only_with_multiple_open(temp_repo):
    paths, config = _pc(temp_repo)
    assert "Portfolio (" not in S.render_digest(S.compute(paths, config))  # 1 open
    M.create_gameplan(paths, "second axis", today="2026-06-02")
    digest = S.render_digest(S.compute(paths, config))
    assert "Portfolio (2 open):" in digest
    assert "★" in digest  # focus is marked


def test_no_focus_digest_still_surfaces_open_gameplans(temp_repo):
    paths, config = _pc(temp_repo)
    M.create_gameplan(paths, "second axis", today="2026-06-02")
    config.focus = None
    digest = S.render_digest(S.compute(paths, config))
    assert "No focus set" in digest and "cz_focus" in digest


# --- the ops -------------------------------------------------------------------


def test_cz_focus_switches_and_retargets_default_ops(temp_repo):
    paths, _ = _pc(temp_repo)
    g2 = M.create_gameplan(paths, "second axis", today="2026-06-02")["gameplan_id"]
    with _chdir(temp_repo):
        res = ops.cz_focus(gameplan_id=g2)
        assert res["ok"] and res["focus"] == g2 and res["previous_focus"] == GID
        # a default-target op (no gameplan_id) now resolves to the new focus
        assert ops.cz_status()["active_gameplan"] == g2
    assert cfg.Config.load(P.resolve(temp_repo).config_file).focus == g2  # persisted


def test_cz_focus_empty_reports_current(temp_repo):
    with _chdir(temp_repo):
        res = ops.cz_focus()
        assert res["ok"] and res["focus"] == GID
        assert isinstance(res["gameplans"], list)


def test_cz_focus_unknown_errors(temp_repo):
    with _chdir(temp_repo):
        res = ops.cz_focus(gameplan_id="2099-01-01-nope")
        assert not res["ok"] and "no gameplan" in res["error"]


def test_cz_focus_warns_on_closed(temp_repo):
    paths, _ = _pc(temp_repo)
    g2 = M.create_gameplan(paths, "done axis", today="2026-06-02")["gameplan_id"]
    M.transition_phase(paths, gameplan_id=g2, phase_n="0", to_status="complete",
                       today="2026-06-02")
    with _chdir(temp_repo):
        res = ops.cz_focus(gameplan_id=g2)
        assert res["ok"] and "closed" in res.get("warning", "")


def test_cz_gameplans_op(temp_repo):
    paths, _ = _pc(temp_repo)
    M.create_gameplan(paths, "second axis", today="2026-06-02")
    with _chdir(temp_repo):
        res = ops.cz_gameplans()
        assert res["ok"] and res["focus"] == GID
        assert len(res["gameplans"]) == 2 and "2 open" in res["summary"]


def test_create_gameplan_focus_false_does_not_steal(temp_repo):
    with _chdir(temp_repo):
        res = ops.cz_create_gameplan("third axis", focus=False)
        assert res["ok"] and res["focused"] is False
        assert ops.cz_status()["active_gameplan"] == GID  # focus unchanged
        # default focus=True still steals
        res2 = ops.cz_create_gameplan("fourth axis")
        assert res2["focused"] is True
        assert ops.cz_status()["active_gameplan"] == res2["gameplan_id"]
