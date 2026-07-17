# kimi-desktop-daimon-host-mcp-autowrite Gameplan

> Created: 2026-07-17
> Status: Complete
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

### Phase 0: Confirm the daimon runtime contract + design cross-platform detection

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Daimon runtime-home mcp.json path confirmed for Windows; macOS/Linux candidate paths chosen (best-effort, marked to confirm)
- [x] The WSL->Windows-desktop case is designed: detect via /mnt/c/Users/<user>/AppData, and emit a wsl.exe -d <distro> wrapped command (reuses session.running_inside_wsl/current_distro)
- [x] The D-031 exception is recorded (D-053) with its safety mitigations: detected-only, non-destructive/atomic, robust command
- [x] Command-robustness design decided: portable uvx + uvx-absolute resolution + when-to-wsl-wrap

### Phase 1: Bespoke kimi-desktop detection + auto-write emitter

**Goal**: A bespoke emitter (absolute per-user path, like grok's): resolve the daimon runtime-home mcp.json cross-platform (Windows %APPDATA%; macOS ~/Library/Application Support; Linux ~/.config; and the WSL->Windows case via /mnt/c/Users/<user>/AppData). DETECTED-ONLY (write only if the runtime home already exists). Non-destructive atomic merge (preserve other mcpServers, temp-write+rename). Robust command: portable uvx --from clauderizer[mcp] clauderizer-mcp, uvx resolved to an absolute path when needed, and a wsl.exe -d <distro> wrapper when init runs inside WSL but the config is Windows-side. Tests with mocked home dirs for each platform + the WSL case + non-destructive merge (L-25 both directions).
**Depends on**: Confirm the daimon runtime contract + design cross-platform detection.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A resolver returns the daimon runtime-home mcp.json path per platform (Windows/macOS/Linux) and for the WSL->Windows case; returns None when no runtime home exists
- [x] emit auto-writes clauderizer into that mcp.json non-destructively + atomically (temp-write+rename), preserving other servers; detected-only (never creates the dir)
- [x] The written command is portable and robust: uvx --from clauderizer[mcp] clauderizer-mcp, absolute-uvx when resolvable, wsl.exe-wrapped when running inside WSL against a Windows-side config
- [x] Tests cover each platform (mocked home), the WSL case, non-destructive merge, and detected-only (both directions, L-25)
- [x] Full suite green in a fresh venv

### Phase 2: Wire kimi-desktop into init, doctor, uninstall

**Goal**: init auto-writes the desktop registration when detected (else emits kimi-desktop-mcp-setup.md), idempotent + non-destructive. doctor reports the desktop host state (wired / unwired / not-detected) and warns LOUDLY on missing uvx, unwritable config, or an undetected-but-app-present home — never silent green. uninstall removes only the clauderizer entry from the runtime-home. configure_hints for kimi-desktop. Tests: init auto-writes on a detected home, guide-only fallback when absent, doctor surfaces state, uninstall is surgical, second run = zero diffs.
**Depends on**: Bespoke kimi-desktop detection + auto-write emitter.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] init auto-writes the desktop registration when the runtime home is detected, and emits kimi-desktop-mcp-setup.md otherwise; idempotent (second run = zero diffs)
- [x] doctor reports the kimi-desktop host state and warns loudly on missing uvx / unwritable config / undetected-app (never silent green)
- [x] uninstall removes only the clauderizer entry from the runtime-home mcp.json, preserving others
- [x] configure_hints + the generated guide cover the runtime-home path, session-restart, no-hook-lane, and the WSL variant
- [x] Full suite green in a fresh venv

### Phase 3: Docs, ship 1.9.0, dogfood close

**Goal**: Docs sweep: CROSS-HOST.md (new kimi-desktop row + host count; note the D-053 exception + the WSL command variant), README host list, VISION, the generated setup guide. CHANGELOG 1.9.0; bump pyproject + __version__ to 1.9.0 in lockstep. Bump subsys.scaffold; cz_cascade + resolve. Verify full suite in a FRESH venv. Close via the clauderizer-close-gameplan skill (cz_audit blind). Then release: merge to main -> tag v1.9.0 -> CI green -> GitHub Release -> PyPI -> verify.
**Depends on**: Wire kimi-desktop into init, doctor, uninstall.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Docs swept: CROSS-HOST kimi-desktop row + host count + D-053 note + WSL variant; README host list; VISION; generated guide
- [x] pyproject AND __version__ bumped to 1.9.0 in lockstep (cz_audit + guard test green)
- [x] subsys.scaffold bumped; cz_cascade run and resolved
- [x] Gameplan closed via the clauderizer-close-gameplan skill with cz_audit run; findings addressed; post-mortem written
- [x] Released: merged to main, tag v1.9.0, CI green (9 cells), GitHub Release published, clauderizer 1.9.0 verified live on PyPI
