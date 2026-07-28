"""The per-call cz_state stamp: INVARIANT-10's five bounds, pinned (D-072).

Figures only (whitelist ratchet), change-triggered (in-memory last-emission),
advisory and isolated in both directions, byte-bounded (no approval artifact
hashing on the stamp path), and silent-by-default (env-armed experiment until
the D-064 matrix). The liveness core: an agent's own writes move the figures
between two calls in the same session.
"""

from __future__ import annotations

import pytest

from clauderizer import config as cfg
from clauderizer import contract, ops, state_stamp
from clauderizer import paths as P


@pytest.fixture
def repo(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    state_stamp._reset()
    return temp_repo


def _armed(monkeypatch):
    monkeypatch.setenv(state_stamp.ARM_ENV, "1")


# --- bound 5: silent by default ----------------------------------------------

def test_dormant_by_default_no_cz_state_anywhere(repo):
    res = ops.run_op("cz_list_open_items")
    assert "cz_state" not in res


def test_armed_attaches_figures(repo, monkeypatch):
    _armed(monkeypatch)
    res = ops.run_op("cz_list_open_items")
    assert "cz_state" in res
    stamp = res["cz_state"]
    assert stamp["gameplan"] == "2026-05-01-bootstrap"
    assert "revision" in stamp or "phase" in stamp


# --- bound 1: figures only, whitelist-ratcheted -------------------------------

def test_whitelist_ratchet_every_key_is_legal(repo, monkeypatch):
    _armed(monkeypatch)
    stamp = ops.run_op("cz_list_open_items")["cz_state"]
    assert set(stamp) <= state_stamp.FIGURE_KEYS
    # The ratchet itself: growing the legal set is a FORCED JUDGMENT here.
    assert state_stamp.FIGURE_KEYS == frozenset({
        "gameplan", "phase", "phase_status", "blockers", "open_items",
        "exit_criteria", "pending_cascades", "revision"})


def test_no_prose_ever(repo, monkeypatch):
    _armed(monkeypatch)
    stamp = ops.run_op("cz_list_open_items")["cz_state"]
    for v in stamp.values():
        assert not isinstance(v, str) or len(v) <= 80


# --- bound 2: change-triggered ------------------------------------------------

def test_unchanged_figures_are_not_reattached(repo, monkeypatch):
    _armed(monkeypatch)
    first = ops.run_op("cz_list_open_items")
    assert "cz_state" in first
    second = ops.run_op("cz_list_open_items")
    assert "cz_state" not in second          # nothing moved -> no notice


def test_own_write_moves_the_figures_within_one_session(repo, monkeypatch):
    _armed(monkeypatch)
    base = ops.run_op("cz_list_open_items")["cz_state"]
    res = ops.run_op("cz_add_open_item", text="a stamped question")
    # the write itself already carries the moved figures...
    moved = res.get("cz_state") or ops.run_op("cz_list_open_items")["cz_state"]
    assert moved["open_items"] == base["open_items"] + 1


def test_excluded_superset_ops_never_carry_the_stamp(repo, monkeypatch):
    _armed(monkeypatch)
    state_stamp._reset()
    res = ops.run_op("cz_status")
    assert "cz_state" not in res


# --- bounds 3+isolation: both directions --------------------------------------

def test_stamp_failure_never_alters_the_op_result(repo, monkeypatch):
    _armed(monkeypatch)

    def _boom(*a, **k):
        raise RuntimeError("stamp exploded")

    monkeypatch.setattr(state_stamp, "emit", _boom)
    res = ops.run_op("cz_list_open_items")
    assert res["ok"] is True and "cz_state" not in res


def test_op_exception_is_never_masked_by_the_stamp(repo, monkeypatch):
    _armed(monkeypatch)
    spec = ops.REGISTRY["cz_list_open_items"]

    def _raise(**k):
        raise RuntimeError("op exploded")

    wrapped = ops._journaled(ops._stamped("cz_list_open_items", _raise), True)
    with pytest.raises(RuntimeError, match="op exploded"):
        wrapped()
    assert spec.fn is not wrapped            # registry untouched by the probe


def test_failed_op_result_still_flows_unchanged(repo, monkeypatch):
    _armed(monkeypatch)
    res = ops.run_op("cz_transition_phase", phase_n="1", to_status="nonsense")
    assert res["ok"] is False                # refusal path unaffected


# --- bound 4: byte-bounded — no approval recompute ----------------------------

def test_exit_criteria_figure_never_calls_the_approval_path(repo, monkeypatch):
    from clauderizer.rituals import status_bundle

    def _forbidden(*a, **k):
        raise AssertionError("stamp path must not recompute approval state")

    monkeypatch.setattr(status_bundle, "exit_criteria", _forbidden)
    paths = P.resolve(repo)
    stamp = state_stamp.compute_stamp(paths, cfg.Config.load(paths.config_file))
    assert stamp is not None                 # computed without the hashing path


# --- resilience + contract ----------------------------------------------------

def test_no_focus_gameplan_yields_figures_without_phase_claims(repo):
    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    config.active_gameplan = ""
    stamp = state_stamp.compute_stamp(paths, config)
    assert stamp is not None and stamp.get("gameplan") is None
    assert "phase" not in stamp and "open_items" not in stamp


def test_contract_minor_bumped_additively():
    assert contract.CONTRACT_SCHEMA_VERSION == "1.1"
