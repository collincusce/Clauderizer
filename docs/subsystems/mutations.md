---
id: subsys.mutations
type: subsystem
version: 0.7.0
status: active
depends_on:
  - subsys.markdown-core@^0.1.0
  - subsys.graph@^0.1.0
last_verified: 2026-07-01
---

# Mutations

The single idempotent, graph-aware write path for all structured memory. Every `cz_add_*` / `cz_upsert_*` / `cz_transition_*` tool delegates here (`ops.py`), and every function routes through `markdown.writer` — so IDs auto-number from what's already in the doc, frontmatter stays valid, append-only logs stay append-only, and the agent never hand-edits a tracked doc.

## Auto-numbering

IDs (`D-NNN`, `INVARIANT-NN`, `H-NN`, `C-NN`, `A-NNN`, `O-NN`, `L-NN`, lesson `**N.**`) are allocated by `model.next_numbered_id()`, called on a fresh read of the target. **Only entry anchors count** — `### <ID> — …` headings and line-start `**<ID>.**` bold entries. A mention inside prose (a scaffold placeholder, or a cross-reference to another doc's IDs) never shifts the sequence. This is the 0.6.0 fix: its regex is line-anchored (`C-01`; before it, a decision citing another gameplan's `D6` made the series skip `D6`). `add_lesson` applies the same line-anchored count to lesson numbers.

## Append-only memory (INVARIANT-03)

Decisions, invariants, findings, corrections, and lessons are **superseded, never deleted**. `obsolete_lesson` rewrites the line with an `(obsolete <date>: …)` marker and keeps it (re-marking is a no-op); `promote_lesson` marks the source `(promoted <date>: L-NN)` so it stops rolling up but stays in the trail; `resolve_finding` updates an `H-NN` block's `**Status**` line + a dated `**Resolution**` in place; `resolve_open_item` appends `_(resolved <date>: …)_` to the `O-NN` line. Nothing is removed — `consolidate_lessons` shrinks the handoff roll-up while the full set of source lines survives, each marked `(obsolete …: consolidated into #N)`.

## The write lock

Every public mutation carries `@_locked`, which wraps the **whole** function (not the individual `writer` calls) in `locking.write_lock` on `.clauderizer/write.lock`. IDs are read at the top and trusted by the write at the bottom, so the lock must span the full read-modify-write; this is the choke point that closes `H-05` (one MCP server per session means a second window or subagent otherwise races appends and ID allocation). N concurrent writer processes therefore yield N sequential IDs and N surviving appends.

- **Acquire** is an `O_CREAT | O_EXCL` create with holder metadata (pid, host, timestamps, a one-shot nonce) written inside — portable, no daemon, no `fcntl`.
- **Stale takeover**: a holder older than `stale_timeout` (~30s; mutations run in milliseconds) is presumed crashed and atomically renamed away; exactly one contender wins, and each writer re-reads its own nonce after create so a loser of a racing takeover rejoins the queue rather than proceeding unlocked.
- **Contention** past `acquire_timeout` (default 10s) raises `LockHeld` — a clear, `retryable` error naming the holder.
- **Reentrant per thread** (L-03 composition): a mutation that calls another (`consolidate_lessons` → `add_lesson` → `obsolete_lesson`) takes the lock once, counted by depth on a per-path `RLock`.
- **Reads never acquire it** (L-03): a context fetch must not block, or be blocked by, a writer. (A few ops that don't route through `mutations.*` lock at the ops layer instead.)

## Cascade coupling

`transition_status` is the one mutation that fires the graph cascade: after writing the new `status` to the entity's frontmatter, when `run_cascade` is on **and** the `cascade` ritual is enabled **and** a gameplan is active, it reloads the graph and runs `cascade.run`, writing a report under `_cascade-reports/`. (`transition_phase` and `add_decision` instead surface advisory findings — see Discipline gates — and never block.)

## Write families

- **Planning** — `create_gameplan` (scaffolds the gameplan tree from templates), `add_phase`, `transition_phase` (phase lifecycle in the markdown trackers, with self-healing of fractured tables and tracker headers), `add_amendment`.
- **Records (append-only)** — `add_decision` (project `D-NNN` or gameplan-internal `D1`), `add_invariant`, `add_finding`/`add_risk` + `resolve_finding`, `add_correction`.
- **Lesson curation** — `add_lesson`, `obsolete_lesson`, `promote_lesson` (to `docs/LESSONS.md`), `consolidate_lessons`; the anti-bloat half of `D-009`.
- **Phase outputs** — `add_output` (the PHASE-STATUS Outputs Registry, upsert-by-key), `add_phase_summary`, `resolve_cascade` (fill a cascade report's verdicts).
- **Entities / status** — `upsert_entity`, `transition_status` (the cascade trigger).
- **Discipline gates** (`D-015`, advisory, never block) — `add_open_item` / `resolve_open_item` (clarify), `set_exit_criteria` / `check_exit_criterion` (machine-checkable `- [ ]` exit criteria). `add_decision` also runs the `D-016` analyze enrichment, returning related existing entries for contradiction judgment.

## In the DAG

`subsys.mutations` depends on **markdown-core** (the `writer`/`sections`/`tables` single write path) and **graph** (`index` + `cascade`, for `transition_status`). **mcp-server** depends on it: the `cz_*` tools in `ops.py` are thin wrappers over these functions.
