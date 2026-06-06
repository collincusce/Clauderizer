# Changelog

All notable changes to Clauderizer are documented here.

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
