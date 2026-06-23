"""F7: the MCP server reports clauderizer's own version in serverInfo, not the
mcp SDK's. FastMCP has no public version param, so build_server sets it on the
wrapped lowlevel server (guarded)."""

import pytest


def test_serverinfo_reports_clauderizer_version():
    pytest.importorskip("mcp")
    from clauderizer import __version__
    from clauderizer.mcp_server import build_server

    srv = build_server()
    assert srv._mcp_server.version == __version__
