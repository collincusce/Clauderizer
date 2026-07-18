# Chat Handoff Index — kimi-desktop-serve-wsl-repo-via-repo-cwd-pin

> Last updated: 2026-07-18
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 889

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
| 0 | Compose the WSL-serving pin (UNC --repo + Windows-safe cwd) | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Self-heal preserves + refreshes an existing --repo/cwd pin | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | init --serve-wsl-here trigger + init/doctor pinned messaging | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs + 1.11.0 release + cascade + close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-18

Built the pure compose primitives for the WSL-serving pin. `winhost.wsl_repo_to_unc(repo_root, distro)` derives the `\\wsl.localhost\<distro>\<path>` UNC form of a WSL repo root, and `winhost.windows_safe_cwd(cfg, …)` returns the Windows-safe spawn cwd (the `C:\Users\<user>` win_base from the config path on WSL, `%USERPROFILE%` on native Windows, `None` if underivable). `kimidesktop.server_entry` gained an optional `pin` parameter: when a pin (a UNC path) is supplied and the host is a Windows daimon with a discoverable `clauderizer-mcp.exe`, it composes `{command: exe, args: ["--repo", pin], cwd: <win-safe>}`; otherwise it falls through to the unchanged repo-agnostic/uvx/unregistrable logic. I refactored the Windows branch to probe the exe once and then choose pinned-vs-agnostic, which keeps the non-pinned entry byte-identical (L-41/D-055 intact).

Correctness is anchored to reality, not just unit tests: composing a pin for `clauderizer-site` against the live daimon config reproduces the **exact** entry the other agent verified end-to-end (`C:\Users\rafaj\…\clauderizer-mcp.exe`, `--repo \\wsl.localhost\Ubuntu\home\ccusce\clauderizer-site`, `cwd C:\Users\rafaj`) — byte-for-byte. 8 new tests (UNC derivation, win-safe cwd for win32/WSL/underivable, pinned composition for WSL+win32, unpinned byte-identical, pin-ignored-off-Windows). Suite 889 → 897 passed, 5 skipped. The threading of the pin through `wire()`/`self_heal` (preserve) and `init --serve-wsl-here` (compose) is Phases 1–2.

### Phase 1 — completed 2026-07-18

Made the WSL-serving pin durable — and a live check forced the design to be right. I read the live daimon config mid-phase and found it had been wiped to `{"mcpServers": {}}` by the app (its regenerate-on-switch behavior, O-01), taking the other agent's manual pin with it. That falsified the planned "self-heal preserves the existing `--repo`" approach: after an app-wipe there is no `--repo` left to read (recorded as correction C-01). So the pin target now lives in a durable per-user **sidecar** — `clauderizer-serve.json` beside the daimon `mcp.json`, which the app leaves alone when it regenerates the config. `compose_entry` sources the pin as `read_serve_pin(cfg) or _existing_repo_pin(cfg)` (sidecar first for cross-wipe durability, the existing `--repo` as a same-session fallback for a hand-applied pin), and `wire()`/`self_heal` recompose it keeping the repo while re-probing a fresh exe + cwd.

Added `kimidesktop.serve_pin_path`/`read_serve_pin`/`write_serve_pin`/`clear_serve_pin` (atomic, via the framework's `_atomic_write_json`) and a generic `bespoke_hosts.read_entry` (read the current server entry). Verified the durability directly: an emptied `mcp.json` plus a sidecar makes `wire()` re-compose `{command: <fresh exe>, args:[--repo, UNC], cwd}` — the pin survives the wipe. Also verified a stale-exe pin is refreshed while the repo is preserved, and that an unpinned entry (no sidecar, no `--repo`) stays repo-agnostic. 5 new/updated tests; suite 897 → 902 passed, 5 skipped. The write path (`init --serve-wsl-here` composing the initial sidecar + pin) and the doctor reporting are Phase 2.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
