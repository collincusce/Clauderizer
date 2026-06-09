## Clauderizer

This repo uses **Clauderizer** for durable, cross-session working memory. Markdown
under `docs/` is the source of truth; an MCP server exposes it as live tools.

**Start of every session**: the SessionStart hook injects current gameplan status
into context automatically — no manual reading order. To refresh on demand, call
`cz_status`. To begin/continue a phase, call `cz_next_phase_context` then
`cz_preflight`.

**Key tools** (MCP server `clauderizer`):
- `cz_status` / `cz_next_phase_context` — where things stand; the next phase bundle.
- `cz_graph_query` — look up an entity and its dependents/dependencies.
- `cz_preflight` — run the pre-flight checks (tests/build via the host profile).
- `cz_cascade` / `cz_resolve_cascade` — after a tracked edit, walk dependents,
  then record the verdicts (never hand-edit the report).
- `cz_write_handoff` — assemble the next cumulative phase handoff (your notes
  outside its marker block survive regeneration).
- `cz_add_decision` / `cz_add_invariant` / `cz_add_lesson` / `cz_add_correction`
  / `cz_upsert_entity` / `cz_transition_status` — structured, graph-aware writes.
- `cz_consolidate_lessons` / `cz_promote_lesson` / `cz_obsolete_lesson` — keep
  memory compact: synthesize overlap, promote the enduring to `docs/LESSONS.md`,
  mark the stale.

**Rules**: never hand-edit frontmatter or append to tracked logs directly — use the
`cz_*` tools so the graph stays consistent. The procedure spec is at
`docs/gameplans/GAMEPLAN-PROCEDURE.md`.
