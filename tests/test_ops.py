"""clauderize ops + the shared registry (L-05, agent-autonomy D2).

The contract under test: op names and schemas ARE the tool names and schemas
(one registry, two transports), batches report per-op results without
aborting, the CLI's exit codes are meaningful, and every write op — including
the non-mutation-backed ones (cascade reports, handoff regeneration) —
serializes on the H-05 write lock.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager

import pytest

from clauderizer import cli, locking, ops
from clauderizer import paths as P
from clauderizer.tools_list import TOOL_NAMES

GID = "2026-05-01-bootstrap"


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _foreign_lock(paths):
    """A fresh-looking lock owned by nobody alive."""
    lock = paths.write_lock_file
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(
        json.dumps({"pid": 999999, "host": "elsewhere",
                    "since": "2026-01-01T00:00:00+00:00",
                    "ts": time.time(), "nonce": "f" * 32}),
        encoding="utf-8",
    )


# --- the registry is the tool surface ------------------------------------------


def test_registry_is_exactly_the_tool_surface():
    assert list(ops.REGISTRY) == TOOL_NAMES  # 42/42, same names, same order — no drift
    for name, spec in ops.REGISTRY.items():
        assert spec.fn.__name__ == name  # op names ARE the tool names
        assert spec.fn.__doc__  # every op self-describes


def test_no_op_dispatch_signature_drift():
    """O-08 guard: every keyword a cz_* op passes to an engine function
    (mutations.*, handoff.*, preflight.*, cascade.*, status_bundle.*) must be a
    REAL parameter of that function. The historical bug was exactly this drift —
    cz_add_amendment passing `rationale` when the impl wanted triggered_by/what/why,
    and cz_add_finding mismatched — silently producing ok:false at call time. This
    static-checks the op<->engine contract so it cannot rot again."""
    import ast
    import inspect

    from clauderizer import mutations, telemetry
    from clauderizer.graph import cascade as cascade_mod
    from clauderizer.graph import index, query
    from clauderizer.rituals import handoff, preflight, status_bundle

    modules = {
        "mutations": mutations, "cascade_mod": cascade_mod, "index": index,
        "query": query, "handoff": handoff, "preflight": preflight,
        "status_bundle": status_bundle, "telemetry": telemetry,
    }
    tree = ast.parse(inspect.getsource(ops))
    violations = []
    for fdef in tree.body:
        if not (isinstance(fdef, ast.FunctionDef) and fdef.name.startswith("cz_")):
            continue
        for node in ast.walk(fdef):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)):
                continue
            mod = modules.get(f.value.id)
            target = getattr(mod, f.attr, None) if mod else None
            if not callable(target):
                continue
            sig = inspect.signature(target)
            if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
                continue  # **kwargs accepts anything
            valid = set(sig.parameters)
            for kw in node.keywords:
                if kw.arg and kw.arg not in valid:
                    violations.append(
                        f"{fdef.name}() -> {f.value.id}.{f.attr}(): unknown kwarg '{kw.arg}'")
    assert not violations, "op<->engine signature drift (O-08):\n" + "\n".join(violations)


def test_mcp_registers_the_registry_functions(temp_repo):
    pytest.importorskip("mcp")
    import asyncio

    from clauderizer.mcp_server import build_server

    with _chdir(temp_repo):
        server = build_server()
        tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == set(TOOL_NAMES)
    # Schema spot-check: derived from the same function object the CLI executes.
    add_lesson = next(t for t in tools if t.name == "cz_add_lesson")
    props = add_lesson.inputSchema["properties"]
    assert set(props) == {"text", "category", "gameplan_id", "evidence"}
    assert add_lesson.inputSchema.get("required") == ["text"]  # evidence is optional (D-017)


def test_ops_write_matches_mcp_write(temp_repo, tmp_path):
    """The same write through both transports produces the same payload."""
    pytest.importorskip("mcp")
    import asyncio

    from clauderizer.mcp_server import build_server

    twin = tmp_path / "twin"
    shutil.copytree(temp_repo, twin)
    with _chdir(temp_repo):
        results, all_ok = ops.run_batch(
            [{"op": "cz_add_lesson", "args": {"text": "parity lesson", "gameplan_id": GID}}]
        )
    with _chdir(twin):
        server = build_server()
        res = asyncio.run(server.call_tool(
            "cz_add_lesson", {"text": "parity lesson", "gameplan_id": GID}))
        mcp_result = res[1] if isinstance(res, tuple) else json.loads(res[0].text)
    assert all_ok and results[0]["ok"]
    ops_result = results[0]["result"]
    for key in ("ok", "number", "summary"):
        assert ops_result[key] == mcp_result[key]


def test_ops_read_matches_mcp_read(temp_repo):
    pytest.importorskip("mcp")
    import asyncio

    from clauderizer.mcp_server import build_server

    with _chdir(temp_repo):
        results, _ = ops.run_batch([{"op": "cz_status", "args": {}}])
        server = build_server()
        res = asyncio.run(server.call_tool("cz_status", {}))
        mcp_result = res[1] if isinstance(res, tuple) else json.loads(res[0].text)
    ops_result = results[0]["result"]
    assert ops_result["active_gameplan"] == mcp_result["active_gameplan"] == GID
    assert ops_result["current_phase"] == mcp_result["current_phase"]


# --- batch semantics -------------------------------------------------------------


def test_run_batch_continues_after_failures(temp_repo):
    with _chdir(temp_repo):
        results, all_ok = ops.run_batch([
            {"op": "cz_nonexistent", "args": {}},
            {"op": "cz_add_lesson", "args": {"text": "after a failure", "gameplan_id": GID}},
            {"op": "cz_add_lesson", "args": {"text": "x", "gameplan_id": GID, "bogus": 1}},
        ])
    assert [r["ok"] for r in results] == [False, True, False]
    assert not all_ok
    assert "unknown op" in results[0]["error"]
    assert "bad args" in results[2]["error"]
    # the middle write really landed
    idx = temp_repo / "docs" / "gameplans" / GID / "CHAT-HANDOFF-INDEX.md"
    assert "after a failure" in idx.read_text(encoding="utf-8")


def test_run_batch_counts_tool_level_failure(temp_repo):
    """An op returning {"ok": false} (validation) fails the batch verdict."""
    with _chdir(temp_repo):
        results, all_ok = ops.run_batch(
            [{"op": "cz_resolve_finding", "args": {"finding_id": "H-99"}}]
        )
    assert not all_ok and not results[0]["ok"]
    assert results[0]["result"]["ok"] is False


# --- the CLI verb ------------------------------------------------------------------


def test_cli_ops_file_executes_and_writes(temp_repo, tmp_path, capsys):
    f = tmp_path / "batch.json"
    f.write_text(json.dumps(
        [{"op": "cz_add_lesson", "args": {"text": "via cli file", "gameplan_id": GID}}]
    ), encoding="utf-8")
    with _chdir(temp_repo):
        rc = cli.main(["ops", str(f)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["ok"]
    assert out["results"][0]["result"]["number"] >= 1
    idx = temp_repo / "docs" / "gameplans" / GID / "CHAT-HANDOFF-INDEX.md"
    assert "via cli file" in idx.read_text(encoding="utf-8")


def test_cli_ops_tolerates_bom(temp_repo, tmp_path, capsys):
    """PS 5.1 writes BOM'd files; the batch reader must not choke (utf-8-sig)."""
    f = tmp_path / "bom.json"
    f.write_bytes(b"\xef\xbb\xbf" + json.dumps([{"op": "cz_status", "args": {}}]).encode())
    with _chdir(temp_repo):
        rc = cli.main(["ops", str(f)])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["ok"]


def test_cli_ops_stdin_single_op(temp_repo, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"op": "cz_status", "args": {}})))
    with _chdir(temp_repo):
        rc = cli.main(["ops", "-"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["result"]["active_gameplan"] == GID


def test_cli_ops_exit_codes(temp_repo, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    failing = tmp_path / "failing.json"
    failing.write_text(json.dumps([{"op": "cz_bogus", "args": {}}]), encoding="utf-8")
    with _chdir(temp_repo):
        assert cli.main(["ops", str(bad)]) == 2  # unreadable batch
        assert cli.main(["ops", str(tmp_path / "missing.json")]) == 2
        assert cli.main(["ops", str(failing)]) == 1  # readable batch, failed op
    capsys.readouterr()


def test_cli_ops_cold_process(temp_repo, tmp_path):
    """The true MCP-less invocation: a fresh interpreter, file in, JSON out."""
    f = tmp_path / "cold.json"
    f.write_text(json.dumps([{"op": "cz_status", "args": {}}]), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "clauderizer", "ops", str(f)],
                       cwd=temp_repo, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["ok"] and out["results"][0]["result"]["active_gameplan"] == GID


# --- write ops serialize on the H-05 lock -------------------------------------------


def test_non_mutation_writes_take_the_lock(temp_repo, monkeypatch):
    """cascade reports + handoff regeneration write outside mutations.* — a held
    foreign lock must block them too (the residue Phase 0 deferred)."""
    paths = P.resolve(temp_repo)
    _foreign_lock(paths)
    monkeypatch.setattr(locking, "DEFAULT_ACQUIRE_TIMEOUT", 0.2)
    with _chdir(temp_repo):
        results, all_ok = ops.run_batch([
            {"op": "cz_cascade",
             "args": {"entity_id": "subsys.calc-engine", "transition": "lock test"}},
            {"op": "cz_write_handoff", "args": {"phase_n": "1", "gameplan_id": GID}},
        ])
    assert not all_ok
    assert all("LockHeld" in r["error"] for r in results)


def test_cascade_dry_run_stays_lock_free(temp_repo, monkeypatch):
    """Dry runs read only — they must not block on a writer (L-03)."""
    paths = P.resolve(temp_repo)
    _foreign_lock(paths)
    monkeypatch.setattr(locking, "DEFAULT_ACQUIRE_TIMEOUT", 0.2)
    with _chdir(temp_repo):
        results, all_ok = ops.run_batch([
            {"op": "cz_cascade",
             "args": {"entity_id": "subsys.calc-engine", "transition": "dry", "dry_run": True}},
        ])
    assert all_ok and results[0]["ok"]


def test_baseline_refresh_skips_not_fails_under_contention(temp_repo, monkeypatch):
    """Preflight's one tracked write yields under contention instead of failing
    the ritual — the value self-heals on the next green run."""
    from clauderizer import config as cfg
    from clauderizer.rituals import preflight as pf

    paths = P.resolve(temp_repo)
    config = cfg.Config.load(paths.config_file)
    idx = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    idx.write_text(idx.read_text(encoding="utf-8")
                   + "\n**Current baseline test count**: 100\n", encoding="utf-8")

    _foreign_lock(paths)
    monkeypatch.setattr(locking, "DEFAULT_ACQUIRE_TIMEOUT", 0.2)
    assert pf._write_back_baseline(paths, config, "123") is None  # skipped, no raise
    assert "**Current baseline test count**: 100" in idx.read_text(encoding="utf-8")

    paths.write_lock_file.unlink()
    assert pf._write_back_baseline(paths, config, "123") == "100"  # heals when free
    assert "**Current baseline test count**: 123" in idx.read_text(encoding="utf-8")
