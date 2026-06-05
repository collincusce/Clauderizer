"""The Clauderizer MCP server — the agentic, discoverable surface.

Every tool here is self-describing via its MCP schema, so an agent dropped into
a clauderized repo discovers the whole workflow from the tool list — no reading
order required. The server is stateless: it resolves the repo + config fresh on
each call and rebuilds the graph from markdown, so it's always consistent with
what's on disk even if files were edited out of band.

The ``mcp`` SDK is an optional dependency (``pip install "clauderizer[mcp]"``);
it is imported lazily so the rest of the package works without it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import mutations
from .config import Config
from .graph import cascade as cascade_mod
from .graph import index, query
from .paths import RepoPaths, find_repo_root, resolve
from .profiles import detect
from .rituals import handoff, preflight, status_bundle
from .tools_list import TOOL_NAMES


def _ctx() -> tuple[RepoPaths, Config]:
    root = find_repo_root(Path.cwd())
    paths = resolve(root)
    if not paths.config_file.exists():
        raise RuntimeError(
            "not a clauderized repo (no .clauderizer/config.toml). Run `clauderize init`."
        )
    return paths, Config.load(paths.config_file)


def _graph(paths: RepoPaths):
    return index.load_or_rebuild(paths.docs, paths.index_file)


def build_server():
    """Construct the FastMCP app. Imports the SDK lazily."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("clauderizer")

    # --- resources (read-only) ------------------------------------------------

    @mcp.resource("clauderizer://status")
    def status_resource() -> str:
        paths, config = _ctx()
        return status_bundle.render_digest(
            status_bundle.compute(paths, config), tools=TOOL_NAMES
        )

    @mcp.resource("clauderizer://procedure")
    def procedure_resource() -> str:
        paths, _ = _ctx()
        if paths.procedure_file.exists():
            return paths.procedure_file.read_text(encoding="utf-8")
        from . import assets

        return assets.procedure_text()

    @mcp.resource("clauderizer://entity/{entity_id}")
    def entity_resource(entity_id: str) -> str:
        paths, _ = _ctx()
        ent = _graph(paths).get(entity_id)
        if ent is None:
            return f"unknown entity: {entity_id}"
        return ent.path.read_text(encoding="utf-8")

    # --- read / context tools -------------------------------------------------

    @mcp.tool()
    def cz_status() -> dict:
        """Current state: active gameplan, phase table, baseline tests, pending cascades, blockers."""
        paths, config = _ctx()
        return status_bundle.compute(paths, config)

    @mcp.tool()
    def cz_next_phase_context() -> dict:
        """Assemble everything the next/current phase session needs in one call."""
        paths, config = _ctx()
        bundle = status_bundle.compute(paths, config)
        target = bundle.get("current_phase") or bundle.get("next_phase")
        if not target or not config.active_gameplan:
            return {"ok": False, "summary": "no active/next phase", "status": bundle}
        result = handoff.assemble(paths, config, config.active_gameplan, target["number"])
        result["phase"] = target
        result["status_summary"] = bundle.get("summary")
        result["next_action"] = bundle.get("next_action")
        return result

    @mcp.tool()
    def cz_graph_query(entity_id: str = "", kind: str = "lookup", transitive: bool = False) -> dict:
        """Query the Project DAG. kind = lookup | dependents | dependencies. Empty id with kind=lookup lists all entities and pin violations."""
        paths, _ = _ctx()
        g = _graph(paths)
        if not entity_id and kind == "lookup":
            return {
                "ok": True,
                "entities": [e.to_dict() for e in g.all()],
                "pin_violations": [vars(v) for v in query.pin_violations(g)],
            }
        if kind == "dependents":
            ids = query.transitive_dependents(g, entity_id) if transitive else query.dependents(g, entity_id)
            return {"ok": True, "entity": entity_id, "dependents": ids}
        if kind == "dependencies":
            return {"ok": True, "entity": entity_id, "dependencies": query.dependencies(g, entity_id)}
        ent = g.get(entity_id)
        return {"ok": ent is not None, "entity": ent.to_dict() if ent else None}

    # --- ritual tools ---------------------------------------------------------

    @mcp.tool()
    def cz_preflight() -> dict:
        """Run the pre-flight checks (git state + host test/build commands) for real."""
        paths, config = _ctx()
        profile = detect.load(config.host_profile)
        return preflight.run(paths, config, profile).to_dict()

    @mcp.tool()
    def cz_cascade(entity_id: str, transition: str, dry_run: bool = False) -> dict:
        """Walk the DAG forward from a changed entity and write a cascade report."""
        paths, config = _ctx()
        if not config.active_gameplan:
            return {"ok": False, "error": "no active gameplan for the report dir"}
        g = _graph(paths)
        reports_dir = paths.gameplan_dir(config.active_gameplan) / "_cascade-reports"
        res = cascade_mod.run(g, entity_id, transition, reports_dir, dry_run=dry_run)
        # The full report is written to disk; don't dump the whole markdown blob
        # back through the tool result (keeps the return shallow + JSON-clean).
        res.pop("report_md", None)
        return res

    @mcp.tool()
    def cz_write_handoff(phase_n: str, gameplan_id: str = "") -> dict:
        """Assemble the cumulative, self-contained handoff for a phase."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        if not gid:
            return {"ok": False, "error": "no gameplan specified or active"}
        return handoff.assemble(paths, config, gid, phase_n)

    # --- mutation tools -------------------------------------------------------

    @mcp.tool()
    def cz_create_gameplan(name: str, first_phase: str = "Bootstrap") -> dict:
        """Scaffold a new gameplan directory and make it active."""
        paths, config = _ctx()
        result = mutations.create_gameplan(paths, name, first_phase=first_phase)
        config.active_gameplan = result["gameplan_id"]
        paths.config_file.write_text(config.to_toml(), encoding="utf-8")
        return result

    @mcp.tool()
    def cz_add_phase(name: str, goal: str, depends_on_phases: list[str] | None = None,
                     gameplan_id: str = "") -> dict:
        """Add a phase to a gameplan (appends a section + status rows)."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        return mutations.add_phase(paths, gameplan_id=gid, name=name, goal=goal,
                                   depends_on_phases=depends_on_phases)

    @mcp.tool()
    def cz_add_amendment(title: str, affected_sections: str, affected_phases: str,
                         triggered_by: str, what: str, why: str, gameplan_id: str = "") -> dict:
        """Record a first-class amendment (A-NNN) to a started gameplan."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        return mutations.add_amendment(paths, gameplan_id=gid, title=title,
                                       affected_sections=affected_sections,
                                       affected_phases=affected_phases,
                                       triggered_by=triggered_by, what=what, why=why)

    @mcp.tool()
    def cz_add_decision(title: str, context: str, decision: str, consequences: str,
                        scope: str = "project", supersedes: str = "", gameplan_id: str = "") -> dict:
        """Append an ADR (D-NNN project-wide, or D-k gameplan-internal)."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        return mutations.add_decision(paths, title=title, context=context, decision=decision,
                                      consequences=consequences, scope=scope,
                                      gameplan_id=gid, supersedes=supersedes or None)

    @mcp.tool()
    def cz_add_invariant(text: str, introduced_by: str = "") -> dict:
        """Append a project invariant (INVARIANT-NN)."""
        paths, _ = _ctx()
        return mutations.add_invariant(paths, text=text, introduced_by=introduced_by or None)

    @mcp.tool()
    def cz_add_finding(
        title: str,
        severity: str,
        impact: str,
        affected: str = "",
        invariant: str = "",
        preconditions: str = "",
        root_cause: str = "",
        reproduction: str = "",
        recommendation: str = "",
        regression_tests: str = "",
        status: str = "open",
    ) -> dict:
        """Append a security finding (H-NN) to the append-only HARDENING risk tracker (a.k.a. add_risk).

        Records a structured audit finding: severity + impact are always captured;
        supply affected code, the invariant violated, exploit preconditions, root
        cause, a safe reproduction, the recommended fix, and regression tests as
        available. Findings are append-only — resolve by updating status, not deleting.
        """
        paths, _ = _ctx()
        return mutations.add_finding(
            paths, title=title, severity=severity, impact=impact,
            affected=affected, invariant=invariant, preconditions=preconditions,
            root_cause=root_cause, reproduction=reproduction,
            recommendation=recommendation, regression_tests=regression_tests,
            status=status,
        )

    @mcp.tool()
    def cz_add_lesson(text: str, category: str = "Process", gameplan_id: str = "") -> dict:
        """Add an accumulated lesson (rolls into every future handoff)."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        return mutations.add_lesson(paths, gameplan_id=gid, text=text, category=category)

    @mcp.tool()
    def cz_add_correction(phase: str, gameplan_said: str, actually: str, why: str,
                          lesson: str = "", gameplan_id: str = "") -> dict:
        """Record a divergence from the gameplan (C-NN); optionally promote a lesson."""
        paths, config = _ctx()
        gid = gameplan_id or config.active_gameplan
        return mutations.add_correction(paths, gameplan_id=gid, phase=phase,
                                        gameplan_said=gameplan_said, actually=actually,
                                        why=why, lesson=lesson or None)

    @mcp.tool()
    def cz_upsert_entity(id: str, type: str, version: str = "", status: str = "",
                         depends_on: list[str] | None = None,
                         fields: dict[str, Any] | None = None) -> dict:
        """Create or update a tracked entity doc with valid frontmatter."""
        paths, _ = _ctx()
        return mutations.upsert_entity(paths, id=id, type=type, version=version or None,
                                       status=status or None, depends_on=depends_on, fields=fields)

    @mcp.tool()
    def cz_transition_status(id: str, to_status: str, run_cascade: bool = True) -> dict:
        """Transition an entity's status; fires cascade automatically when enabled."""
        paths, config = _ctx()
        result = mutations.transition_status(paths, config, id=id, to_status=to_status,
                                             run_cascade=run_cascade)
        # Flatten the nested cascade result so the tool return stays shallow.
        casc = result.pop("cascade", None)
        if casc:
            result["cascade_report_path"] = casc.get("report_path")
            result["cascade_direct"] = casc.get("direct")
            result["cascade_transitive"] = casc.get("transitive")
        return result

    return mcp


def main(argv: list[str] | None = None) -> int:
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
