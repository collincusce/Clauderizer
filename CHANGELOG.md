# Changelog

All notable changes to Clauderizer are documented here.

## [Unreleased]

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
