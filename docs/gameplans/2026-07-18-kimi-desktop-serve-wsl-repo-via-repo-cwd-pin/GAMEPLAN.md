# kimi-desktop-serve-wsl-repo-via-repo-cwd-pin Gameplan

> Created: 2026-07-18
> Status: Executing
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Compose the WSL-serving pin (UNC --repo + Windows-safe cwd)

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A pure helper composes the WSL repo's UNC path (\\wsl.localhost\<distro>\<repo-path>) from the repo root + $WSL_DISTRO_NAME, and the Windows-safe cwd (win_base) via winhost
- [x] server_entry/compose_entry can produce the pinned entry {command: clauderizer-mcp.exe, args:[--repo, <UNC>], cwd: <win_base>} when a pin is requested
- [x] The non-pinned path is byte-identical to today (repo-agnostic .exe / uvx / unregistrable); no default behavior change
- [x] New tests cover the UNC + cwd derivation and the pinned-entry composition per topology; full suite green (>= 889 passed)

### Phase 1: Self-heal preserves + refreshes an existing --repo/cwd pin

**Goal**: Make a pin durable: when the daimon entry already carries `--repo <X>` (a deliberate WSL-serving pin, hand-applied or previously composed), compose_entry/self-heal recompose it KEEPING X but re-probing the fresh Windows-native clauderizer-mcp.exe path and the Windows-safe cwd — so the pin survives every self-heal (init/status/doctor) and stays current across pipx reinstalls. A non-pinned entry keeps the current repo-agnostic behavior unchanged.
**Depends on**: Compose the WSL-serving pin (UNC --repo + Windows-safe cwd).

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] When the existing daimon entry carries --repo <X>, wire()/self_heal recompose KEEPING X and re-probing a fresh exe path + cwd (verified by test)
- [ ] A pinned entry survives repeated self-heal (init/status/doctor) — the --repo value is never clobbered to args:[]
- [ ] A pin with a stale exe path is refreshed to the current exe on self-heal (proves 'preserve X, refresh command')
- [ ] A non-pinned entry is untouched by the new logic (repo-agnostic behavior unchanged); full suite green

### Phase 2: init --serve-wsl-here trigger + init/doctor pinned messaging

**Goal**: Add the opt-in `clauderize init --serve-wsl-here` flag: when run from a WSL repo on a Windows desktop, it composes the initial pin (--repo <this repo's UNC> + Windows-safe cwd) into the daimon config. Update messaging: for the pinned repo, init/doctor drop the D-055 'unservable' UNC guidance; doctor handshakes the pinned command and REPORTS which repo it serves + the single-repo tradeoff (never silent). Guard: the flag is a no-op (with a clear message) when not on the WSL-repo+Windows-desktop combo.
**Depends on**: Self-heal preserves + refreshes an existing --repo/cwd pin.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] `clauderize init --serve-wsl-here` from a WSL repo on a Windows desktop writes the pinned daimon entry (--repo <this repo UNC> + Windows-safe cwd)
- [ ] The flag is a clear no-op off the WSL-repo+Windows-desktop combo (native/Windows-hosted repo) — never writes a bogus pin
- [ ] For the pinned repo, init/doctor no longer emit the D-055 'unservable' UNC guidance; doctor handshakes the pinned command and REPORTS which repo it serves + the single-repo tradeoff
- [ ] Tests cover: flag composes the pin, flag no-ops off-combo, doctor reports the pinned repo; full suite green

### Phase 3: Docs + 1.11.0 release + cascade + close-out

**Goal**: Document the pin in the kimi-desktop setup guide (the working override recipe + the single-repo tradeoff) and CROSS-HOST.md; CHANGELOG 1.11.0; version bump 1.10.0 → 1.11.0; full test run across the concern; cascade over D-057 / subsys.scaffold / subsys.mcp-server resolved; gameplan closed with a post-mortem; publish 1.11.0 to PyPI via the L-51 ritual.
**Depends on**: init --serve-wsl-here trigger + init/doctor pinned messaging.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] kimi-desktop setup guide + CROSS-HOST.md document the pin (recipe + the single-repo tradeoff + that it's opt-in and self-heal-preserving); doc-content test pins the claim
- [ ] CHANGELOG 1.11.0 entry; version bumped 1.10.0 → 1.11.0 (pyproject + __init__), editable reinstalled
- [ ] cascade over D-057 / subsys.scaffold / subsys.mcp-server resolved; full suite green
- [ ] gameplan closed with a post-mortem; 1.11.0 published to PyPI via the L-51 ritual (CI matrix green, release-check exit 0, tag==source, uvx --refresh verifies)
