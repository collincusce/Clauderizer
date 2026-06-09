"""The canonical list of MCP tool names, shared by the server and the hook.

Kept in one place so the SessionStart digest advertises exactly what the server
exposes.
"""

TOOL_NAMES = [
    "cz_status",
    "cz_next_phase_context",
    "cz_graph_query",
    "cz_preflight",
    "cz_cascade",
    "cz_resolve_cascade",
    "cz_write_handoff",
    "cz_upsert_entity",
    "cz_transition_status",
    "cz_add_decision",
    "cz_add_invariant",
    "cz_add_finding",
    "cz_resolve_finding",
    "cz_add_lesson",
    "cz_obsolete_lesson",
    "cz_consolidate_lessons",
    "cz_promote_lesson",
    "cz_add_correction",
    "cz_create_gameplan",
    "cz_add_phase",
    "cz_transition_phase",
    "cz_add_amendment",
]
