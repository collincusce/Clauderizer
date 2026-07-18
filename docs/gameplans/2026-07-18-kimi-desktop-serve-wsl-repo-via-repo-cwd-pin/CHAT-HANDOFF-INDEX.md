# Chat Handoff Index — kimi-desktop-serve-wsl-repo-via-repo-cwd-pin

> Last updated: 2026-07-18
> Status: All 4 phases complete

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
| 2 | init --serve-wsl-here trigger + init/doctor pinned messaging | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs + 1.11.0 release + cascade + close-out | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-18

Built the pure compose primitives for the WSL-serving pin. `winhost.wsl_repo_to_unc(repo_root, distro)` derives the `\\wsl.localhost\<distro>\<path>` UNC form of a WSL repo root, and `winhost.windows_safe_cwd(cfg, …)` returns the Windows-safe spawn cwd (the `C:\Users\<user>` win_base from the config path on WSL, `%USERPROFILE%` on native Windows, `None` if underivable). `kimidesktop.server_entry` gained an optional `pin` parameter: when a pin (a UNC path) is supplied and the host is a Windows daimon with a discoverable `clauderizer-mcp.exe`, it composes `{command: exe, args: ["--repo", pin], cwd: <win-safe>}`; otherwise it falls through to the unchanged repo-agnostic/uvx/unregistrable logic. I refactored the Windows branch to probe the exe once and then choose pinned-vs-agnostic, which keeps the non-pinned entry byte-identical (L-41/D-055 intact).

Correctness is anchored to reality, not just unit tests: composing a pin for `clauderizer-site` against the live daimon config reproduces the **exact** entry the other agent verified end-to-end (`C:\Users\rafaj\…\clauderizer-mcp.exe`, `--repo \\wsl.localhost\Ubuntu\home\ccusce\clauderizer-site`, `cwd C:\Users\rafaj`) — byte-for-byte. 8 new tests (UNC derivation, win-safe cwd for win32/WSL/underivable, pinned composition for WSL+win32, unpinned byte-identical, pin-ignored-off-Windows). Suite 889 → 897 passed, 5 skipped. The threading of the pin through `wire()`/`self_heal` (preserve) and `init --serve-wsl-here` (compose) is Phases 1–2.

### Phase 1 — completed 2026-07-18

Made the WSL-serving pin durable — and a live check forced the design to be right. I read the live daimon config mid-phase and found it had been wiped to `{"mcpServers": {}}` by the app (its regenerate-on-switch behavior, O-01), taking the other agent's manual pin with it. That falsified the planned "self-heal preserves the existing `--repo`" approach: after an app-wipe there is no `--repo` left to read (recorded as correction C-01). So the pin target now lives in a durable per-user **sidecar** — `clauderizer-serve.json` beside the daimon `mcp.json`, which the app leaves alone when it regenerates the config. `compose_entry` sources the pin as `read_serve_pin(cfg) or _existing_repo_pin(cfg)` (sidecar first for cross-wipe durability, the existing `--repo` as a same-session fallback for a hand-applied pin), and `wire()`/`self_heal` recompose it keeping the repo while re-probing a fresh exe + cwd.

Added `kimidesktop.serve_pin_path`/`read_serve_pin`/`write_serve_pin`/`clear_serve_pin` (atomic, via the framework's `_atomic_write_json`) and a generic `bespoke_hosts.read_entry` (read the current server entry). Verified the durability directly: an emptied `mcp.json` plus a sidecar makes `wire()` re-compose `{command: <fresh exe>, args:[--repo, UNC], cwd}` — the pin survives the wipe. Also verified a stale-exe pin is refreshed while the repo is preserved, and that an unpinned entry (no sidecar, no `--repo`) stays repo-agnostic. 5 new/updated tests; suite 897 → 902 passed, 5 skipped. The write path (`init --serve-wsl-here` composing the initial sidecar + pin) and the doctor reporting are Phase 2.

### Phase 2 — completed 2026-07-18

Shipped the opt-in trigger and the pinned messaging, then proved the whole feature live on the real machine. `clauderize init --serve-wsl-here` (a new flag on init) derives this repo's `\\wsl.localhost` UNC and writes the durable sidecar before the wire loop, guarded to the WSL-repo + Windows-desktop combo (windows_side daimon, `$WSL_DISTRO_NAME` set, repo not under `/mnt`); off-combo it's a clear no-op note. The framework gained generic `pinned_repo`/`clear_pin` hooks (KimiDesktopHost implements them from the sidecar); `unservable_reason` returns `None` when pinned (the pinned repo IS served, so the D-055 UNC guidance is suppressed); `doctor` prints "MCP registered, PINNED to serve <repo>" plus the single-repo tradeoff advisory ("serves <repo> for EVERY project opened, not the one you open"); and `uninstall` clears the sidecar.

Live end-to-end on the reporting machine: applying the pin for `clauderizer-site` produced the exact entry the desktop agent had verified, the pinned command's `cz_status` returned clauderizer-site's real status over the UNC path (`host_profile: node`), the pin survived 2/2 app-wipe→`clauderize status` cycles (re-composed from the sidecar — the C-01 durability win), and `doctor` reported the pin + tradeoff with a green initialize handshake. The user's `clauderizer-site` is now pinned; a desktop restart gives it the full `cz_*` toolset. 4 new tests (flag writes the sidecar, off-combo no-op, doctor reports the pin, uninstall clears it); suite 902 → 906 passed, 5 skipped.

### Phase 3 — completed 2026-07-18

Documented the opt-in pin and shipped 1.11.0. `setup_guide()` now presents `clauderize init --serve-wsl-here` as the recommended fix for a WSL repo on the Windows desktop (replacing the D-055 "forward path (not yet automatic)" prose), with the override shape, the durable sidecar, the single-repo tradeoff, and the unpin path; `CROSS-HOST.md` and the README carry the same, and a doc-content test pins the claim (L-55). A latent f-string brace bug in the guide's JSON example (single `{}` → runtime `NameError`) was caught by the suite and fixed. Version bumped 1.10.0 → 1.11.0 with a CHANGELOG entry; cascades over `subsys.scaffold`/`subsys.mcp-server` resolved (additive/opt-in).

1.11.0 was published to PyPI via the full L-51 ritual: push → CI matrix green on all 9 cells (ubuntu/macos/windows × 3.11–3.13) → `release-check` exit 0 (v1.11.0 unclaimed across all four registries) → tag → GitHub Release → Trusted-Publishing workflow success → verified fresh (`uvx --refresh --from clauderizer==1.11.0` → clauderizer 1.11.0; PyPI index latest 1.11.0; the transient 1.10.0 read was CDN propagation lag that cleared in seconds). Final suite: 907 passed, 5 skipped (from 889 at the gameplan's start; +18 tests).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Durable per-host OVERRIDE state must NOT live only in a config the host regenerates. When a host wipes/regenerates its own config on context-switch (kimi-desktop's mcp.json → {}, O-01), any override you wrote there (a --repo pin, a custom cwd) is gone — and self-heal that reads the override BACK from the current config finds nothing and reverts to the default. Fix: record the override in a durable SIDECAR the host leaves alone (a clauderizer-owned file beside the config that the host's regeneration doesn't touch), and have self-heal RE-COMPOSE the override from the sidecar (re-probing volatile bits like an exe path). Reading the override from the live config is only a same-session fallback, never durability. Corollary (extends L-50): before building on a hypothesized host capability, VERIFY it against the host's actual source + a live probe — the daimon 'honors a per-server cwd' hypothesis was confirmed by grepping the app bundle's config normalizer AND a live initialize+cz_status handshake serving a real WSL repo over UNC, not assumed; and the tempting-but-absent alternative (an in-WSL 'executor' value) was ruled out by reading the bundle's validated executor set (shell/bash/local/native/kaos), not guessed. *(evidence: D-057: kimidesktop.clauderizer-serve.json sidecar + read_serve_pin/write_serve_pin; compose_entry pin = read_serve_pin(cfg) or _existing_repo_pin(cfg); live-verified durable across 2/2 app-wipe→status cycles; daimon cwd-honor confirmed in bundle c-UL5Q755D.js + a live cz_status over UNC.)* (promoted 2026-07-18: L-61)
