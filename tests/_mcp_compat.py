"""Test-side compatibility across both mcp SDK majors (H-31).

The engine behaves identically on mcp 1.x and 2.x — only the SDK's return
shapes and internal attribute names moved. Normalizing here keeps the tests
asserting Clauderizer's behaviour instead of one SDK major's data model.
"""

from __future__ import annotations


def mcp_call_content(result):
    """Content blocks from a call_tool result.

    1.x returns a subscriptable sequence; 2.0 returns a ``CallToolResult`` whose
    blocks live on ``.content``.
    """
    return getattr(result, "content", result)


def mcp_lowlevel(server):
    """The wrapped lowlevel server — ``_mcp_server`` on 1.x, ``_lowlevel_server``
    on 2.x."""
    for attr in ("_mcp_server", "_lowlevel_server"):
        s = getattr(server, attr, None)
        if s is not None:
            return s
    raise AttributeError("no lowlevel server attribute on this SDK")
