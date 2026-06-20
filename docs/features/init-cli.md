---
id: feat.init-cli
type: feature
version: 0.3.0
status: completed
depends_on:
  - subsys.scaffold@^0.5.0
last_verified: 2026-06-20
---

# Init Cli

The `clauderize init` subcommand — the human/agent entry point that drops Clauderizer
into a repo. A thin CLI layer (`cli.cmd_init`) over `subsys.scaffold`'s `init()`; see
[scaffold](../subsystems/scaffold.md) for the wiring internals (host-of-record,
spawn-tests, the breadcrumb wrapper, split-host shapes).

## Usage

```
clauderize init [path] [--size pet|standard|saas] [--profile auto|node|python|go|ruby]
                [--gameplan "Name"] [--run-cmd "uvx --from clauderizer"]
                [--workflow code|docs|audit] [--session-host native|windows-wsl:<distro>]
                [--no-spawn-test] [-v]
```

- **`path`** — repo to clauderize (default: cwd).
- **`--size`** — the doc/ritual dial (default `standard`): `pet` (a gameplan + handoffs),
  `standard` (named docs + cascade + the 8-check pre-flight), `saas` (the full doc set +
  incidents + amendments).
- **`--profile`** — host language (default `auto` — detects node/python/go/ruby from repo
  markers, else `generic`).
- **`--gameplan`** — also scaffold a first gameplan with this name and record it active.
- **`--run-cmd`** — how the repo invokes the engine (default `uvx --from clauderizer`).
- **`--workflow`** — `docs`/`audit` make `clean_tree` (and, for audits, `tests`) advisory
  rather than fatal, so a deliverable-accumulating workflow doesn't fail pre-flight on
  every resume.
- **`--session-host`** — which host spawns sessions: `native` (default, auto-detected from
  existing wiring) or `windows-wsl:<distro>` for a WSL-installed engine driven from Windows.
- **`--no-spawn-test`** — skip the pre-write launch probes (an escape hatch for sandboxes
  that cannot spawn; the probes are the mis-wiring guard, so use sparingly).

## Behavior

**Idempotent.** Re-running fills gaps and refreshes engine-owned files but never clobbers
your content — marker blocks in `CLAUDE.md`/`AGENTS.md`, key-scoped `.mcp.json` merges,
exists-checks for `docs/`, and `profile.lock.toml` edits all survive. It prints a summary
(size, host profile, session host, files written vs. kept) plus any warnings; `-v` lists
every action. Before writing wiring it spawn-tests each command and refuses anything that
won't launch and identify itself (`WiringRefused`).

## Exit codes

`0` — clauderized (or refreshed). `1` — init refused: a `WiringRefused` (a command failed
its `--version` probe) or an invalid `--session-host`, with nothing written. Verify the
result with `clauderize doctor`.
