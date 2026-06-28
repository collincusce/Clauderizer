---
id: subsys.mcp-server
type: subsystem
version: 0.5.0
status: active
depends_on:
  - subsys.graph@^0.1.0
  - subsys.rituals@^0.1.0
  - subsys.mutations@^0.1.0
last_verified: 2026-06-28
---

# Mcp Server

The agentic tool surface: it exposes the markdown memory as **42 self-describing MCP tools** over stdio, so an agent dropped into a clauderized repo discovers the entire workflow from the tool list alone — no reading order, no doc pass. Each tool's name, signature, and docstring carry its schema, and that is the whole onboarding.

## Optional dependency

The core engine is zero-dep. The MCP SDK is needed only by the server and ships as the `mcp` extra: `pip install "clauderizer[mcp]"`. `mcp_server.build_server()` imports the SDK lazily, and `main()` catches `ImportError` to print the install hint — the rest of the package runs without it. `clauderizer-mcp --version`/`--help` answer without touching stdin or the SDK (a deterministic exit-0 probe for `init`/`doctor`).

## One shared registry (the key design)

Tools are **not** bespoke server closures. `ops.py` holds a single `REGISTRY: dict[str, Op]`, where `Op(fn, writes: bool)` pairs the implementation function with whether it mutates. `mcp_server.build_server()` registers those exact function objects in a loop, so the MCP schemas derive from the same callables that `clauderize ops` runs via `ops.run_batch()`. **The two transports cannot drift** — same names, same signatures, same docstrings, one table.

`run_batch()` executes a `[{op, args}, ...]` list sequentially, returning per-op `{n, op, ok, result|error}` plus an overall verdict. A failing op never aborts the batch (later ops still run); an op-level `{"ok": false}` counts as failed, same as a raised `TypeError` (bad args) or other exception (`LockHeld`, not-a-repo). This is the no-MCP fallback the README points to when the SDK is absent.

## The surface (42 tools)

The registry is **stateless**: `repo_ctx()` re-resolves the repo from cwd and rebuilds the graph from markdown on every call, so results match what's on disk even after out-of-band edits.

- **Reads** (`writes=False`, 13) — side-effect-free by contract (L-03), never take the write lock: `cz_status`, `cz_next_phase_context`, `cz_gameplans`, `cz_graph_query`, `cz_get`, `cz_analyze`, `cz_critique`, `cz_mine_failures`, `cz_corpus_health`, `cz_lesson_health`, `cz_curate`, `cz_loop_step`, `cz_discover_skills`.
- **Rituals** — `cz_preflight` (runs the host test/build or the focus kind's QA gates, refreshes the tracked baseline), `cz_cascade` / `cz_resolve_cascade` (walk dependents — incl. the cross-gameplan fan-out — then record verdicts), `cz_write_handoff`.
- **Mutations** — entity/graph (`cz_upsert_entity`, `cz_consumes`, `cz_transition_status`), the memory writes (`cz_add_decision`, `cz_add_invariant`, `cz_add_finding`/`cz_resolve_finding`, `cz_add_lesson` and the lesson-curation set `cz_consolidate_lessons`/`cz_obsolete_lesson`/`cz_promote_lesson`, `cz_add_correction`), skills (`cz_register_skill`/`cz_obsolete_skill`), the Ending-Protocol writes (`cz_add_output`, `cz_add_phase_summary`), and gameplan structure + focus (`cz_create_gameplan`, `cz_focus`, `cz_add_phase`, `cz_transition_phase`, `cz_add_amendment`).
- **Discipline gates** — `cz_add_open_item`/`cz_resolve_open_item`, `cz_set_exit_criteria`/`cz_check_exit_criterion` (always advisory, never blocking — INVARIANT-05).

### Locking

Writes serialize on the H-05 write lock (`.clauderizer/write.lock`). Mutation-backed ops lock inside `mutations.*`; ops that write through other paths — cascade reports, handoff regeneration, the active-gameplan config flip in `cz_create_gameplan` — take the lock in their own bodies, so MCP and CLI callers inherit identical serialization. `cz_preflight` is the deliberate exception: it runs host commands for minutes, so it skips an op-level lock and locks only at its single tracked write (the baseline refresh) to avoid tripping stale-lock takeover.

## Resources

`build_server()` also registers three read-only resources:

- `clauderizer://status` — the SessionStart digest, rendered with `TOOL_NAMES`.
- `clauderizer://procedure` — the gameplan procedure spec (on-disk, or the bundled asset).
- `clauderizer://entity/{entity_id}` — the raw markdown of one tracked entity.

## Tool-name parity

`tools_list.TOOL_NAMES` is the canonical list, shared by the server **and** the SessionStart digest — the digest advertises exactly what the server exposes (`status_bundle.render_digest(..., tools=TOOL_NAMES)`). A parity test welds `REGISTRY` to `TOOL_NAMES` so neither can grow a tool the other lacks.

## Position in the DAG

`subsys.mcp-server` is the outward face of the engine and **depends on** the graph (`graph.index`/`graph.query`/`graph.cascade`), the rituals (`rituals.status_bundle`/`preflight`/`handoff`/`critique`), and the mutations layer. It adds no memory logic of its own — it is purely the transport that turns those subsystems into a discoverable, agent-facing tool surface.
