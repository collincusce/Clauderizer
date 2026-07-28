---
id: subsys.mutations
type: subsystem
version: 0.8.0
status: active
depends_on:
  - subsys.markdown-core@^0.1.0
  - subsys.graph@^0.1.0
last_verified: 2026-07-25
---

# Mutations

The single idempotent, graph-aware write path for all structured memory. Every `cz_add_*` / `cz_upsert_*` / `cz_transition_*` tool delegates here (`ops.py`), and every function routes through `markdown.writer` — so IDs auto-number from what's already in the doc, frontmatter stays valid, append-only logs stay append-only, and the agent never hand-edits a tracked doc.

## Auto-numbering

IDs (`D-NNN`, `INVARIANT-NN`, `H-NN`, `C-NN`, `A-NNN`, `O-NN`, `L-NN`, lesson `**N.**`) are allocated by `model.next_numbered_id()`, called on a fresh read of the target. **Only entry anchors count** — `### <ID> — …` headings and line-start `**<ID>.**` bold entries. A mention inside prose (a scaffold placeholder, or a cross-reference to another doc's IDs) never shifts the sequence. This is the 0.6.0 fix: its regex is line-anchored (`C-01`; before it, a decision citing another gameplan's `D6` made the series skip `D6`). `add_lesson` applies the same line-anchored count to lesson numbers.

## Append-only memory (INVARIANT-03)

Decisions, invariants, findings, corrections, and lessons are **superseded, never deleted**. `obsolete_lesson` rewrites the line with an `(obsolete <date>: …)` marker and keeps it (re-marking is a no-op); `promote_lesson` marks the source `(promoted <date>: L-NN)` so it stops rolling up but stays in the trail; `resolve_finding` updates an `H-NN` block's `**Status**` line + a dated `**Resolution**` in place; `resolve_open_item` appends `_(resolved <date>: …)_` to the `O-NN` line. Nothing is removed — `consolidate_lessons` shrinks the handoff roll-up while the full set of source lines survives, each marked `(obsolete …: consolidated into #N)`.

## Well-formedness at the write boundary (D-066)

Every render site interpolates caller strings into markdown that line-anchored parsers then read back, so the boundary is where a string could **forge structure**. `_safe_body` / `_safe_cell` / `_one_line` are that boundary, and the contract is **normalize, never reject**: no write is lost (INVARIANT-03) and no mutation gains a hard block (INVARIANT-05). This is D-007/INVARIANT-02 well-formedness, *not* a discipline gate — INVARIANT-05 enumerates exactly three gates, and `dreams.validate` is the shipped precedent that a blessed write may check its own input. Normalization runs **before** the change diff, so re-submitting identical input stays a no-op.

- **Forged structure** — a column-zero heading, a `### D-900 — …` entry anchor, or a `**N.**` lesson number is backslash-escaped (CommonMark renders it identically, so the human view is byte-equivalent while the parsers stop matching). Unescaped, `add_decision(title="ok\n\n### D-900 — FAKE…")` returned `ok:true`, created a genuine-looking D-900, absorbed the real entry's body, and burned 899 ids irreversibly.
- **Table cells** — pipes escaped and newlines collapsed (H-02): a `|` in a phase name ate half the name on the next transition.
- **Marker blocks** — a body containing `clauderizer:handoff` would permanently escape its block, voiding D-008's byte-for-byte guarantee.
- **Leaked tool-call markup** (1.14.1) — `_strip_toolcall_markup` removes the writing agent's own framing when it lands in an argument *value*. Two signals, neither of them "any angle bracket": the tool-call vocabulary (`parameter` / `invoke` / `function_calls`, bare or `antml:`-prefixed), and **unbalanced** closing tags — `</context>` with no `<context…>` opening it. Unbalanced-detection is what leaves a body legitimately containing `<div>…</div>` completely alone, which a field-name blocklist could not promise. Code spans and fenced blocks are skipped, matching the read side's `sections._without_code_spans`, so an entry that *quotes* this shape is never rewritten.

1.14.0 specified that last guard as an exit criterion and never built it; four entries — `D-052`, `D-062`, `H-19`, `H-23` — carry the proof, and `tests/test_toolcall_write_guard.py` reads them off disk as its acceptance corpus. They are deliberately **not** retro-edited: append-only (INVARIANT-03), they parse, and repair belongs to the amendment op.

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
- **Lesson curation** — `add_lesson`, `obsolete_lesson`, `promote_lesson` (to `docs/LESSONS.md`), `consolidate_lessons`, `reinforce_lesson` (D-075: the third verb beside consolidate/append — strengthens the EXISTING lesson with an in-place `*(reinforced xN, last <date>)*` trailer through the single `_inline_trailer` renderer instead of keeping a near-duplicate twin; only the agent ever calls it, INVARIANT-05); the anti-bloat half of `D-009`.
- **Phase outputs** — `add_output` (the PHASE-STATUS Outputs Registry, upsert-by-key), `add_phase_summary`, `resolve_cascade` (fill a cascade report's verdicts).
- **Entities / status** — `upsert_entity`, `transition_status` (the cascade trigger).
- **Discipline gates** (`D-015`, advisory, never block) — `add_open_item` / `resolve_open_item` (clarify), `set_exit_criteria` / `check_exit_criterion` (machine-checkable `- [ ]` exit criteria). `add_decision` also runs the `D-016` analyze enrichment, returning related existing entries for contradiction judgment.

## In the DAG

`subsys.mutations` depends on **markdown-core** (the `writer`/`sections`/`tables` single write path) and **graph** (`index` + `cascade`, for `transition_status`). **mcp-server** depends on it: the `cz_*` tools in `ops.py` are thin wrappers over these functions.
