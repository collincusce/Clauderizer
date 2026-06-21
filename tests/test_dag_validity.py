"""DAG integrity validation: dangling depends_on edges + cycles (Phase 2).

Deterministic, stdlib-only detection (graph/validate) surfaced advisorily through
the existing status drift channel. Per INVARIANT-05 it must never raise and never
block; these tests pin both the detection and that advisory contract.
"""
from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.graph import index, validate
from clauderizer.rituals import status_bundle


def _pc(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _graph(paths):
    return index.build(paths.docs)


# --- dangling depends_on edges ----------------------------------------------

def test_dangling_edge_detected(temp_repo):
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.x", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.missing"])
    issues = validate.validate(_graph(paths))
    assert ("subsys.x", "subsys.missing") in issues.dangling


def test_multiple_dangling_edges_all_detected(temp_repo):
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.x", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.ghost", "subsys.phantom"])
    M.upsert_entity(paths, id="subsys.y", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.ghost"])
    dangling = validate.dangling_edges(_graph(paths))
    # 100% detection on the seeded broken edges (constraints stripped to bare id).
    assert ("subsys.x", "subsys.ghost") in dangling
    assert ("subsys.x", "subsys.phantom") in dangling
    assert ("subsys.y", "subsys.ghost") in dangling
    assert dangling == sorted(dangling)  # deterministic ordering


def test_dangling_ignores_satisfied_constraint_pin(temp_repo):
    # A pin with a version constraint whose target *does* exist is not dangling.
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.core", type="subsystem", version="1.0.0",
                    status="active")
    M.upsert_entity(paths, id="subsys.x", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.core@^1.0.0"])
    dangling = validate.dangling_edges(_graph(paths))
    assert all(src != "subsys.x" for src, _ in dangling)


# --- cycles ------------------------------------------------------------------

def test_two_node_cycle_detected(temp_repo):
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.a", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.b"])
    M.upsert_entity(paths, id="subsys.b", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.a"])
    cycles = validate.cycles(_graph(paths))
    assert ["subsys.a", "subsys.b"] in cycles


def test_three_node_cycle_detected(temp_repo):
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.a", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.b"])
    M.upsert_entity(paths, id="subsys.b", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.c"])
    M.upsert_entity(paths, id="subsys.c", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.a"])
    cycles = validate.cycles(_graph(paths))
    assert ["subsys.a", "subsys.b", "subsys.c"] in cycles


def test_self_loop_detected_as_cycle(temp_repo):
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.loop", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.loop"])
    cycles = validate.cycles(_graph(paths))
    assert ["subsys.loop"] in cycles


# --- zero false positives on a valid acyclic DAG ----------------------------

def test_valid_dag_has_zero_findings(temp_repo):
    # core <- mid <- top: a clean chain, no dangling, no cycles.
    paths, _ = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.core", type="subsystem", version="1.0.0",
                    status="active")
    M.upsert_entity(paths, id="subsys.mid", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.core"])
    M.upsert_entity(paths, id="subsys.top", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.mid"])
    g = _graph(paths)
    # Restrict the assertion to the seeded subtree so unrelated fixture entities
    # can't muddy the "zero false positives on a valid DAG" claim.
    seeded = {"subsys.core", "subsys.mid", "subsys.top"}
    issues = validate.validate(g)
    assert [d for d in issues.dangling if d[0] in seeded] == []
    assert [c for c in issues.cycles if set(c) & seeded] == []


def test_canonical_fixture_dag_is_clean(sample_repo):
    # The shipped fixture DAG must itself be dangling- and cycle-free (the
    # zero-false-positive guarantee on a real, valid graph).
    g = index.build(sample_repo / "docs")
    issues = validate.validate(g)
    assert issues.dangling == []
    assert issues.cycles == []


# --- advisory contract: never raises; surfaces via drift --------------------

def test_validate_never_raises_on_arbitrary_graph():
    # A hand-built graph with both pathologies must not throw — advisory only.
    from clauderizer.graph.index import Graph
    from clauderizer.model import Entity, Pin
    from pathlib import Path

    def ent(eid, deps):
        return Entity(id=eid, type="subsystem", path=Path("x.md"),
                      depends_on=[Pin(target=t) for t in deps])

    g = Graph(entities={
        "a": ent("a", ["b", "ghost"]),
        "b": ent("b", ["a"]),
    })
    issues = validate.validate(g)  # must not raise
    assert ("a", "ghost") in issues.dangling
    assert ["a", "b"] in issues.cycles


def test_dangling_surfaces_in_status_drift(temp_repo):
    paths, config = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.x", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.missing"])
    bundle = status_bundle.compute(paths, config)
    assert any("dangling depends_on subsys.x -> subsys.missing" in w
               for w in bundle["drift"])


def test_cycle_surfaces_in_status_drift_and_digest(temp_repo):
    paths, config = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.a", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.b"])
    M.upsert_entity(paths, id="subsys.b", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.a"])
    bundle = status_bundle.compute(paths, config)
    assert any("depends_on cycle subsys.a -> subsys.b -> subsys.a" in w
               for w in bundle["drift"])
    digest = status_bundle.render_digest(bundle)
    assert "⚠ Drift: depends_on cycle subsys.a -> subsys.b -> subsys.a" in digest


def test_valid_dag_adds_no_drift_noise(temp_repo):
    # The advisory must not cry wolf: a clean added DAG yields no DAG drift line.
    paths, config = _pc(temp_repo)
    M.upsert_entity(paths, id="subsys.core", type="subsystem", version="1.0.0",
                    status="active")
    M.upsert_entity(paths, id="subsys.mid", type="subsystem", version="1.0.0",
                    status="active", depends_on=["subsys.core"])
    bundle = status_bundle.compute(paths, config)
    assert not any("dangling depends_on" in w or "depends_on cycle" in w
                   for w in bundle["drift"])
