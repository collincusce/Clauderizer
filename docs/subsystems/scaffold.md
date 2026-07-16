---
id: subsys.scaffold
type: subsystem
version: 0.11.0
status: active
depends_on:
  - subsys.markdown-core@^0.1.0
  - subsys.profiles@^0.3.0
last_verified: 2026-07-16
---

# Scaffold

One idempotent command — `clauderize init` (`scaffold/init.py`, the `init()` entry) — clauderizes any repo, in any language, on native Linux/macOS or Windows→WSL. It wires the MCP server, the lifecycle hooks, the skills, the docs scaffold, and the config dial in a single pass, composing every command for the **session host of record** and **spawn-testing it before writing**.

## Idempotent & non-clobbering

Every step fills gaps without clobbering your content; a second run on an unchanged repo produces **zero diffs** (a tested invariant). The mechanisms (`init.py`):

- **Marker blocks** — `CLAUDE.md` and `AGENTS.md` get the *same* `clauderizer` stanza via `writer.upsert_marker_block`, so the rest of each file survives and the two cannot drift (L-16).
- **Key-scoped JSON merge** — `_register_mcp` only touches `mcpServers["clauderizer"]`; `_register_hook` replaces only clauderizer hook entries (matched by `hosts.is_hook_command`, not exact string) under each event, preserving unrelated hooks.
- **Exists-checks for docs** — `writer.create_if_absent` writes a doc only when absent; engine-owned files (skills, wrappers, the stanza) refresh via a diff-only rewrite.
- **`profile.lock.toml` is write-once** — created if absent, then preserved: it is the project's editable per-project command override (read back by `detect.load_for_repo`). Delete it to re-derive from a profile.

## What init writes

The detailed, authoritative file list lives in [`docs/TRUST.md`](../TRUST.md). In brief, `init()` produces: `.mcp.json`; `.claude/settings.json` (SessionStart + UserPromptSubmit hooks); `.claude/skills/clauderizer-*`; the `.clauderizer/` dir (`config.toml`, the hook wrapper, `kimi-setup.md`, `profile.lock.toml`, `index.json`); the `clauderizer` marker stanza in `CLAUDE.md` and `AGENTS.md`; and the `docs/` tree (the gameplan procedure plus a doc per enabled config module). It also gitignores `.clauderizer/index.json` and rebuilds the graph cache. A `--gameplan` seeds a first gameplan and records it as `active_gameplan`.

## Wiring that can't lie

The key design (`hosts.py`): wiring is composed for, and verified against, the host that actually spawns sessions — closing H-04's gap where WSL-composed wiring launched from Windows went unrecorded and `doctor` stayed green for a setup the session host could not launch.

- **Session host of record** — `native` | `windows-wsl:<distro>`. `init()` resolves it as: explicit `--session-host` flag > what `config.toml` already records > the host the existing `.mcp.json` wiring serves > `native`. Invalid values fail loudly before anything composes.
- **Prefer installed console scripts over `uvx`** — `_resolve_invocation` prefers the `clauderizer-mcp`/`clauderizer-hook` scripts next to the running interpreter (the venv/pipx case `shutil.which` misses), then a PATH lookup, falling back to the durable `uvx --from clauderizer` form only when nothing is on PATH.
- **Refuse uvx ephemeral-cache paths** — `_under_uv_cache` rejects console-script paths under uv's cache; such wiring dies on `uv cache clean`, so the durable `uvx --from clauderizer` form is wired instead.
- **Spawn-test every command before writing (H-04 guard)** — `init()` runs a real `--version` execution on both composed commands *before any write*. A command that exits non-zero raises `WiringRefused` and nothing is written; `unverifiable` (no interop path to the session host) proceeds with a loud warning naming the command to certify. The probe's `--version` output is an identity claim, not just an exit code, so a stale pin or a dead engine that exits 0 is still rejected.

## The breadcrumb wrapper

The registered SessionStart command is not the engine hook directly but a wrapper (`render_hook_wrapper`, written to `.clauderizer/hook.sh` or `hook.cmd`). The harness injects only a hook's **stdout** into session context, so a hook that cannot spawn is silent. The wrapper is the layer below the engine: it **always exits 0**, **anchors its cwd** to the repo it was generated for (`cd '<repo>'` / `cd /d "<repo>"`, H-09 — the executor chain does not reliably preserve the project cwd, and cmd.exe cannot hold a UNC cwd), and converts any engine failure or unreachable repo into a **one-line stdout breadcrumb** naming `clauderize doctor` instead of silence. After writing, `init()` re-probes the *registered* wrapper with a no-arg digest probe from a non-repo cwd — only the digest path proves the anchor, since `--version` answers before repo discovery.

## Split-host (Windows→WSL)

For `windows-wsl:<distro>`, the engine argv is prefixed with the `wsl.exe -d <distro>` shim. The registered hook command uses the **`//`-led path shape (shape C, H-08)**: `wsl.exe -d <d> //bin/sh //<repo>/.clauderizer/hook.sh`. The harness may execute the registered string through Git Bash, whose MSYS2 conversion rewrites `/`-led POSIX args into Windows paths (`/bin/sh` → `C:/Program Files/Git/usr/bin/sh`, exit 127 inside the distro) but skips `//`-led args as UNC-form; Linux collapses `//` to `/`. The shape carries zero quote surface, so it also survives cmd.exe and PowerShell verbatim (executor matrix: `scripts/wiring_matrix.ps1`).

Doctor traverses the **real consumer leg (D-010)**: it runs the direct `wsl.exe` round-trip first (deepest engine-identity diagnosis), then the registered command *through Git Bash from a non-repo cwd*, requiring both in-band identity and the digest — because the direct argv probe stayed green through the entire H-08 outage. When Git Bash is unreachable it reports an honest **`unverifiable`** (doctor's exit 3) rather than a green that speaks for a leg nothing traversed.

## Place in the DAG

`subsys.scaffold` depends on `subsys.profiles` (it calls `profiles.detect` to pick the host language and derive `profile.lock.toml`) and uses the markdown-core writers (`create_if_absent`, `upsert_marker_block`). `feat.init-cli` is the CLI feature layered over `init()`.
