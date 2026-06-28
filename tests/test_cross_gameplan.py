"""Phase 4 of concurrent-multi-axis-gameplans: cross-gameplan dependencies.

A gameplan.<gid> node (cz_consumes) declares cross-gameplan consumption; the
cascade then walks ACROSS gameplans, fanning a pending cross-ref into a non-focus
consuming gameplan so its own cascade_hygiene catches it. The handoff surfaces a
Consumes section. The mechanism is kind-agnostic (proven here between driven
gameplans).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer.graph import index
from clauderizer.profiles.detect import Profile
from clauderizer.rituals import handoff, preflight, status_bundle as S

G1 = "2026-05-01-bootstrap"  # the fixture's focus gameplan


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


def _second_gameplan(paths: P.RepoPaths, name="second axis") -> str:
    # mutations.create_gameplan does not steal focus, so focus stays on G1.
    return M.create_gameplan(paths, name, today="2026-06-02")["gameplan_id"]


# --- cz_consumes ---------------------------------------------------------------


def test_cz_consumes_creates_node_and_unions(temp_repo):
    paths, _ = _pc(temp_repo)
    g2 = _second_gameplan(paths)
    with _chdir(temp_repo):
        r1 = ops.cz_consumes(["subsys.auth"], gameplan_id=g2)
        assert r1["ok"] and r1["consumes"] == ["subsys.auth"]
        r2 = ops.cz_consumes(["subsys.calc-engine", "subsys.auth"], gameplan_id=g2)
        assert r2["consumes"] == ["subsys.auth", "subsys.calc-engine"]  # union, stable
    node = index.build(paths.docs).get(f"gameplan.{g2}")
    assert node is not None and node.type == "gameplan"
    assert {str(p.target) for p in node.depends_on} == {"subsys.auth", "subsys.calc-engine"}


# --- cascade fan-out -----------------------------------------------------------


def test_manual_cascade_fans_out_to_consumer(temp_repo):
    paths, _ = _pc(temp_repo)  # focus = G1
    g2 = _second_gameplan(paths)
    with _chdir(temp_repo):
        ops.cz_consumes(["subsys.auth"], gameplan_id=g2)
        res = ops.cz_cascade("subsys.auth", "manual edit")
    assert res["ok"] and len(res.get("cross_gameplan_refs", [])) == 1
    # the consuming gameplan now has a pending cascade it must resolve
    assert len(S.pending_cascades(paths.gameplan_dir(g2) / "_cascade-reports")) == 1
    # the focus gameplan got its own normal report too
    assert S.pending_cascades(paths.gameplan_dir(G1) / "_cascade-reports")


def test_transition_status_auto_cascade_fans_out(temp_repo):
    paths, _ = _pc(temp_repo)
    g2 = _second_gameplan(paths)
    with _chdir(temp_repo):
        ops.cz_consumes(["subsys.auth"], gameplan_id=g2)
        ops.cz_transition_status("subsys.auth", "deprecated")  # fires cascade
    assert len(S.pending_cascades(paths.gameplan_dir(g2) / "_cascade-reports")) >= 1


def test_cross_ref_caught_by_consumers_cascade_hygiene(temp_repo):
    paths, _ = _pc(temp_repo)
    g2 = _second_gameplan(paths)
    with _chdir(temp_repo):
        ops.cz_consumes(["subsys.auth"], gameplan_id=g2)
        ops.cz_cascade("subsys.auth", "edit")
    # preflight for the consumer (focus it) surfaces the pending cross-ref
    config = cfg.Config.load(paths.config_file)
    config.focus = g2
    config.preflight_checks = ["cascade_hygiene"]
    result = preflight.run(paths, config, Profile(name="generic", commands={}),
                           runner=lambda cmd, cwd: (0, ""))
    ch = next(c for c in result.checks if c.name == "cascade_hygiene")
    assert ch.status == "fail" and result.passed is False


def test_no_consumer_no_fanout(temp_repo):
    paths, _ = _pc(temp_repo)
    _second_gameplan(paths)  # exists but declares no consumption
    with _chdir(temp_repo):
        res = ops.cz_cascade("subsys.auth", "edit")
    assert "cross_gameplan_refs" not in res  # nothing consumes it -> no fan-out


# --- handoff Consumes section --------------------------------------------------


def test_handoff_renders_consumes_section(temp_repo):
    paths, config = _pc(temp_repo)
    g2 = _second_gameplan(paths)
    with _chdir(temp_repo):
        ops.cz_consumes(["subsys.auth"], gameplan_id=g2)
    md = handoff.assemble(paths, config, g2, "0", write=False)["handoff_md"]
    assert "## Consumes (Cross-Gameplan)" in md
    assert "subsys.auth" in md
    assert "project invariants" in md.lower()  # scoping is documented inline


def test_handoff_no_consumes_section_without_node(temp_repo):
    paths, config = _pc(temp_repo)
    g2 = _second_gameplan(paths)
    md = handoff.assemble(paths, config, g2, "0", write=False)["handoff_md"]
    assert "Consumes (Cross-Gameplan)" not in md  # back-compat: only when declared
