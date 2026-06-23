"""The `clauderize ops` discoverability surface (F4): --list / --schema
introspection over the shared REGISTRY, and the corrected unknown-op hint."""

import json

from clauderizer import ops


def test_list_ops_covers_every_registry_op():
    listed = {e["op"] for e in ops.list_ops()}
    assert listed == set(ops.REGISTRY)  # one entry per op, none missing or extra
    for e in ops.list_ops():
        assert isinstance(e["writes"], bool)
        assert isinstance(e["required"], list)
        assert e["summary"]  # every op carries a docstring-derived summary


def test_op_schema_every_op_introspects_and_is_json_serializable():
    # L-34 seam: introspection must hold for EVERY op in the shared registry, not
    # a sampled one — a future op with an odd signature would surface right here.
    for name in ops.REGISTRY:
        sch = ops.op_schema(name)
        assert sch is not None and sch["op"] == name
        assert set(sch) == {"op", "writes", "summary", "required", "optional"}
        json.dumps(sch)  # defaults coerced → the schema round-trips through ops


def test_op_schema_required_vs_optional():
    sch = ops.op_schema("cz_add_decision")
    assert sch["required"] == ["title", "context", "decision", "consequences"]
    optional = {o["name"] for o in sch["optional"]}
    assert {"scope", "supersedes", "evidence", "gameplan_id"} <= optional
    assert sch["writes"] is True


def test_op_schema_unknown_returns_none():
    assert ops.op_schema("cz_not_a_real_op") is None


def test_unknown_op_hint_points_at_ops_list_not_tools_list():
    results, ok = ops.run_batch([{"op": "tools_list", "args": {}}])
    assert ok is False
    err = results[0]["error"]
    assert "clauderize ops --list" in err
    assert "(see tools_list)" not in err  # the dead module reference is gone
