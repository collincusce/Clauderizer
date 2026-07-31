"""F7: the MCP server reports clauderizer's own version in serverInfo, not the
mcp SDK's. Neither SDK major exposes a public version param, so build_server
sets it on the wrapped lowlevel server (guarded) — an attribute named
``_mcp_server`` on mcp 1.x and ``_lowlevel_server`` on 2.x (H-31)."""

import pytest

from _mcp_compat import mcp_lowlevel


def test_serverinfo_reports_clauderizer_version():
    pytest.importorskip("mcp")
    from clauderizer import __version__
    from clauderizer.mcp_server import build_server

    srv = build_server()
    assert mcp_lowlevel(srv).version == __version__
