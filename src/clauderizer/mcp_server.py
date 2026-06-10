"""The Clauderizer MCP server — the agentic, discoverable surface.

Every tool here is self-describing via its MCP schema, so an agent dropped into
a clauderized repo discovers the whole workflow from the tool list — no reading
order required. The server is stateless: it resolves the repo + config fresh on
each call and rebuilds the graph from markdown, so it's always consistent with
what's on disk even if files were edited out of band.

Tool implementations live in :mod:`clauderizer.ops` (the shared registry, D2 of
agent-autonomy): this module registers those exact function objects, so the MCP
schemas derive from the same callables ``clauderize ops`` executes — the two
surfaces cannot drift.

The ``mcp`` SDK is an optional dependency (``pip install "clauderizer[mcp]"``);
it is imported lazily so the rest of the package works without it.
"""

from __future__ import annotations

import sys

from . import __version__
from .graph import index
from .ops import REGISTRY, repo_ctx
from .rituals import status_bundle
from .tools_list import TOOL_NAMES


def build_server():
    """Construct the FastMCP app. Imports the SDK lazily."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("clauderizer")

    # --- resources (read-only) ------------------------------------------------

    @mcp.resource("clauderizer://status")
    def status_resource() -> str:
        paths, config = repo_ctx()
        return status_bundle.render_digest(
            status_bundle.compute(paths, config), tools=TOOL_NAMES
        )

    @mcp.resource("clauderizer://procedure")
    def procedure_resource() -> str:
        paths, _ = repo_ctx()
        if paths.procedure_file.exists():
            return paths.procedure_file.read_text(encoding="utf-8")
        from . import assets

        return assets.procedure_text()

    @mcp.resource("clauderizer://entity/{entity_id}")
    def entity_resource(entity_id: str) -> str:
        paths, _ = repo_ctx()
        ent = index.load_or_rebuild(paths.docs, paths.index_file).get(entity_id)
        if ent is None:
            return f"unknown entity: {entity_id}"
        return ent.path.read_text(encoding="utf-8")

    # --- tools: the shared ops registry, registered verbatim -------------------
    # The op functions ARE the tool implementations — names, signatures, and
    # docstrings carry the schema, so MCP and `clauderize ops` stay identical.

    for spec in REGISTRY.values():
        mcp.tool()(spec.fn)

    return mcp


def main(argv: list[str] | None = None) -> int:
    # Answer --version/--help without touching stdin or the mcp SDK: init's and
    # doctor's spawn probes (D3) need a deterministic, fast exit-0 path that
    # proves the entry point launches — not a stdio server waiting on EOF luck.
    args = sys.argv[1:] if argv is None else argv
    if "--version" in args or "-V" in args:
        print(f"clauderizer {__version__}")
        return 0
    if "--help" in args or "-h" in args:
        print("clauderizer-mcp — launch the Clauderizer MCP server on stdio.\n"
              "Flags: --version, --help. No other arguments.")
        return 0
    try:
        server = build_server()
    except ImportError:
        print(
            "The MCP server needs the 'mcp' package. Install with:\n"
            '  pipx install "clauderizer[mcp]"   (or: pip install "clauderizer[mcp]")'
        )
        return 1
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
