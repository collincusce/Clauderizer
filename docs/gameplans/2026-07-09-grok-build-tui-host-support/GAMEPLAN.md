# grok-build-tui-host-support Gameplan

> Created: 2026-07-09
> Status: Complete
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

Make **Grok Build TUI** a first-class Clauderizer `host-target` so dogfooding and
consumer projects (e.g. viderizer) can run Clauderizer under Grok without lying
about Tier-1 SessionStart injection. Grok has lifecycle hooks, AGENTS.md, and MCP
(`.mcp.json` + project config), but **passive hook stdout is not injected into
model context** — so best automatic delivery is **P7 server bootstrap + AGENTS.md
floor**, not the Claude Code digest path. Work is strictly additive
(INVARIANT-07): Claude Code wiring never regresses.

## Subsystems Touched

- `subsys.scaffold` (init `--host grok`, emitters)
- `subsys.mcp-server` / `session.py` routing (bootstrap vs `_HOOK_HOSTS`)
- hosttargets / CROSS-HOST matrix / doctor (cli)
- docs: CROSS-HOST.md, README host list, CHANGELOG

## Source-of-Truth Captures

| Capture | Value | As of |
|---------|-------|-------|
| Package version | **1.5.3** (`pyproject.toml` / installed dogfood venv) | 2026-07-09 |
| Procedure version | **1.6.0** (`.clauderizer/config.toml`) | 2026-07-09 |
| Host profile | **python** | config |
| Current host-target (dogfood) | **claude-code** | config |
| Session-host (dogfood) | **windows-wsl:ubuntu** | config |
| Baseline tests (status digest) | **0** reported by status bundle (suite still run for ship) | 2026-07-09 |
| Prior host count (CROSS-HOST) | **11** in-scope (no `grok`) | gameplan 2026-06-21 close |
| Grok Hook→ctx | **no** (docs: SessionStart stdout ignored) | Grok user-guide 10-hooks.md |
| Grok MCP | loads **`.mcp.json`** + project **`.grok/config.toml`** | Grok 07-mcp-servers.md |
| Grok AGENTS.md | **native** (project rules) | Grok 12-project-rules.md |
| Live field session | Grok in WSL on viderizer: MCP `cz_*` works; no auto-digest | 2026-07-09 |

## Amendments

### A-001 — Collapse duplicate Phase 0/1 from planning scaffold

- **Date**: 2026-07-09
- **Affected sections**: Phase Breakdown; PHASE-STATUS.md
- **Affected phases**: 0–5 renumbered to 0–4
- **Triggered by**: `cz_create_gameplan(first_phase=…)` already created Phase 0; a second `cz_add_phase` with the same name produced a duplicate row
- **What changed**: Single Phase 0 (capability audit); subsequent phases renumbered 1–4 (registry → emitters → doctor/docs → ship). Open-item phase tags re-aligned.
- **Why**: Planning-time scaffold bug; clean phase table before any execution.

## Decisions

### D1 — Grok is a host-target with lifecycle hooks but governance-only context injection (not Tier-1)

**Context**: Grok Build TUI documents SessionStart/UserPromptSubmit and loads Claude-compat hooks from .claude/settings.json and native .grok/hooks/*.json. Passive hooks (SessionStart included) explicitly ignore stdout — digest text does not enter model context. That matches Cursor's governance-hook pattern in D-034, not Claude Code / kimi Tier-1.
**Decision**: Classify host-target id `grok` with hooks=governance (events SessionStart, UserPromptSubmit, PreCompact, PostCompact available for side-effects/scrollback) and Hook→ctx=no. best_tier=3 if MCP prompts surface as slash commands after live check, else 4 (AGENTS.md floor + MCP tools + P7 server bootstrap). NEVER put `grok` in session._HOOK_HOSTS — that would suppress bootstrap and leave cold sessions dark.
**Consequences**: init/doctor/docs can claim automatic orientation only via P7 bootstrap + AGENTS.md floor, not SessionStart digest. When xAI adds stdout→context (or additionalContext JSON), promote via amendment + move into _HOOK_HOSTS and re-tier to 1.
**Evidence**: Grok user-guide 10-hooks.md Passive Hooks: stdout ignored for SessionStart; 07-mcp-servers.md loads .mcp.json; 12-project-rules.md loads AGENTS.md; session.py _HOOK_HOSTS / _PROMPT_HOSTS pattern
**Status**: active (2026-07-09)

### D2 — Grok MCP write policy: prefer portable .mcp.json; optional project .grok/config.toml is guide-only TOML

**Context**: Grok natively merges project .mcp.json (standard MCP format) and also supports project .grok/config.toml [mcp_servers.*] (TOML). Clauderizer has no stdlib TOML writer (CROSS-HOST O-04 / D-031). Dogfood .mcp.json often carries wsl.exe absolute paths that break a native-Linux Grok session.
**Decision**: For host-target `grok`, treat MCP registration as satisfied by the portable path-safe .mcp.json command (uvx --from clauderizer[mcp] clauderizer-mcp) already used for the substrate. Ship a guide (or append-only marker stanza) for .grok/config.toml; do not structured-rewrite TOML. Auto-write ONLY JSON hook files under .grok/hooks/ when emitting native Grok wiring. Document that dual Claude+Grok machines must not commit machine-specific wsl.exe MCP args (D-031).
**Consequences**: No new TOML dependency. Doctor for grok checks: AGENTS.md floor present, path-safe .mcp.json (or guide noted), optional .grok/hooks/clauderizer.json present after init --host grok, host_target=grok not in _HOOK_HOSTS.
**Evidence**: Grok 07-mcp-servers.md project .grok/config.toml + .mcp.json merge order; hosttargets.py is_path_safe / guide-only TOML pattern for codex/kimi
**Status**: active (2026-07-09)

### D3 — Session-host composition stays orthogonal: Grok-native hooks never force wsl.exe

**Context**: D-028: session-host × host-profile × host-target are independent. This machine's Claude sessions use windows-wsl; Grok Build often runs inside WSL Ubuntu natively. Registering wsl.exe-shimmed SessionStart for a Grok-in-Linux session fails or double-wraps.
**Decision**: When emitting Grok hooks (.grok/hooks/*.json), the registered command is composed for the *configured session_host* of the repo OR, if session_host is windows-wsl and the Grok process is native Linux, prefer the POSIX wrapper path (`/bin/sh .clauderizer/hook.sh` relative/abs anchored). Document dual-entry setups: Claude keeps .claude/settings.json with session_host composition; Grok uses .grok/hooks with a native-safe command. Never silently rewrite Claude Code wiring (INVARIANT-07).
**Consequences**: May need a small hosts.compose branch or grok-specific emitter that skips wsl.exe when writing .grok/hooks. Consumption proof must run from a real Grok session in WSL.
**Evidence**: hosts.py compose/session_host; viderizer .claude/settings.json wsl.exe command; live Grok session 2026-07-09 in /home/ccusce/viderizer
**Status**: active (2026-07-09)

## Open Items

**O-01.** _(phase 0)_ Confirm live whether Grok surfaces MCP prompts as slash commands (/cz-status). That decides best_tier 3 vs 4 in the matrix (tools alone do not make Tier 3). _(resolved 2026-07-09: best_tier=4. Grok 0.2.93 user-guide 04-slash-commands.md: slash sources are shell builtins + pager builtins + SKILL.md skills only — no MCP prompts. 07-mcp-servers.md: model tool discovery is search_tool/use_tool only. Clauderizer still exposes MCP prompt cz-status for hosts that surface it, but Grok does not — do not claim Tier 3. Re-spot-check in Phase 4 consumption proof with /cz-status attempt.)_

**O-02.** _(phase 0)_ Confirm whether folder-trust is required for project .grok/hooks and project .mcp.json on Grok; document trust step in doctor/setup guide. _(resolved 2026-07-09: Folder-trust IS required for project .grok/hooks and project-local MCP/LSP. Grok 10-hooks.md: first open needs /hooks-trust or --trust; decision in ~/.grok/trusted_folders.toml; same gate for repo-local MCP. Document in doctor/setup guide for host_target=grok. Global ~/.grok/hooks always trusted.)_

**O-03.** _(phase 2)_ Dual-entry layout: when repo session_host=windows-wsl for Claude, what exact command string should .grok/hooks use for Grok-in-WSL? Measure with a real /hooks annotation + exit code. _(resolved 2026-07-09: Measured command for .grok/hooks: `cd "${GROK_WORKSPACE_ROOT}" && uvx --from clauderizer clauderizer-hook`. Always native-safe (no wsl.exe) regardless of repo session_host=windows-wsl used for Claude. Dual-entry: Claude keeps .claude/settings.json with session_host composition; Grok uses portable uvx + GROK_WORKSPACE_ROOT anchor. Evidence: temp-repo init + unit tests.)_

**O-04.** _(phase 4)_ Ship version: patch 1.5.4 vs next minor — decide from CHANGELOG cadence and whether matrix/docs alone warrant minor. _(resolved 2026-07-09: Recommend patch 1.5.4 (matches 1.5.x field-train cadence; additive host-target, no API break). Publish deferred pending user OK — code + CHANGELOG Unreleased ready; do not tag/PyPI without explicit go-ahead.)_

**O-05.** _(phase 4)_ xAI feature ask: SessionStart stdout (or additionalContext JSON) into model context — track as external dependency for future Tier-1 promotion; not blocking this gameplan.

## Phase Breakdown

### Phase 0: Capability audit + honesty constraints

**Goal**: Lock the Grok host capability row from primary docs + live probe; Source-of-Truth table is complete; no code claims Tier-1 Hook→ctx.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | Write/verify CROSS-HOST draft row for `grok` (MCP prims, hooks, Hook→ctx, AGENTS.md, MCP reg, best_tier, write policy) from Grok docs + live session notes | S |
| 0.2 | Resolve O-01 (MCP prompts as slash?) and O-02 (folder-trust) with evidence in Outputs Registry | S |
| 0.3 | Confirm D1–D3 still match measured facts; open amendments if not | S |

**Exit criteria**:
- [x] CROSS-HOST §3 has a draft grok row with Hook→ctx=no and best_tier ∈ {3,4} justified by O-01
- [x] Source-of-Truth Captures table has no placeholders
- [x] O-01 and O-02 resolved or explicitly deferred with owner note
- [x] No production code change claims Tier-1 for grok

### Phase 1: Registry + session routing

**Goal**: Add host-target `grok` to valid targets, CROSS-HOST matrix (committed), and session.py routing (**not** in `_HOOK_HOSTS`; bootstrap enabled).
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | `valid_host_targets` / parse / detect hooks for `grok` | S |
| 1.2 | `session.py`: route grok like governance/prompt hosts (bootstrap on); unit tests on `delivers_status_via_hook` / `best_tier` | M |
| 1.3 | Commit CROSS-HOST matrix row + D-045 already recorded | S |

**Exit criteria**:
- [x] clauderize init --host grok accepts the id (no unknown-host error)
- [x] delivers_status_via_hook("grok") is False and should_inject("grok") is True when undelivered (tests)
- [x] best_tier("grok") matches the Phase-0 matrix decision (tests)
- [x] INVARIANT-07 regression: claude-code still in _HOOK_HOSTS with best_tier 1

### Phase 2: Emitters — `.grok/hooks` + portable MCP path

**Goal**: `init --host grok` emits path-safe `.mcp.json` (or verifies existing), auto-writes `.grok/hooks/clauderizer.json` with a **native-safe** hook command, ships TOML guide if needed; never clobbers Claude Code wiring.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | HostEmitter / emit path for `.grok/hooks/*.json` (JSON auto-write) | M |
| 2.2 | Native-safe command composition (D3); resolve O-03 with measured argv | M |
| 2.3 | Portable `.mcp.json` path-safety (D-031); guide for `.grok/config.toml` | S |
| 2.4 | Golden tests: init on temp repo does not rewrite `.claude/settings.json` when target is grok | M |

**Exit criteria**:
- [x] Temp-repo init --host grok produces .grok/hooks SessionStart (+ UserPromptSubmit if retained) and path-safe MCP registration
- [x] is_path_safe true on all auto-written commands
- [x] Claude Code files unchanged on grok-target init (or only dual-written if explicitly designed and tested)
- [x] O-03 resolved with the measured command string in Outputs Registry

### Phase 3: Doctor, tests, docs truth-up

**Goal**: Doctor branches for `host_target=grok`; wiring-contract tests green; CROSS-HOST/README/site host list honest; CHANGELOG notes.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | `cmd_doctor` grok branch (floor + MCP + optional hooks; no false Claude drift) | M |
| 3.2 | Wiring-contract sweep includes grok where auto-write | S |
| 3.3 | README / clauderizer.com host list + CROSS-HOST §9 net count | S |
| 3.4 | CHANGELOG unreleased notes for the patch train | S |

**Exit criteria**:
- [x] Doctor green on a grok-wired temp repo; no exit-2 false drift for missing .claude/settings.json
- [x] Full unit suite green on the branch
- [x] Docs never claim Grok SessionStart injects the digest
- [x] Website or README host list includes Grok with accurate tier wording

### Phase 4: Live consumption proof + ship patch

**Goal**: Manual Grok cold-session proof (MCP tools, floor, bootstrap note, hooks fire without claiming digest inject); suite green; release train (version from O-04).
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Live Grok session on Clauderizer and/or viderizer: trust, MCP, bootstrap, `/hooks` | M |
| 4.2 | Decide O-04 version; D-011 release ritual (or patch ritual matching 1.5.x field trains) | M |
| 4.3 | Close gameplan; hand focus back (curator loop or as directed) | S |

**Exit criteria**:
- [x] Consumption proof notes in Outputs Registry (what fired, what did not inject)
- [x] Published version on PyPI/uvx verified OR explicit defer of publish with user OK
- [x] O-04 resolved; O-05 left open or filed externally
- [x] Gameplan status Complete; focus handed back
