# Chat Handoff Index — kimi-desktop-wiring-end-to-end-repair

> Last updated: 2026-07-17
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 840

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Windows-native command composition (clauderizer-mcp.exe) | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Self-healing registration on every entry point | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Doctor MCP initialize-handshake smoke-test | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | WSL-hosted-repo UNC guidance instead of dead registration | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs + release close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-17

Decoupled repo discovery from the process cwd — the primitive the whole gameplan needs. `ops.repo_ctx()` now resolves the served repo from `$CLAUDERIZER_REPO` when set (walking up to the `.clauderizer/config.toml` marker like cwd discovery does), else falls back to `Path.cwd()`; a non-clauderized override raises a RuntimeError that names the source and points at `clauderize init`. `clauderizer-mcp` gained a `--repo <path>` flag (`_parse_repo`, last-wins, `--repo X` and `--repo=X` forms) that `main()` exports into `$CLAUDERIZER_REPO` before building the server, so the CLI flag beats an inherited env var. The `--version`/`--help` deterministic probe path (D3) is preserved and `--help` documents the new flag.

This lets a host that cannot set the repo as its spawn cwd — a Windows desktop serving a `\\wsl.localhost` UNC repo it can't `cd` into (D-054/D-055) — still point the stateless server at the right repo, and lets Phase 3's doctor smoke-test spawn from a non-repo cwd. Scope kept tight: the transcripts-dir discovery (ops.py ~979, a separate telemetry concern) was intentionally left on cwd. 7 new tests in tests/test_repo_override.py; suite 840 → 847 passed, 5 skipped; verified end-to-end from /tmp.

### Phase 1 — completed 2026-07-17

Replaced the bare-`uvx`-for-Windows composition (which can never spawn — kimi-desktop bundles uv.exe but not uvx.exe) with host-topology-aware probing for a Windows-native `clauderizer-mcp.exe`. `server_entry` now returns `(dict | None, warnings)`: on a Windows host (native win32, or a WSL init detecting a `/mnt/c` Windows-side config) it probes `pipx\venvs\clauderizer\Scripts` and `.local\bin` (which doubles as uv's tool-bin dir), registering the absolute path with `args: []`. From WSL it stats the `/mnt/c` mirror and registers the translated `C:\` spelling, deriving the profile from the config path (`_windows_profile_from_cfg`). win32-native adds a `which()` fallback for PATH/uv-tool installs. When no exe is found it returns `None` → `wire()` reports the new `unregistrable` status and `init` drops the setup guide — never a silent/bare-uvx entry. The macOS/Linux `uvx` path is untouched.

Verified end-to-end against the live machine (read-only): the composition reproduces the user's hand-fixed verified-good entry byte-for-byte (`C:\Users\rafaj\pipx\venvs\clauderizer\Scripts\clauderizer-mcp.exe`, `args: []`, zero warnings). Tests: replaced the old bare-uvx assertion with per-topology unit tests (WSL→translated exe, WSL no-exe→unregistrable, win32 exe, win32 which-fallback, win32 no-exe→unregistrable) + an init-drops-guide-on-unregistrable integration test; hardened the shared `_detected` helper to stub `server_entry` so the init/doctor/uninstall plumbing tests stay green on the Windows CI leg (L-23). Suite 847 → 852 passed, 5 skipped.

### Phase 2 — completed 2026-07-17

Made the daimon registration durable against the app regenerating its `mcp.json` on project switch. Investigation (O-01) confirmed there is NO persistent user-level MCP source the app merges from — `daimon-share/config.toml` and `daimon/config.json` carry no MCP keys, `kimi-agent/created-workspaces.json` is just a workspace registry, and the `.bak-2026-07-17` preserved our old bare-uvx entry, proving the wipe. So the fix is self-heal: `kimidesktop.self_heal()` (a never-raising wrapper over `wire()`) re-applies the idempotent+atomic entry, called on every `clauderize status` (silent) and `clauderize doctor` (reports "re-applied" when it changed), in addition to `init`.

Deliberately scoped away from two paths (C-01): the SessionStart hook (INVARIANT-06 keeps hooks read-only) and the MCP `cz_status` read op (L-03 keeps read ops non-mutating). This is also the only design that can work — once the app wipes the entry, the kimi-desktop MCP server isn't loaded, so it can't self-heal from within; the re-heal necessarily rides other `clauderize` CLI activity on the machine (a WSL `status`/`doctor`, Claude Code sessions). Live-verified end-to-end: after wiping the real config to `{"mcpServers":{}}`, a single `clauderize status` restored the exact verified-good `C:\...\clauderizer-mcp.exe` entry (backup insurance kept, not needed). 5 new tests (self-heal re-applies wiped entry, idempotent no-op, opt-out, never-raises, cmd_status + cmd_doctor heal); suite 852 → 857 passed, 5 skipped.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
