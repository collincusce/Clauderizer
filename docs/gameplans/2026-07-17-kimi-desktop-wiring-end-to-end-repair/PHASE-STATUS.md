# kimi-desktop-wiring-end-to-end-repair — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-17

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Windows-native command composition (clauderizer-mcp.exe) | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Self-healing registration on every entry point | ✅ COMPLETE | 2026-07-17 | 2026-07-17 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Doctor MCP initialize-handshake smoke-test | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | WSL-hosted-repo UNC guidance instead of dead registration | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Docs + release close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
repo-override-surface: clauderizer-mcp `--repo <path>` and `$CLAUDERIZER_REPO` both resolve the served repo; precedence --repo > env > cwd. Impl: ops.repo_ctx() reads $CLAUDERIZER_REPO (src/clauderizer/ops.py:35), mcp_server._parse_repo + main() export the flag into env (src/clauderizer/mcp_server.py). Non-clauderized override raises RuntimeError naming CLAUDERIZER_REPO + `clauderize init`.
test-baseline-after-p0: 847 passed, 5 skipped (was 840). New file tests/test_repo_override.py (7 tests). End-to-end drive: from /tmp, CLAUDERIZER_REPO=/home/ccusce/Clauderizer → repo_ctx resolves root correctly, exit 0.
```

### Phase 1 Outputs

```
windows-exe-composition: kimidesktop.server_entry now returns (dict|None, warnings). Windows host (win32 OR in_wsl+windows_side) probes _WIN_EXE_SUBPATHS = pipx/venvs/clauderizer/Scripts + .local/bin (the latter doubles as uv tool bin) for clauderizer-mcp.exe. From WSL: _windows_profile_from_cfg derives (mnt_base,/mnt/c/Users/<user>; win_base, <DRIVE>:\Users\<user>) from the cfg path (drive = users_dir.parts[-2]); registers translated C:\ command. win32-native falls back to which(). No .exe → entry None, status 'unregistrable', guide dropped, NEVER bare uvx. Non-Windows uvx path unchanged. wire() gained exists= inject + 'unregistrable' status; init.py routes failed|unregistrable → guide.
real-machine-verification: Read-only compose against the live env (WSL_DISTRO_NAME=Ubuntu): detect_config → /mnt/c/Users/rafaj/AppData/Roaming/kimi-desktop/.../mcp.json; server_entry → {"command":"C:\\Users\\rafaj\\pipx\\venvs\\clauderizer\\Scripts\\clauderizer-mcp.exe","args":[]}, zero warnings — byte-identical to the user's verified-good hand-fixed entry. Real exe present at /mnt/c/Users/rafaj/pipx/venvs/clauderizer/Scripts/clauderizer-mcp.exe (+ .local/bin symlink). Suite 847→852 passed, 5 skipped.
```

### Phase 2 Outputs

```
self-heal-mechanism: kimidesktop.self_heal() wraps wire() (never raises). Called by cmd_status (silent, src/clauderizer/cli.py cmd_status) and cmd_doctor (reports "re-applied" when changed; self-heals BEFORE the presence report). init already wires. NOT called from the SessionStart hook (INVARIANT-06) nor MCP cz_status (L-03) — see C-01. O-01 finding: no persistent user-level MCP source; app regenerates home/mcp.json on project switch. Live-verified: wipe entry → `clauderize status` → exact C:\ .exe entry restored.
```

## Corrections Log

### C-01 — Phase 2

**Phase**: 2
**What gameplan said**: Re-apply/repair the daimon registration whenever any entry point runs — init/doctor/status/hook.
**What was actually correct**: Self-heal rides init/doctor/status (the write-permitted CLI entry points) but NOT the SessionStart hook. Also NOT the MCP cz_status read op.
**Why**: INVARIANT-06 requires every hook handler to be read-only and never mutate/block a session — a self-heal write from the hook would violate it. L-03 requires MCP read ops to never mutate/lock. The kimi-desktop host itself has no hook surface, and its MCP server can't bootstrap a wiped registration from inside (the server isn't loaded once the entry is gone), so the durable self-heal necessarily comes from OTHER clauderize CLI runs on the same machine (a WSL `clauderize status`/`doctor`, or Claude Code activity) — exactly the write-permitted entry points. Verified live: after the app wipes the entry, one `clauderize status` restores the exact verified-good C:\ .exe entry.
