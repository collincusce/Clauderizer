<!-- clauderizer:start -->
## Clauderizer

This repo uses **Clauderizer** for durable, cross-session working memory. Markdown
under `docs/` is the source of truth; an MCP server exposes it as live tools.

**Start of every session — load memory first.** If a `[Clauderizer]` status digest
appeared at the top of this session, your host has a session hook and memory is
already loaded. **If no digest appeared, call `cz_status` now, before anything
else** — many hosts have no session hook, and `cz_status` is your durable project
memory (where the gameplan stands, the baseline, open items). Either way, to
begin or continue a phase, call `cz_next_phase_context` then `cz_preflight`.

**If the `cz_*` tools themselves are absent** (the call fails, not just a missing
digest), the wiring is broken, not the memory: run `clauderize doctor` in a shell,
use `clauderize status` for the digest, and make tracked writes with `clauderize
ops <file.json|->` — a JSON batch `[{"op": "cz_add_lesson", "args": {...}}, ...]`
against the exact tool names and schemas — until the wiring is repaired. Every
`cz_*` tool is reachable that way.

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
- `cz_add_output` / `cz_add_phase_summary` — the Ending Protocol writes: record
  a phase's concrete produced values and its completion summary.
- `cz_consolidate_lessons` / `cz_promote_lesson` / `cz_obsolete_lesson` — keep
  memory compact: synthesize overlap, promote the enduring to `docs/LESSONS.md`,
  mark the stale.
- `cz_add_open_item` / `cz_resolve_open_item` / `cz_set_exit_criteria` /
  `cz_check_exit_criterion` / `cz_analyze` — the discipline gates (D-015/D-016,
  always advisory & judgment-based — INVARIANT-05): track open items and
  machine-checkable exit criteria (surfaced when a phase completes), and surface the
  decisions/invariants most relevant to a new decision for contradiction-judgment.

**Rules**: never hand-edit frontmatter or append to tracked logs directly — use the
`cz_*` tools (or `clauderize ops` when MCP is unavailable) so the graph stays
consistent. The procedure spec is at `docs/gameplans/GAMEPLAN-PROCEDURE.md`.
<!-- clauderizer:end -->
