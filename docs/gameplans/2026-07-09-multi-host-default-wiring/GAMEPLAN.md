# 2026-07-09-multi-host-default-wiring Gameplan

> Created: 2026-07-09
> Status: Planning
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

**O-01.** _(phase 2)_ Which env/process markers reliably identify Grok vs Cursor vs Claude Code vs Copilot vs Codex at runtime? Measure on this machine + document fallbacks.

**O-02.** _(phase 0)_ Does default multi-emit of ~8 project config trees (.cursor, .vscode, .continue, …) create unacceptable repo clutter for strangers? Mitigations: gitignore templates, --hosts minimal, or docs that these files are intentional dual-entry.

**O-03.** _(phase 1)_ Back-compat: repos with host_target=cursor only — on upgrade, expand to multi or keep singleton until re-init? Prefer modernize advisory + next init expands.

## Phase Breakdown

### Phase 0: Model: wiring set vs session routing

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Documented split: enabled_hosts (wiring) vs session_agent (runtime) with D-046/D-047/D-048 referenced
- [ ] Open items for detect signals and file-clutter tradeoffs recorded
- [ ] No production code claims exclusive --host is still the primary UX

### Phase 1: Config + emit multi-host default

**Goal**: Change init so default wires all project-level hosts non-destructively; --host scopes; config schema for enabled_hosts with host_target back-compat.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Bare init (no --host) emits claude-code wiring PLUS all auto-write host MCP configs (path-safe) plus guide-only setup docs
- [ ] --host X emits only that host's footprint (scope filter)
- [ ] Config persists enabled_hosts; legacy host_target= still loads
- [ ] INVARIANT-07: Claude SessionStart path unchanged when multi-wiring
- [ ] Unit tests: multi init idempotent; second host merge preserves foreign keys

### Phase 2: Runtime session-agent detection + bootstrap safety

**Goal**: Detect which agent is driving the session for P7/hook silence; multi-safe default never leaves Grok/Cursor dark because Claude files exist on disk.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] detect_session_agent returns a host id or multi-safe hook-less default
- [ ] Grok/Cursor sessions get should_inject True when undelivered even if .claude/ exists on disk
- [ ] Claude Code detected sessions keep delivers_status_via_hook True
- [ ] Tests cover env/marker detection and multi-safe default

### Phase 3: Doctor configure-on-demand + uninstall/docs/ship

**Goal**: Doctor reports per-host readiness + configure steps; uninstall multi-safe; README teaches multi-host default; suite green; ship.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Doctor lists per-host readiness + configure steps (Grok trust, Amp approve, guide-only TOML) as advisories
- [ ] Uninstall bare removes multi footprint; --host still scoped
- [ ] README/docs teach multi-host default; --host as optional scope
- [ ] Full suite green; CHANGELOG notes
