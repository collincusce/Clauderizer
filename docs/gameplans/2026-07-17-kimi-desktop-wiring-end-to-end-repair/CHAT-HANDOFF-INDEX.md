# Chat Handoff Index — kimi-desktop-wiring-end-to-end-repair

> Last updated: 2026-07-17
> Status: All 6 phases complete

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
| 3 | Doctor MCP initialize-handshake smoke-test | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-3-HANDOFF.md |
| 4 | WSL-hosted-repo UNC guidance instead of dead registration | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs + release close-out | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-5-HANDOFF.md |

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

### Phase 3 — completed 2026-07-17

Doctor now verifies the kimi-desktop MCP command's CAPABILITY, not its mere presence in mcp.json (L-25). `kimidesktop.handshake_probe` spawns the registered command from a non-repo cwd (the way the app does — doctor passes the system tempdir), sends an MCP `initialize` over stdio (newline-delimited JSON-RPC, protocol 2024-11-05), parses `result.serverInfo`, and asserts `name == "clauderizer"`. It returns a three-state verdict wired into doctor's `verdict()`: a failed/mismatched handshake is drift (exit 2), and a command targeting an unreachable host (a wsl.exe shim with no interop) is honestly `unverifiable` (exit 3) — never a false green. `_spawn_target` makes this work cross-host by translating a `C:\` command to `/mnt/<drive>/...` for WSL interop; a green handshake against a different-version desktop install raises an advisory warn (the exe is a separate Windows pipx install, so a skew isn't same-install drift).

O-02 was resolved empirically: a WSL doctor CAN spawn the real Windows clauderizer-mcp.exe via the /mnt interop path and complete the handshake (serverInfo clauderizer 1.9.1) — so this is a real live verification, not unverifiable. Both directions confirmed against the live machine: the good entry → ok, a bogus exe → fail loudly. 12 new tests (ok, wrong-name, no-serverInfo+stderr tail, spawn-not-found, timeout, no-command, /mnt translation, native passthrough, wsl.exe-unverifiable, doctor-fails, doctor-passes, version-skew-advisory). Suite 857 → 868 → 869 passed, 5 skipped.

### Phase 4 — completed 2026-07-17

Refined the WSL-hosted-repo messaging so it reads as targeted guidance, not a dead registration. Since Phase 1 already made the composed entry the working Windows `.exe` (repo-agnostic, serving any Windows-hosted repo the app opens) and D-054 already emitted the UNC playbook, Phase 4 closed the remaining gap: the init and doctor warnings now state explicitly that the registered entry *still serves Windows-hosted repos* and only THIS WSL-hosted repo can't be served (the app spawns with a `\\wsl.localhost` UNC cwd it can't use). `setup_guide()` gained a "forward path (not yet automatic)" section naming `--repo`/`$CLAUDERIZER_REPO` as the mechanism by which a desktop spawning from a Windows-safe cwd could serve a UNC repo — with the honest caveat that the one repo-agnostic daimon file can't bake a per-repo `--repo` automatically, so the two existing fixes (Windows-filesystem clone, or Kimi Code CLI in WSL) remain the recommendation until the app exposes a safe spawn cwd.

3 new tests: the guide references the `--repo` forward path; `wire()` for the WSL+Windows combo registers the launchable `.exe` (not a dead/bare-uvx entry) while flagging `windows_side`; doctor's combo warning clarifies the registration stands. Verified live: the real doctor prints the refined "THIS repo … the registered entry still serves Windows-hosted repos" guidance. Suite 869 → 872 passed, 5 skipped.

### Phase 5 — completed 2026-07-17

Docs + release close-out for the kimi-desktop wiring repair. `setup_guide()` was rewritten to be host-topology-specific: the Windows-hosted-repo composition (absolute `clauderizer-mcp.exe`, with the reason a bare `uvx` can't spawn there), the macOS/Linux `uvx` form, and the WSL-repo UNC guidance — plus a "Persistence" section documenting that the app regenerates its `mcp.json` and that clauderizer self-heals on `init`/`doctor`/`status`, and the doctor `initialize`-handshake smoke-test. The stale bare-uvx example is gone. The two reference docs that had drifted were corrected: `docs/CROSS-HOST.md` (the "writes a bare uvx" claim → the topology-aware `.exe`/self-heal/handshake behavior) and `docs/TRUST.md` (a transparency note that the kimi-desktop self-heal is the one write outside the repo — detected-only, idempotent, never from a hook, opt-out honored).

Version bumped 1.9.1 → 1.10.0 (minor: new `--repo` surface, Windows-native composition, doctor handshake, self-heal — all backward-compatible), with a CHANGELOG entry; the editable install was reinstalled so dist-info matches (the 12 transient failures were exactly that stale-metadata parity check doing its job — L-23). All four acceptance criteria were demonstrably verified (evidence in the `acceptance-criteria-evidence` output), including AC4: `.mcp.json`/`.claude/` untouched by the branch and every Claude wiring check green at 1.10.0. Cascades over subsys.mcp-server and subsys.scaffold resolved (all dependents "no change needed" — additive/backward-compatible). Final suite: 873 passed, 5 skipped (from 840 at the gameplan's start; +33 tests). A real-machine bonus: the new version-skew advisory correctly flags that the user's Windows desktop pipx install is still 1.9.1 vs the 1.10.0 WSL engine — a `pipx upgrade clauderizer` on Windows after 1.10.0 ships will clear it.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A host that REGENERATES its own MCP config on context-switch and merges from no persistent source cannot bootstrap its own re-heal from within — once the entry is wiped the MCP server isn't loaded, so nothing on that host runs to re-register it. Durable registration must therefore ride EXTERNAL write-permitted entry points (other CLI runs on the same machine — init/doctor/status), made idempotent+atomic so re-applying is a safe no-op; never a hook (INVARIANT-06 keeps hooks read-only) nor the MCP read path (L-03). Corollary for VERIFYING such a registration (extends L-25): to prove a cross-OS command actually launches, spawn it the way the consumer will — a Windows `clauderizer-mcp.exe` registered for the desktop IS verifiable from WSL by translating the `C:\` command to its `/mnt/<drive>` interop path and completing the real MCP `initialize` handshake (asserting serverInfo.name), so it's a real green, not 'unverifiable'; reserve unverifiable for a target genuinely unreachable from the probing host (a wsl.exe shim with no interop). MCP stdio is newline-delimited JSON-RPC, not Content-Length framed. *(evidence: D-055 / gameplan 2026-07-17-kimi-desktop-wiring-end-to-end-repair: kimidesktop.self_heal on init/doctor/status; handshake_probe + _spawn_target /mnt translation (mcp_server.py, cli.py); live wipe→status→restore + real exe initialize handshake serverInfo clauderizer.)* (promoted 2026-07-17: L-59)
