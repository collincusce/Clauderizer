"""Drive the real MCP tools in-process via FastMCP's call_tool.

These run the same code path Claude Code would, against a tmp copy of the
fixture repo. The engine resolves the repo from cwd, so we chdir into the copy.
"""

import asyncio
import json
import os
from contextlib import contextmanager

import pytest

pytest.importorskip("mcp")

from clauderizer.mcp_server import build_server  # noqa: E402


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _call(server, name, args=None):
    # FastMCP versions differ: success may return (content, structured) OR just a
    # list of content blocks. Be tolerant and always hand back the parsed dict.
    res = asyncio.run(server.call_tool(name, args or {}))
    if isinstance(res, tuple):
        return res[1]
    return json.loads(res[0].text)


def test_all_tools_are_discoverable(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        names = {t.name for t in asyncio.run(server.list_tools())}
    expected = {
        "cz_status", "cz_next_phase_context", "cz_graph_query", "cz_preflight",
        "cz_cascade", "cz_write_handoff", "cz_upsert_entity", "cz_transition_status",
        "cz_add_decision", "cz_add_invariant", "cz_add_finding", "cz_add_lesson",
        "cz_add_correction", "cz_create_gameplan", "cz_add_phase", "cz_add_amendment",
    }
    assert expected <= names


def test_cz_status_tool(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_status")
    assert result["active_gameplan"] == "2026-05-01-bootstrap"
    assert result["current_phase"]["number"] == "1"


def test_cz_graph_query_dependents(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_graph_query",
                       {"entity_id": "subsys.calc-engine", "kind": "dependents"})
    assert result["dependents"] == ["feat.legacy", "subsys.auth"]


def test_cz_graph_query_lists_all_and_pin_violations(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_graph_query")
    ids = {e["id"] for e in result["entities"]}
    assert "subsys.auth" in ids
    assert any(v["dependent"] == "feat.legacy" for v in result["pin_violations"])


def test_cz_add_decision_then_query(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        added = _call(server, "cz_add_decision", {
            "title": "Adopt X", "context": "c", "decision": "d", "consequences": "e",
        })
        assert added["id"] == "D-002"


def test_cz_add_finding(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        added = _call(server, "cz_add_finding", {
            "title": "Sample finding via MCP", "severity": "CRITICAL",
            "impact": "example impact text", "invariant": "INVARIANT-01",
        })
    assert added["id"] == "H-01"
    text = (temp_repo / "docs" / "HARDENING.md").read_text(encoding="utf-8")
    assert "### H-01 — Sample finding via MCP" in text
    assert "**Severity**: CRITICAL" in text


def test_cz_transition_status_fires_cascade(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_transition_status",
                       {"id": "subsys.auth", "to_status": "completed"})
    assert result["to"] == "completed"
    assert result["cascade_direct"] == ["feat.login"]


def test_cz_cascade_writes_and_returns_shallow(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_cascade",
                       {"entity_id": "subsys.auth", "transition": "active -> completed"})
    assert result["direct"] == ["feat.login"]
    assert "report_md" not in result  # trimmed; full report is on disk
    assert result["written"] is True


def test_cz_next_phase_context(temp_repo):
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_next_phase_context")
    # fixture has phase 1 IN PROGRESS
    assert result["phase"]["number"] == "1"
    assert result["lessons_rolled_up"] == 3


def test_cz_preflight_runs(temp_repo):
    # No git in the fixture copy -> git checks skip, tests skip cleanly; the point
    # is the tool executes and returns a structured verdict.
    with _chdir(temp_repo):
        server = build_server()
        result = _call(server, "cz_preflight")
    assert "checks" in result and "passed" in result


# --- P3 prompts + P7 bootstrap, exercised through the real server (P9 criterion 2) ---

def test_server_serves_prompts(temp_repo):
    # the Tier-3 slash-command prompts must be discoverable on a prompt-host; the
    # launched-server stdio round-trip confirmed this live, this pins it in CI
    with _chdir(temp_repo):
        server = build_server()
        prompts = asyncio.run(server.list_prompts())
        names = {p.name for p in prompts}
        assert {"cz-status", "cz-next-phase"} <= names
        got = asyncio.run(server.get_prompt("cz-status", {}))
        text = got.messages[0].content.text
    assert "[Clauderizer]" in text                     # the live digest, via the prompt


def test_server_bootstrap_injects_only_on_hookless_host(temp_repo, monkeypatch):
    from clauderizer import mcp_server, session
    with _chdir(temp_repo):
        server = build_server()
        try:
            # hook-less host (cursor): the first non-status tool call carries the note
            monkeypatch.setattr(mcp_server, "_host_target", lambda: "cursor")
            session.reset()
            result = _call(server, "cz_graph_query")
            assert "clauderizer_status" in result
            assert "cz_status" in result["clauderizer_status"]
            # hook host (claude-code): the hook delivers; the server stays silent
            monkeypatch.setattr(mcp_server, "_host_target", lambda: "claude-code")
            session.reset()
            result2 = _call(server, "cz_graph_query")
            assert "clauderizer_status" not in result2
        finally:
            session.reset()                            # don't leak the signal to other tests
