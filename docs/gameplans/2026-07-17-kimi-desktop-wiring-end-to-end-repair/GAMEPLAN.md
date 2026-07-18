# kimi-desktop-wiring-end-to-end-repair Gameplan

> Created: 2026-07-17
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

**O-01.** _(phase 2)_ Unknown: does kimi-desktop merge its runtime mcp.json from any persistent user-level source (not config.toml / daimon/config.json, which were checked and have no MCP keys)? If such a source exists, register there instead of self-healing on every entry point. Investigate at the start of Phase 2; if none, self-heal is the fix.

**O-02.** _(phase 3)_ Unknown: from a WSL-side doctor, can the composed Windows clauderizer-mcp.exe entry actually be spawned+handshaked via binfmt/interop, or must that verdict be 'unverifiable' (verify from the Windows session host)? Decide the verdict policy in Phase 3, mirroring hosts.verify_wiring's wsl.exe/interop handling — never a false green.

## Phase Breakdown

### Phase 0: --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderizer-mcp accepts `--repo <path>` and honors `CLAUDERIZER_REPO`; repo_ctx resolves that path instead of Path.cwd() when set
- [x] Precedence is explicit and tested: --repo > CLAUDERIZER_REPO > cwd discovery; an invalid/non-clauderized --repo fails with a clear message
- [x] --version/--help fast-path still exits 0 without touching the SDK or stdin
- [x] New tests cover --repo, CLAUDERIZER_REPO, and precedence; full suite green (>= 840 passed)

### Phase 1: Windows-native command composition (clauderizer-mcp.exe)

**Goal**: Replace the bare-uvx Windows entry: server_entry probes for a Windows-native clauderizer-mcp.exe (pipx venv Scripts, ~/.local/bin, uv tool dir) and registers its absolute path with args:[]. From WSL, probe the /mnt/c mirror and translate to the C:\ spelling, deriving the user from the config path. Never bare uvx for Windows; never the wsl.exe form for the repo-agnostic entry. Fall back to a loud warning + guide when no .exe is found.
**Depends on**: --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] server_entry probes for clauderizer-mcp.exe in %USERPROFILE%\pipx\venvs\clauderizer\Scripts, %USERPROFILE%\.local\bin, and the uv tool dir; registers the absolute path with args:[]
- [x] From WSL detecting a /mnt/c Windows-side config, probes the /mnt/c mirror and registers the translated C:\ path (user derived from the config path)
- [x] No Windows topology composes a bare `uvx` or a wsl.exe-through-WSL command for the repo-agnostic entry
- [x] When no .exe is found, writes a loud warning + guide (never a silent broken entry); native macOS/Linux path is unchanged
- [x] New/updated tests assert the composed entry per topology (win32-native, WSL->Windows, no-exe fallback, native); full suite green

### Phase 2: Self-healing registration on every entry point

**Goal**: Make the daimon registration durable against the app regenerating its mcp.json on project switch: re-apply/repair the clauderizer entry whenever any entry point runs (init already; add doctor, status, and the SessionStart hook), gated by CLAUDERIZER_NO_KIMI_DESKTOP=1. Investigate first whether a persistent user-level source the app merges from exists; if not, self-heal via the idempotent+atomic merge (no-op when already current). Document the finding.
**Depends on**: Windows-native command composition (clauderizer-mcp.exe).

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Finding recorded: whether a persistent user-level source the app merges from exists (and if so, we register there)
- [ ] doctor, status, and the SessionStart hook each re-apply/repair the daimon entry (self-heal), in addition to init
- [ ] Re-wiring is idempotent+atomic: a no-op write when the entry is already current (verified by test)
- [ ] CLAUDERIZER_NO_KIMI_DESKTOP=1 still fully skips detection/auto-write on every entry point
- [ ] Tests cover self-heal firing from a non-init entry point and the opt-out; full suite green

### Phase 3: Doctor MCP initialize-handshake smoke-test

**Goal**: Doctor spawns the composed kimi-desktop command from a non-repo cwd the way the app would, sends an MCP initialize JSON-RPC over stdio, and asserts serverInfo.name=="clauderizer" (and version parity, mirroring verify_wiring). Fail loudly on MSYS-mangled args, UNC-cwd compositions, and registrations that vanished since last run; report unverifiable (not fail) when the command targets a host this doctor can't reach (e.g. wsl.exe with no interop). Pure, injectable handshake helper + doctor integration.
**Depends on**: Windows-native command composition (clauderizer-mcp.exe), --repo / CLAUDERIZER_REPO repo decoupling in clauderizer-mcp.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] A pure, injectable handshake helper spawns the composed command from a non-repo cwd, sends MCP initialize over stdio, and parses serverInfo
- [ ] doctor fails the kimi-desktop check when the handshake does not return serverInfo.name=="clauderizer" (and flags version mismatch, mirroring verify_wiring)
- [ ] MSYS-mangled args, UNC-cwd compositions, and vanished registrations fail loudly with actionable detail
- [ ] Unreachable-host commands (e.g. wsl.exe with no interop) report unverifiable, not a false pass or false fail
- [ ] Tests cover pass, name-mismatch, spawn-fail, and unverifiable paths; full suite green

### Phase 4: WSL-hosted-repo UNC guidance instead of dead registration

**Goal**: When the current repo is WSL-hosted but the daimon host is Windows (UNC-cwd spawn limit, D-054), init/doctor emit the targeted UNC guidance (Windows-hosted clone, or Kimi Code CLI in WSL) rather than a command that cannot spawn — while the repo-agnostic Windows .exe entry still stands for Windows-hosted repos. Wire the --repo primitive into the guidance story (how a Windows-safe-cwd server could serve a UNC repo once that lands).
**Depends on**: Windows-native command composition (clauderizer-mcp.exe).

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] When the current repo is WSL-hosted and the daimon host is Windows, init/doctor emit the D-054 UNC guidance (Windows-hosted clone or Kimi Code CLI in WSL) instead of a dead command
- [ ] The repo-agnostic Windows .exe entry still stands so Windows-hosted repos the app opens keep the cz_* tools
- [ ] Guidance references the --repo primitive as the forward path to serving a UNC repo from a Windows-safe cwd
- [ ] Tests assert guidance-not-dead-registration for the WSL-repo+Windows-host combo; full suite green

### Phase 5: Docs + release close-out

**Goal**: Update .clauderizer/kimi-desktop-mcp-setup.md (and setup_guide()) with the persistence finding (app regenerates the runtime mcp.json; hand-edits are temporary; clauderizer self-heals on every entry point) and the verified-working compositions per host topology (Windows-hosted repo → clauderizer-mcp.exe absolute path; WSL-hosted repo → UNC guidance; macOS/Linux → native). Version bump (minor), CHANGELOG, full test run, and release close-out.
**Depends on**: Self-healing registration on every entry point, Doctor MCP initialize-handshake smoke-test, WSL-hosted-repo UNC guidance instead of dead registration.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] .clauderizer/kimi-desktop-mcp-setup.md and setup_guide() carry the persistence finding and the verified compositions per host topology
- [ ] All four acceptance criteria from the request demonstrably hold (durable Windows-repo tools, doctor fails on broken handshake, WSL-repo guidance, Claude Code wiring unchanged/green)
- [ ] Version bumped (minor), CHANGELOG updated, full test suite green
- [ ] cascade run over D-055 / subsys.scaffold / subsys.mcp-server resolved; gameplan closed with a post-mortem
