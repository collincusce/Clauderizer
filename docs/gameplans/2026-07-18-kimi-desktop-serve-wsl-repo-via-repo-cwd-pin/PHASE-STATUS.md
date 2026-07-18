# kimi-desktop-serve-wsl-repo-via-repo-cwd-pin — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-18

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Compose the WSL-serving pin (UNC --repo + Windows-safe cwd) | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Self-heal preserves + refreshes an existing --repo/cwd pin | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-1-HANDOFF.md |
| 2 | init --serve-wsl-here trigger + init/doctor pinned messaging | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Docs + 1.11.0 release + cascade + close-out | ✅ COMPLETE | 2026-07-18 | 2026-07-18 | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
pin-compose-primitives: winhost.wsl_repo_to_unc(repo_root, distro) → \\wsl.localhost\<distro>\<path>; winhost.windows_safe_cwd(cfg, platform, home, users_dir) → win_base (C:\Users\<user>) from WSL, %USERPROFILE% on win32, None if underivable. kimidesktop.server_entry gained pin: str|None — when pin set + windows_host + exe found, composes {command: exe, args:[--repo, pin], cwd: <win_safe>} (cwd omitted if None); refactored to probe the exe once then branch pinned/repo-agnostic (non-pinned byte-identical). VERIFIED: composed pin for clauderizer-site == the agent's live-verified working entry (byte-for-byte). Suite 889→897.
```

### Phase 1 Outputs

```
durable-pin-sidecar: Pin durability via a sidecar (C-01): kimidesktop.SERVE_PIN_FILE = "clauderizer-serve.json" beside the daimon mcp.json (survives the app's regenerate-to-{} wipe). Helpers: serve_pin_path/read_serve_pin/write_serve_pin/clear_serve_pin (write via bespoke_hosts._atomic_write_json). KimiDesktopHost.compose_entry: pin = read_serve_pin(cfg) or _existing_repo_pin(cfg,servers_key) → server_entry(pin=...); so self-heal recomposes the pin (fresh exe + cwd) even after an app-wipe (sidecar), or preserves a hand-applied --repo same-session. bespoke_hosts.read_entry added (read current server entry). Verified: emptied mcp.json + sidecar → wire re-composes {command: <fresh exe>, args:[--repo, UNC], cwd}. Suite 897→902.
```

### Phase 2 Outputs

```
serve-wsl-here-live-verified: `clauderize init --serve-wsl-here` (init.py serve_wsl_here param + cli flag): writes the sidecar (UNC of this repo) before the wire loop, guarded to the WSL-repo+Windows-desktop combo (windows_side, $WSL_DISTRO_NAME set, root not under /mnt), else a "had no effect" note. BespokeHost.pinned_repo/clear_pin hooks; KimiDesktopHost overrides (pinned_repo = sidecar or existing --repo; unservable_reason returns None when pinned). doctor: prints "MCP registered, PINNED to serve <repo>" + a tradeoff advisory ("serves <repo> for EVERY project opened"). uninstall clears the sidecar. LIVE-VERIFIED on the real machine: applied the pin for clauderizer-site → live mcp.json is the exact pinned entry → the pinned command's cz_status returns clauderizer-site's status over UNC (host_profile node) → durable across 2/2 app-wipe→status cycles → doctor reports PINNED + tradeoff + green handshake. 4 tests; suite 902→906.
```

### Phase 3 Outputs

```
release-1.11.0: 1.11.0 published to PyPI via the L-51 ritual: pushed 386ebeb → CI matrix all 9 cells green (ubuntu/macos/windows × 3.11-3.13) → release-check exit 0 (v1.11.0 unclaimed across 4 registries) → tag v1.11.0 → GitHub Release → Publish-to-PyPI workflow success (Trusted Publishing) → verified fresh (uvx --refresh --from clauderizer==1.11.0 → clauderizer 1.11.0; PyPI index latest 1.11.0). Docs: setup_guide pin recipe, CROSS-HOST + README, CHANGELOG 1.11.0. Cascades resolved (scaffold, mcp-server — additive). Suite 907 passed, 5 skipped.
```

## Corrections Log

### C-01 — Phase 1

**Phase**: 1
**What gameplan said**: Self-heal preserves a pin by reading the existing --repo <X> from the daimon entry and recomposing keeping X.
**What was actually correct**: Reading the existing --repo alone does NOT survive the app's regenerate-to-{} wipe (O-01) — after a wipe the entry is empty, so there is no --repo to read and self-heal composes the repo-agnostic args:[], losing the pin. The durable pin target must live in a per-user SIDECAR (clauderizer-serve.json in the daimon home, which the app leaves alone when it regenerates mcp.json). compose_entry reads pin = sidecar-repo OR existing --repo (fallback for a hand-applied pin within a session).
**Why**: Verified live 2026-07-18: the live daimon mcp.json is currently {"mcpServers": {}} — the app wiped both clauderizer's entry AND the other agent's manual pin. A pin that only lives in mcp.json cannot survive that; the whole point of the feature is durability, so the pin choice must be stored where the app can't wipe it (a clauderizer-owned sidecar in the same per-user daimon home, detected-only + atomic like the mcp.json write, D-053).
