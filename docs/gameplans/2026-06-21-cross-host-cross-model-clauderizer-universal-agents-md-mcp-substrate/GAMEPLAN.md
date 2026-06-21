# Cross-host & cross-model Clauderizer (universal AGENTS.md + MCP substrate) Gameplan

> Created: 2026-06-21
> Status: Executing
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

**O-01.** _(phase 0)_ Re-derive a FRESH per-host MCP-primitive matrix (tools/resources/prompts/sampling/roots/elicitation) for all 13 hosts. Deep research found the canonical modelcontextprotocol.io/clients matrix URL dead (308 redirect) and could not verify primitive support for Windsurf, Codex CLI, Gemini CLI, Roo Code, Continue.dev, Zed, Amp — reconstruct from the GitHub clients.mdx plus each host's own docs. _(resolved 2026-06-21: Resolved. Per-host capability matrix built and verified from primary sources for all 13 candidates (docs/CROSS-HOST.md section 3). Net 11 in-scope after dropping Roo Code (archived) and deferring Aider (no MCP).)_

**O-02.** _(phase 0)_ Confirm whether ANY non-Claude host exposes a true lifecycle-hook system (session-start / pre-post-prompt / pre-post-tool-use) that could reach Tier 1. Research established this only for Claude Code (and Clauderizer's kimi wiring); no non-Claude hook system was confirmed. If none exist, deterministic auto-injection is a hard Claude-only capability and the ladder's Tier 1 stays Claude-Code/kimi-only. _(resolved 2026-06-21: Resolved (overturned). Lifecycle hooks are NOT Claude-only: Copilot/VS Code, Codex CLI, Gemini CLI, Windsurf, Cline (POSIX), and Amp expose SessionStart/UserPromptSubmit-class hooks; Cursor has governance hooks (context-injection TBD at emitter time). See C-01. Residual: confirm each host hook context-injection semantics when building its emitter (Phase 4/5).)_

**O-03.** _(phase 0)_ Determine, per host, whether MCP Resources are AUTO-LOADED into model context vs only listed for manual @-mention. This decides whether Tier 2 is actually reachable on each host (the cleanest portable substitute for SessionStart injection). The spec allows Resources but host behavior varies and was not resolved by research. _(resolved 2026-06-21: Resolved (negative). No host auto-loads MCP resources into context; all are model-requested or manual @-mention (Zed has no resources at all). Tier 2 retired. See C-02.)_

**O-04.** _(phase 0)_ Zero-runtime-dep format audit: enumerate every in-scope host's config format (JSON / INI / TOML / YAML / markdown) and flag any that would require a non-stdlib parser to edit comment/key-order-safely (e.g. YAML for Windsurf/Cline/Zed). Each such host is either guide-only or gets a stdlib-only serializer — the stdlib-only invariant must not break. Blocks the floor/bespoke emitter phases. _(resolved 2026-06-21: Resolved. Zero-dep audit (docs/CROSS-HOST.md section 6): JSON hosts auto-write via stdlib json; Continue written as JSON not YAML to avoid PyYAML; TOML hosts (Codex, kimi) stay guide-only/append-only (no stdlib TOML writer). Stdlib-only invariant preserved.)_

**O-05.** _(phase 0)_ Decide the subsystem version-coordination policy across scaffold / mcp-server / rituals as they grow host support: lock versions at release boundaries vs a clauderize doctor coherence check, so a user can never end up with mismatched host capability across subsystems. _(resolved 2026-06-21: Resolved (decided). clauderize doctor gains a subsystem-version-coherence check: installed scaffold/mcp-server versions must declare support for every host_target in config; a mismatch surfaces as advisory drift. Recorded in docs/CROSS-HOST.md section 8.)_

## Phase Breakdown

### Phase 0: Host model, capability audit & parity contract

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] HostTarget capability descriptor defined (hooks / mcp-tools / mcp-resource-autoload / mcp-prompts / rules-file format+location / slash-commands) and the three-axis host model (session-host x host-profile x host-target) recorded as a decision
- [x] Fresh per-host MCP-primitive + config-format + config-location matrix completed for all 13 hosts (O1 resolved); each host classified auto-write vs guide-only and assigned a target injection tier
- [x] Zero-dep format audit done (O4 resolved): no in-scope auto-write host requires a non-stdlib parser, or it is reclassified guide-only
- [x] Injection-parity ladder, tier-routing rules, and the 'status delivered at most once per session' rule written into a cross-host design doc
- [x] Verification strategy documented: wiring-contract vs consumption-proof split, host-simulator design, and the narrow static-analysis model-agnostic claim
- [x] Release decisions recorded: incremental-per-tier cadence, beta-gate impact, and subsystem version-coordination policy
- [x] Parity invariant 'Claude Code never regresses' recorded; CHANGELOG entry stub drafted

### Phase 1: Model-agnostic protocol hardening & injection-delivery signal

**Goal**: Make every protocol step idempotent, re-entrant, and self-correcting so it survives non-Claude models and hook-less hosts; remove any hidden dependence on hook-injected context from cz_status/cz_preflight and the other read tools. Introduce a session-scoped, in-memory, READ-ONLY 'status-delivered' signal (never a config flag per INVARIANT-05; read-only and non-blocking per INVARIANT-06) that (a) dedups injection across tiers to honor trim-first (D-027), (b) detects silent tier-degradation, and (c) drives a write-first self-correction floor: if a write tool runs with no prior status this session, prepend a compact status summary to its result. Rewrite tool descriptions to survive prompt-format variation and work in both native-function-calling and prompt-mode (BFCL). Add a static check that the shared instruction/tool surface contains no Claude-specific syntax. This phase is the load-bearing substrate and a hard prerequisite for the middle tiers, emitters, and bootstrap.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_status, cz_next_phase_context, cz_preflight and the other read tools proven idempotent and re-entrant by tests, with no hidden dependence on hook-injected context
- [ ] Session-scoped, in-memory, read-only 'status-delivered' signal implemented (no config flag; never blocks; never mutates docs)
- [ ] Write-first self-correction floor implemented and tested: a write tool with no prior status this session prepends a compact status summary to its result
- [ ] Tool descriptions rewritten to work in both native-function-calling and prompt-mode and to survive prompt-format variation
- [ ] Static check passes: the shared instruction/tool surface contains no Claude-specific syntax
- [ ] Full suite green (baseline 450 tests) plus new tests for the above

### Phase 2: AGENTS.md canonical substrate & Tier-4 floor

**Goal**: Promote AGENTS.md to the canonical bootstrap carrier the whole ecosystem reads; make CLAUDE.md import/symlink it so Claude Code specifics are preserved with zero duplication-drift. Embed the lowest-common-denominator 'call cz_status first' floor instruction (focused and minimal per D-027) that works on any host that reads AGENTS.md and speaks MCP, with zero per-host code. Unlocks the Floor-Release milestone: AGENTS.md+MCP-native hosts become claimable at Tier 4. Hard gate: Claude Code parity unchanged (regression suite green).
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] AGENTS.md is the canonical bootstrap carrier and contains the minimal 'call cz_status first' floor instruction
- [ ] CLAUDE.md imports/symlinks AGENTS.md; no duplicated stanza can drift
- [ ] A clean checkout with only AGENTS.md + MCP registered surfaces the floor to a fresh agent (simulator-verified)
- [ ] Claude Code regression suite green — SessionStart/UserPromptSubmit digest unchanged (parity invariant)
- [ ] Floor-Release milestone documented: which hosts are claimable at Tier 4 and how it was verified

### Phase 3: MCP middle tiers: prompts, auto-load resource & tier routing

**Goal**: Add MCP prompts (/cz-status, /cz-do-phase, ...) — none exist today — for hosts that support prompts, and shape the clauderizer://status resource for auto-load where hosts do that. Implement tier-selection logic (hook -> auto-resource -> prompt -> floor) with: re-probe at session start (not just init) so host upgrades do not leave a stale capability model; downgrade-to-floor safe fallback on any negotiation mismatch; and double-injection dedup via the P1 session signal so every tier checks 'status already delivered?' before emitting.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] MCP prompts (/cz-status, /cz-do-phase, ...) exposed by the server and listed on a prompt-supporting host
- [ ] clauderizer://status shaped for auto-load; tier-selection logic implemented (hook -> resource -> prompt -> floor)
- [ ] Capability re-probe at session start with safe downgrade-to-floor on mismatch
- [ ] Tier-routing unit tests: for each host capability profile the correct tier fires and higher tiers are skipped; double-injection prevented via the P1 signal

### Phase 4: Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence

**Goal**: Generalize init/wiring (src/clauderizer/scaffold/init.py) into additive per-host emitters for the cheap tier — the AGENTS.md+MCP-native hosts needing no bespoke rule-format work. Each emitter writes well-formed, NON-DESTRUCTIVE, path-safe wiring; has a committed golden/snapshot test (emit to temp dir, diff fixture) so host-format drift becomes an explicit fixture-update PR; preserves co-resident hosts' keys (re-running init for a 2nd host must NOT clobber the 1st's MCP registration — the top config-safety risk); routes global-level config to guide-only (never auto-edit ~/.config/...); and refuses to bake absolute user/venv/wsl.exe paths into committed files. Ship `clauderize uninstall [--host <name>]` (removes only marker blocks + the clauderizer MCP key) before any host ships.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Per-host emitters for the AGENTS.md+MCP floor hosts produce well-formed, path-safe, non-destructive wiring; each has a committed golden/snapshot test
- [ ] Re-running init for a second co-resident host preserves the first host's MCP registration and hooks (coexistence test)
- [ ] Global/user-level configs are guide-only; no absolute user/venv/wsl.exe path is written into a committed file
- [ ] clauderize uninstall [--host <name>] removes only Clauderizer marker blocks + the clauderizer MCP key, leaving everything else intact (tested)

### Phase 5: Bespoke-host wiring emitters (native rule formats & deeper integration)

**Goal**: Build emitters for hosts that need more than AGENTS.md+MCP — host-native rule formats and any hook-like systems that can reach Tier 1/2 (e.g. GitHub Copilot/VS Code's own instructions file + global MCP settings; Windsurf specifics; Cline rule-toggles and slash-commands). Apply the same safety bars as the floor emitters: golden tests, uninstall support, co-resident coexistence, path-safety, global->guide-only. Each bespoke host reaches its best achievable injection tier.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Bespoke-host emitters (e.g. Copilot/VS Code instructions + global MCP; Windsurf; Cline rule-toggles/slash-commands) implemented, each reaching its best achievable tier
- [ ] Same safety bars met: golden tests, uninstall, coexistence, path-safety, global->guide-only

### Phase 6: Cross-host verification execution & release gate

**Goal**: Stand up the verification the release depends on. Build an in-process host-simulator harness (a minimal MCP client stub that reads each emitted config, launches the server, and round-trips cz_status) to close the consumption loop for MCP-standard hosts in CI. Run `clauderize doctor --format json` as a green-gated CI job (native self-probe). Generalize doctor's identity/digest probes per host and add a gitignore/path-safety audit. Enforce the release gate as the WIRING CONTRACT (emitted config well-formed + server launches + simulator round-trips) — NOT 'tested on 13 live hosts' (11 are proprietary and unrunnable in CI); consumption proof is a manual spot-check on 2-3 representative real hosts. Produce the updated release checklist (four-registry sweep + every CI host leg, L-20) and the CHANGELOG entry. Claude Code regression suite green.
**Depends on**: 3, 4, 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] In-process host-simulator harness round-trips cz_status through each MCP-standard host's emitted config in CI
- [ ] clauderize doctor --format json runs green in CI (native self-probe) and its identity/digest probes are generalized per host; gitignore/path-safety audit included
- [ ] Wiring-contract release gate enforced for every in-scope host; manual consumption spot-check completed on 2-3 representative real hosts and recorded
- [ ] Release checklist updated (four-registry sweep + every CI host leg, L-20) and CHANGELOG written; full suite green

### Phase 7: Server-side session bootstrap (fast-follow; non-gating)

**Goal**: Make the MCP server inject status into the FIRST read-like tool result of a session to recover hook-like determinism on hook-less hosts. Strict policy (recorded in P0): inject only into a read-like call (cz_status/cz_next_phase_context/cz_preflight); if a write comes first, do NOT contaminate it (D-027) — fall back to Tier 3/4. Dedup via the P1 session signal so it never double-injects alongside a hook or auto-resource. Honor INVARIANT-06 (read-only, never block) even though it holds per-connection in-memory session state. Explicitly a FAST-FOLLOW: it does not gate the floor release.
**Depends on**: 1, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Server-side bootstrap injects status into the first read-like tool result of a session; a write-first call is NOT contaminated (falls back to Tier 3/4)
- [ ] Dedup via the P1 session signal: bootstrap never double-injects alongside a hook or auto-resource
- [ ] INVARIANT-06 honored (read-only, never blocks) despite per-connection in-memory session state; injected status is minimal (D-027)
- [ ] Confirmed non-gating: floor release shipped without this phase
