# Changelog

All notable changes to Clauderizer are documented here.

## [0.7.0] — 2026-06-09

The **agent-autonomy** release: the recording machinery now works — and fails —
out loud, from any host, under any concurrency, with or without MCP. Every
change closes a named finding from the 0.6.0 live tests (H-05, L-05, H-04,
H-01 residue, the stale-uvx thread).

### Added
- **Advisory write lock** (`.clauderizer/write.lock`) — every tracked write
  serializes at the mutation choke point: O_EXCL acquire with holder metadata,
  stale takeover (~30s), clear retryable `LockHeld` error naming the holder.
  N concurrent writer *processes* now yield N sequential IDs and N surviving
  appends (closes H-05). Reads stay lock-free.
- **`clauderize ops <file.json|->`** — CLI write parity: a JSON batch of
  `[{op, args}, ...]` executes against the same registry the MCP server
  dispatches; op names and schemas are exactly the `cz_*` tool names. Every
  tracked write is now reachable without an MCP client (closes L-05); the
  ad-hoc shim patterns are retired.
- **Session host of record** — config records which host spawns sessions
  (`native` | `windows-wsl:<distro>`); init composes host-appropriate wiring
  (wsl.exe shim, command/args split) and **spawn-tests every command before
  writing** (refuses the H-04 `clauderize clauderizer-mcp` mis-composition
  with nothing written); doctor verifies launchability *for the recorded
  host* or honestly reports "unverifiable from this host" (exit 3 — never a
  false green). Closes H-04.
- **Cold-start breadcrumb wrapper** — init registers a thin always-spawns
  wrapper (`.clauderizer/hook.sh`, `hook.cmd` on native win32) as the
  SessionStart command; any engine failure becomes a stdout breadcrumb
  (`[Clauderizer] engine unreachable: … — run clauderize doctor`) instead of
  silence (closes H-01's residue). Doctor checks wrapper presence and
  freshness against the engine path.
- **Wiring identity verification (D5)** — doctor's round-trip launch checks
  now require the wiring to *identify its engine*: the probed `--version`
  output must claim the same version as the engine answering doctor.
  Catches pinned-stale wiring that launches fine (a `uvx --from
  clauderizer[mcp]==0.5.0` pin passes every exit-code probe — demonstrated
  live, recorded as H-06) and a dead engine behind the always-exit-0 hook
  wrapper (whose breadcrumb previously read as a green hook verdict).

### Fixed
- **`cz_add_amendment` dangling cascade pointer** — amendment entries cited
  `_cascade-reports/<date>-A-NNN.md`, a per-amendment filename no code path
  creates under any setting. The `Cascade report` line now renders only when
  the `amendments` ritual is enabled, and as an honest pending pointer
  (cascade reports are per-entity files). A-001 in the 0.6.0 gameplan healed
  to cite the per-entity report that actually holds its cascade evidence.
  Procedure 1.2.0 → 1.2.1 documents the conditional line.

Closes the **engine-robustness cluster** from the two prior post-mortems plus
the cold-start findings H-01..H-03. The through-line is *structure over
substrings*: every defect came from the engine writing or reading markdown by
line/substring heuristics — tables appended as paragraphs, IDs counted in
prose, lesson state inferred from anywhere-in-line markers.

### Added
- **`cz_add_output`** — blessed write for the PHASE-STATUS **Outputs Registry**
  (per-phase fenced blocks; same-key upserts rewrite in place). The registry
  had sat at its scaffold placeholder through two closed gameplans for want of
  this write.
- **`cz_add_phase_summary`** — blessed write for the index's **Per-Phase
  Completion Summaries** (one block per phase; re-recording replaces it).
- **Tracker header write-backs** — `cz_transition_phase` / `cz_add_phase` now
  refresh `> Status:` / `> Last updated:` on both trackers and GAMEPLAN.md's
  `Status` (Planning → Executing → Complete) from the live phase table. Both
  closed gameplans had read "Phase 0 ready" since the day they finished.
- **`doctor` engine-identity checks** — installed dist-info must match the
  running source `__version__` (caught live: an editable install reporting
  0.3.0 under 0.5.0 source), and when the repo *is* the clauderizer source,
  the running engine must match the repo's pyproject version (stale uvx/pipx
  cache while dogfooding).
- **CLI fallback breadcrumb** — the CLAUDE.md stanza now says what to do when
  the `cz_*` tools are absent: `clauderize doctor` / `clauderize status`
  (a cold session previously couldn't tell broken wiring from no Clauderizer).

### Changed
- **Anchored ID numbering** — `next_numbered_id` counts only entry anchors
  (`### <ID> —` headings, `**<ID>.**` bold entries). Scaffold placeholder
  prose and cross-references no longer shift sequences (one gameplan's
  decisions had numbered D3..D9, skipping D6, because template prose and a
  citation of another gameplan's D6 were counted).
- **Structural table writes** — tracker phase rows go through a table-aware
  writer (`markdown/tables.py`) that rebuilds the block contiguously on every
  blessed touch; trackers fractured by the old paragraph-append healed in
  place, no migration script. Rendered markdown is valid for humans again,
  not just for the engine's own tolerant parser.
- **Collision-proof cascade reports** — filenames carry a zero-padded `-NN`
  sequence per date+entity (never timestamps), so same-day cascades of one
  entity coexist instead of silently overwriting; `pending_cascades` orders
  chronologically (legacy unsuffixed names rank as sequence 0).
- **Lesson state is a grammar, not a substring** — one parser
  (`markdown/lesson_state.py`) reads the trailing `(obsolete …)` /
  `(promoted …)` markers (or legacy `~~strikethrough~~`); the gauge, handoff
  roll-ups, and obsolete/promote/consolidate all share it. A lesson whose
  *text* mentions "(obsolete" counts as active everywhere.
- **Preflight runs profile commands in the engine's own environment** — the
  running interpreter's bin dir leads PATH, so a venv-installed engine finds
  its own pytest/ruff without shell activation (`pytest: not found` observed
  live on a venv-wired engine).
- A completed gameplan's digest says `(handoff n/a: gameplan complete)`
  instead of silently dropping the promised size estimate.

## [0.5.0] — 2026-06-09

Closes review finding 5 (**context economics**): cumulative memory grew
monotonically — handoffs carried every lesson forever, lessons died with their
gameplan at close, and nothing measured the bundle. Per ADR D-009 the answer is
consolidation *pressure*, never caps: three blessed writes plus visibility, with
the audit trail intact.

### Added
- **`cz_consolidate_lessons`** — synthesize N overlapping lessons into one; each
  source is marked `(obsolete: consolidated into #N)` and every future handoff
  carries one line instead of many. All sources validated before anything is
  written.
- **`cz_promote_lesson`** — promote an enduring lesson into a compact,
  on-demand `docs/LESSONS.md` as an `L-NN` entry with provenance; the source is
  marked `(promoted <date>: L-NN)` and stops rolling up individually. Handoffs
  gain a "Project Lessons (distilled)" section that rides **across gameplans** —
  lessons finally outlive the gameplan that learned them.
- **Memory gauge** — `cz_status` / the SessionStart digest report
  `Memory: N active lessons, M project (~K tok handoff)` and nudge toward
  consolidate/promote/obsolete past `ACTIVE_LESSONS_WARN` (12, a documented
  constant). Bloat is a visible state, not a silent failure mode.
- `cz_obsolete_lesson` accepts `L-NN` ids, so the project list is curated with
  the same rules (its `number` parameter is now a string).
- Close-gameplan skill: a lesson-curation step (consolidate, then promote
  deliberately — not in bulk); do-phase nudges consolidation when the list
  repeats itself.

## [0.4.0] — 2026-06-09

Closes the **discipline seams** from the 2026-06-09 external review: the places
where the workflow still depended on agents hand-editing tracked docs because
the blessed write was missing, destructive, or never ran.

### Added
- **`cz_resolve_cascade`** — record per-dependent verdicts + the Updates
  applied/deferred sections on a cascade report. Previously, clearing the
  `cascade_hygiene` preflight check *required* a forbidden hand-edit — the rules
  banned the only way to make progress. Defaults to the latest pending report;
  partial resolution keeps it pending (`status_bundle.pending_cascades` is now
  the public, shared predicate).
- **`cz_obsolete_lesson`** — mark an accumulated lesson `(obsolete <date>: <reason>)`
  through a tool. The line stays in the log (append-only memory); handoff roll-ups
  stop carrying it, so cumulative handoffs can shrink without a hand-edit.
- **Baseline write-back** — a green `cz_preflight` run that measures a test count
  now refreshes the active gameplan's "Current baseline test count" line
  (anti-pattern #7, stale references, applied to the system itself: this repo's
  own hook said "0 tests" while 84 passed).
- **Completed-gameplan status** — a gameplan whose phases are all complete now
  reports "all N phase(s) COMPLETE" with close-out guidance instead of the
  confusing "no in-progress or ready phase found".
- **`doctor`: lock-file check** — flags a `profile.lock.toml` that doesn't parse
  (whose overrides were being silently ignored).

### Changed
- **Marker-protected handoffs (D-008)** — `cz_write_handoff` owns only a
  `<!-- clauderizer:handoff -->` marker block; regeneration replaces the block and
  preserves everything outside it byte-for-byte. Fresh handoffs add an agent-owned
  "Phase Notes" scaffold; legacy generated skeletons are migrated wholesale;
  unrecognized files are preserved verbatim below the block. `cz_next_phase_context`
  returns the merged view, so a context fetch includes on-disk enrichment.
- Skills no longer instruct hand-edits anywhere: cascade/do-phase route through
  `cz_resolve_cascade`, record routes risks through `cz_add_finding`.

### Fixed
- **`Profile.to_lock_toml` emitted invalid TOML** for profiles whose baseline
  regex contains backslashes (e.g. python's `(\d+) passed`) — and since
  `load_for_repo` falls back silently on parse errors, every python-profile lock
  written by `init` was being ignored in its entirety. Lock values are now
  TOML-escaped, with a round-trip regression test across all packaged profiles.

## [0.3.0] — 2026-06-05

Fixes the **state-mutation surface** — the gaps a second dogfooding session found
where structured state drifted because the blessed write was missing or destructive.

### Added
- **`cz_transition_phase`** — phases finally get a lifecycle write
  (not_started/ready/in_progress/complete/blocked/failed, with aliases + auto-dated
  Started/Completed). Without it, `cz_status` froze at "Phase 0" on finished work
  because nothing could advance a phase. The single highest-leverage fix.
- **`cz_resolve_finding`** — update a finding's status + dated resolution note in
  `HARDENING.md`, satisfying its own "mark resolved, never delete" policy through a
  blessed path instead of a forbidden hand-edit.
- **Drift hint** — `cz_status` / the SessionStart digest now flag entities still
  `planned` while phases are complete ("⚠ Drift: … cz_transition_status to reconcile").
  Conservative: fires only when there's completed work *and* untouched entities.
- **`init --workflow {code,docs,audit}`** + `preflight_advisory` config — makes
  `clean_tree` (and, for audits, `tests`) advisory rather than fatal, so a
  deliverable-accumulating workflow stops failing preflight on every resume.

### Fixed
- `init` resolves the engine command from the **running interpreter's bin dir**
  (`sys.executable`) before falling back to PATH/uvx — reliable for venv/WSL even
  when the bin dir isn't on PATH.
- `init` **no longer clobbers `profile.lock.toml`** on re-run — per-project command
  overrides (read back by `detect.load_for_repo`) are preserved. Delete the lock to
  re-derive it.

## [0.2.1] — 2026-06-05

### Fixed
- Require **Python ≥ 3.11**. The engine uses the stdlib `tomllib`, which only
  exists from 3.11, so 0.2.0 crashed on import under 3.10 despite advertising
  `>=3.10`. Corrected `requires-python`, classifiers, and the CI matrix. (Keeps
  the zero-runtime-dependency promise rather than pulling in a `tomli` backport.)

## [0.2.0] — 2026-06-05

First release published to PyPI.

### Packaging
- Fixed the wheel build: removed a `force-include` table that collided with
  `packages`, which broke `uv build` / `python -m build`. The `templates/`,
  `profiles/`, and `skills/` data dirs are bundled via `packages` and verified
  present in the wheel.
- Core install is dependency-free; the MCP server is the `clauderizer[mcp]` extra.

### Added
- `cz_add_finding` / `mutations.add_finding` (alias `add_risk`) — record structured
  security/audit findings into the append-only `HARDENING.md` tracker.
- `doctor` now probes that the MCP server **and** SessionStart hook commands are
  actually executable, not just registered — a green check on a non-launchable
  setup is worse than no check.
- `detect.load_for_repo()` overlays a project-local `profile.lock.toml`, so
  per-project test/build/lint/typecheck overrides take effect (the lock was
  previously write-only).

### Changed
- `init` wiring now prefers installed console scripts (venv/pipx) and only falls
  back to `uvx`, fixing the Windows→WSL / venv drop-in path.
- Re-running `init` with a changed invocation now **replaces** the SessionStart
  hook instead of appending a duplicate.
- `cz_next_phase_context` is side-effect-free: it assembles the handoff in memory
  (`handoff.assemble(..., write=False)`) and returns it as `handoff_md`; only
  `cz_write_handoff` persists a file.
- The first real entry in a doc section now replaces the scaffold `_(…)_`
  placeholder instead of stacking beneath it.

### Fixed
- SessionStart hook errors print to stdout (visible in session context) instead
  of stderr, where silent failure was the dangerous kind.

## [0.1.0] — 2026-05-30

Initial release. A drop-in, MCP-native successor to the markdown "gameplan
system": same conceptual model (gameplan → phase → task, a long-lived Project
DAG, post-hoc cascade, cumulative handoffs, append-only memory), delivered as an
active system instead of a procedure followed by hand.

### Added

- **Markdown core** — zero-dependency frontmatter parser, section/marker editing,
  and a single idempotent mutation path (`markdown/writer.py`).
- **Project DAG** — graph index (cached to a disposable `index.json`), dependent/
  dependency queries, and semver pin-violation detection.
- **Cascade** — post-hoc forward walk that writes a judgment-based report
  (dependents marked "needs review"). Replaces the never-built `bin/cascade`.
- **Rituals as operations** — `preflight` (the 7 checks run for real against host
  profile commands), cumulative `handoff` assembly, and the `status` digest.
- **Structured mutations** — decisions, invariants, lessons, corrections,
  gameplans, phases, amendments, entities, and status transitions (auto-cascade).
- **MCP server** — 15 self-describing tools + resources over stdio (optional
  `mcp` extra).
- **Configurability** — `pet` / `standard` / `saas` size dial and host-language
  profiles (Node, Python, Go, Ruby, generic) as pure data.
- **Drop-in** — `clauderize init` (idempotent), `status`, `doctor`, `reindex`,
  `mcp`; a SessionStart hook for automatic cold-start; six Claude Code skills.
- Test suite: 57 tests covering markdown round-trips, the graph, cascade,
  rituals, mutations, init idempotency, profiles, and the live MCP tools.
