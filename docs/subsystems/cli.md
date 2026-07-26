---
id: subsys.cli
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.ops
  - subsys.scaffold
  - subsys.hosts
  - subsys.hosttargets
last_verified: 2026-07-25
---

# CLI

`clauderize` — the human and agent command line, and the transport that works when MCP does not.

## The subcommands

- **`cmd_init`** — drop Clauderizer into the current repo. **Idempotent**: re-running fills gaps without overwriting choices, expands host wiring rather than narrowing it (L-48), and preserves the profile lock.
- **`cmd_status`** — print the current gameplan digest. The same bundle the SessionStart hook emits.
- **`cmd_gameplans`** / **`cmd_focus`** — the portfolio, and which gameplan is in focus.
- **`cmd_reindex`** — rebuild the disposable graph cache from markdown. Always safe, because the markdown is the source of truth (INVARIANT-01).
- **`cmd_upgrade`** — apply `subsys.modernize`'s mechanical tier and surface its proposals.
- **`cmd_doctor`** — verify the install and report drift.
- **`cmd_release_check`** — preflight the four version registries plus push ordering (`subsys.release-check`).
- **`cmd_mcp`** — launch the MCP server over stdio.
- **`cmd_ops`** — execute a JSON batch of `cz_*` operations. The no-MCP fallback.
- **`cmd_uninstall`** — reverse the wiring footprint. **Preserves `docs/` memory**: uninstalling the engine must never delete what the project learned.
- **`build_parser()`** — the parser, exposed so tests and embedders can introspect the surface rather than shelling out.

## Why `ops` matters more than it looks

`clauderize ops <file.json|->` reaches **every** `cz_*` operation, because both transports execute the same registry (`subsys.ops`). That makes it the repair path when MCP wiring is broken — and, less obviously, the path a non-Claude model may take by preference. A model that makes zero MCP calls can still make tracked writes, which is why the fallback is a first-class surface and not a debugging aid.

The corollary is a verification duty: a model's self-reported close-out is not evidence. A reindex once showed a plausible-sounding summary claiming entities that were never created (L-66) — so trust, but check the engine state.

## Doctor is three-state

`doctor` reports `ok` with its evidence, `fail`, or `unverifiable` — never a false green (D-010). It verifies by **capability**: spawning the composed hook command and completing a real MCP handshake (L-25), rather than confirming a config file contains plausible JSON. It also reports nested installs (`subsys.nesting`), a `profile.lock.toml` that will not parse, and engine identity drift (`subsys.engine-identity`).

## Entry points that self-heal

`init`, `doctor` and `status` are the write-permitted entry points that re-apply bespoke-host registration (`subsys.bespoke_hosts`). A host that regenerates its own config cannot bootstrap its re-heal, so the repair has to ride commands the user runs anyway — idempotent and atomic, so re-applying is a safe no-op.

## The documented install path is tested as text

The README's first command was broken in four places while every test passed (L-66), because an editable venv is not `uvx --from PyPI`. The fix was a CI job that runs the **doc-exact** text from a fresh environment, with assertions that self-arm when the fix they guard is unreleased.

## DAG position

Depends on `subsys.ops`, `subsys.scaffold` (init/uninstall), `subsys.hosts` and `subsys.hosttargets` (wiring), plus `modernize`, `release_check`, `nesting`, `mcp_probe`, `proposals`, `config`, `paths` and `tools-list`. The top of the dependency graph — nothing imports it.
