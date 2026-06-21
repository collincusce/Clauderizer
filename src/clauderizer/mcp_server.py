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

import functools
import sys

from . import __version__, session
from .graph import index
from .ops import REGISTRY, repo_ctx
from .rituals import status_bundle
from .tools_list import TOOL_NAMES

# --- cross-host injection: write-first self-correction (P1, INVARIANT-08) -------
# On a hook-less host_target, if the agent issues a write before any status was
# delivered this session, prefix a compact status note to the result so it is not
# operating blind. On a hook host (default "claude-code") the gate is off and these
# wrappers are exact no-ops — INVARIANT-07. The signal lives in `session` (in
# memory, never persisted); this is the server seam that maintains it.

_STATUS_TOOLS = ("cz_status", "cz_next_phase_context")


def _status_summary() -> str:
    try:
        paths, config = repo_ctx()
        return str(status_bundle.compute(paths, config).get("summary") or "")
    except Exception:
        return ""


def _host_target() -> str | None:
    try:
        return repo_ctx()[1].host_target
    except Exception:
        return None


def _deliver_aware(name: str, spec):
    """Register-time wrapper maintaining the session-delivery signal. The two
    status-delivering reads mark the signal directly. For EVERY other tool — read or
    write — the server-side bootstrap (P7) attaches a compact status note to the
    FIRST call's result on a hook-less host that has not seen status yet, so the
    agent is never blind regardless of which tool it reaches for first. After that
    first call the signal is set and the wrapper stands down — so a hook host pays a
    single host-target lookup and never an injection. functools.wraps keeps the MCP
    schema identical to the bare op (INVARIANT-07)."""
    fn = spec.fn
    delivers = name in _STATUS_TOOLS

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        if delivers:
            session.mark_status_delivered()
            return fn(*args, **kwargs)
        result = fn(*args, **kwargs)
        if not session.status_delivered():
            if not session.should_inject(_host_target()):
                session.mark_status_delivered()        # hook host: the hook delivers; stand down
            elif isinstance(result, dict):
                result.setdefault("clauderizer_status", session.status_note(_status_summary()))
                session.mark_status_delivered()
            # else hook-less + non-dict result: cannot attach the note; retry next call
        return result

    return wrapped


def _prompt_cz_status() -> str:
    """Load the current Clauderizer project status — gameplan, phase, baseline,
    open items. Run this first on a host with no session hook."""
    session.mark_status_delivered()
    paths, config = repo_ctx()
    return status_bundle.render_digest(
        status_bundle.compute(paths, config), tools=TOOL_NAMES
    )


def _prompt_cz_next_phase() -> str:
    """Load the next or current phase bundle — tasks, key files, exit criteria —
    so you can begin or continue the work."""
    session.mark_status_delivered()
    return str(REGISTRY["cz_next_phase_context"].fn().get("handoff_md", ""))


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

    # --- prompts: Tier-3 user-invoked slash commands (D-034) -------------------
    # On hosts that surface MCP prompts (Cursor, Copilot, Continue, Gemini, Zed)
    # these appear as /cz-status etc. — a one-shot pull of memory into context where
    # no session hook does it. Invoking one marks status delivered so the write-first
    # self-correction and the bootstrap do not double-fire (INVARIANT-08).
    mcp.prompt(name="cz-status")(_prompt_cz_status)
    mcp.prompt(name="cz-next-phase")(_prompt_cz_next_phase)

    # --- tools: the shared ops registry, registered verbatim -------------------
    # The op functions ARE the tool implementations — names, signatures, and
    # docstrings carry the schema, so MCP and `clauderize ops` stay identical.

    for name, spec in REGISTRY.items():
        mcp.tool()(_deliver_aware(name, spec))

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
