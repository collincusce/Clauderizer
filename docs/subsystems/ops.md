---
id: subsys.ops
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.mutations
  - subsys.listing
  - subsys.rituals
  - subsys.contract
  - subsys.locking
last_verified: 2026-07-25
---

# Ops

The shared ops registry — **one dispatch surface for MCP and CLI** (L-05).

## The surfaces cannot drift

Every `cz_*` operation lives here as a plain function whose **name, signature and docstring *are* the tool contract**. The MCP server registers these exact function objects, so its schemas derive from them; `clauderize ops` executes the same objects from JSON batches. One table, two transports.

That property is load-bearing well beyond tidiness. Cursor's Composer 2.5 Fast made **0 MCP calls across 142 tool calls** and found the `uvx … clauderize ops` CLI fallback on its own — so a CLI-reachable path for every tracked write is what makes cross-*model* sessions work, not merely no-MCP ones. If the two transports exposed different op sets, the fallback would be a trap rather than a fallback.

## The registry

- **`Op`** — one registered operation: the shared callable plus **`writes: bool`**.
- **`REGISTRY`** — the table. `cz_get` is `writes=False` because it never mutates canonical markdown (INVARIANT-01).
- **`run_op(name, **kwargs)`** — execute one.
- **`run_batch(spec)`** — execute a JSON batch: `[{"op": "cz_add_lesson", "args": {...}}, ...]`. The no-MCP fallback in full.
- **`op_schema(name)`** / **`list_ops()`** — introspection, derived from the function signatures rather than a parallel schema file.
- **`repo_ctx()`** — resolve the repo from the working directory. Called on **every** op, stateless, matching the MCP server's behaviour.

## Locking follows the write path

Mutation-backed ops lock inside `mutations.*`. The ops that write through other paths — cascade reports (`cz_resolve_cascade`), handoff regeneration (`cz_write_handoff`), the active-gameplan flip (`cz_focus`) — take the lock **here**, in their own bodies, so MCP and CLI callers inherit it identically (H-05). Read ops never lock (L-03).

## The op families

- **Orientation** — `cz_status`, `cz_next_phase_context`, `cz_gameplans`, `cz_graph_query`, `cz_get`, `cz_revision`.
- **Gates, advisory by construction** (INVARIANT-05) — `cz_analyze`, `cz_critique`, `cz_audit`, `cz_preflight`, `cz_cascade`, `cz_resolve_cascade`.
- **Gameplan lifecycle** — `cz_create_gameplan`, `cz_focus`, `cz_add_phase`, `cz_transition_phase`, `cz_add_amendment`, `cz_write_handoff`, `cz_add_output`, `cz_add_phase_summary`, `cz_approve_gate`, `cz_assign`.
- **Memory writes** — `cz_add_decision`, `cz_add_invariant`, `cz_add_finding`, `cz_resolve_finding`, `cz_add_lesson`, `cz_add_correction`, `cz_upsert_entity`, `cz_consumes`, `cz_transition_status`, `cz_register_skill`, `cz_obsolete_skill`.
- **Curation** — `cz_consolidate_lessons`, `cz_obsolete_lesson`, `cz_promote_lesson`, `cz_reinforce_lesson` (D-075: strengthen the existing lesson instead of appending a near-duplicate twin), `cz_corpus_health`, `cz_lesson_health`, `cz_curate`, `cz_loop_step`.
- **Discipline gates** — `cz_add_open_item`, `cz_resolve_open_item`, `cz_set_exit_criteria`, `cz_check_exit_criterion`.
- **Reads over the registers** — `cz_list_open_items`, `cz_list_decisions`, `cz_list_invariants`, `cz_list_findings`, `cz_list_lessons`, `cz_list_corrections`, `cz_list_amendments`, `cz_phase_detail`, `cz_list_cascade_reports`, `cz_docs_index`, `cz_doc`, `cz_assignments`.
- **Upgrade and discovery** — `cz_modernize`, `cz_dismiss_proposal`, `cz_defer_proposal`, `cz_onboard`, `cz_discover_skills`, `cz_mine_failures`.
- **The dream loop** — `cz_add_dream`, `cz_dream`, `cz_dream_propose`, `cz_handle_dream_proposal`, `cz_register_dream_schedule`.

## Two contracts the surface must hold

Every result is stamped with `contract.CONTRACT_SCHEMA_VERSION`, and every write bumps `subsys.revision`. Together those are what let an external client poll cheaply and render safely without ever parsing the markdown itself (INVARIANT-01).

## DAG position

Depends on `subsys.mutations` (writes), `subsys.listing` (reads), `subsys.rituals` (preflight, handoff, status), `subsys.contract` (the stamp) and `subsys.locking`. Consumed by `mcp_server` (tool registration) and `cli` (`clauderize ops`). `subsys.tools-list` names the surface for the digest.
