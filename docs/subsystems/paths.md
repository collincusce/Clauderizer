---
id: subsys.paths
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Paths

Where everything lives, resolved once from the repo root. This is the smallest and most widely depended-on module in the engine — twenty-two other modules import it — precisely because it is the only place that knows a filename.

## What makes a repo clauderized

One definition, and it is here: a directory containing `.clauderizer/config.toml`.

**`find_repo_root(start=None)`** walks `start` and its parents looking for that file and returns the first match. When nothing is clauderized it falls back in two stages — the nearest `.git` directory, then `start` itself — because `init` has to work on a repo that is not clauderized *yet*, which is the whole point of running it. The fallback order matters: preferring the git root over the cwd means `clauderize init` from a subdirectory installs at the repo root, where it belongs.

Every entry point resolves the root from the working directory on **every call**. Nothing caches it. That statelessness is what lets the MCP server and the `clauderize ops` CLI behave identically, and it is what makes `subsys.nesting`'s ownership test possible at all.

## RepoPaths

A frozen dataclass carrying `root`, `docs` and `gameplans`, with every other well-known location derived as a property. Freezing it is deliberate: a path bundle that callers can mutate is a path bundle that drifts.

**`resolve(root, docs_rel="docs", gameplans_rel="docs/gameplans")`** is the constructor. The two relative arguments are the only knobs; everything else is fixed.

The properties fall into four groups:

- **Engine state** under `.clauderizer/` — `clauderizer_dir`, `config_file`, `index_file`, `abstract_index_file`, `profile_lock`, `kinds_dir`, `write_lock_file`, `telemetry_file`, `dreams_file`. The last three are per-machine and gitignored; `index_file` and `abstract_index_file` are disposable caches rebuilt from markdown on demand (INVARIANT-01).
- **Memory** under `docs/` — `doc(name)` for the named living docs (`doc("DECISIONS")` → `docs/DECISIONS.md`, appending `.md` when absent), plus `features_dir`, `subsystems_dir`, `procedure_file`, and `gameplan_dir(gameplan_id)`.
- **Host wiring** at the repo root — `claude_md`, `agents_md` (the cross-harness instructions file that Codex, kimi and others honor, carrying the same marker-block stanza), `mcp_json`.
- **Generated guides** — `kimi_setup`, the Kimi Code CLI setup guide whose guide-only pieces `init` writes rather than editing the user's global config.

`doc()` and `gameplan_dir()` are methods rather than properties because they take an argument; everything else is a property so a caller cannot forget to call it.

## Why the filenames live here and not at each call site

A path spelled at its point of use is a path that gets spelled differently somewhere else. Keeping every well-known location on one dataclass means renaming an artifact is a one-line change, and it means a reader can enumerate the engine's entire on-disk footprint by reading one file — which is what `TRUST.md` and the uninstaller both depend on.

## DAG position

Depends on nothing. Imported by essentially everything: `mutations`, `ops`, `cli`, `listing`, `analyze`, `dreams`, `telemetry`, `modernize`, `onboard`, `proposals`, `nesting`, `engine_identity`, `skill_discovery`, the hook handlers, all of `rituals/`, `graph/abstract_index`, and both `scaffold/init` and `scaffold/uninstall`.
