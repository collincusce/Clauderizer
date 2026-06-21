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

### A-001 — Add battle-hardening series P8-P13; revisit P4 (init never wired to host_target)

- **Date**: 2026-06-21
- **Affected sections in GAMEPLAN.md**: Phase Breakdown; P4 emitters (unreachable via init)
- **Affected phases**: 4,8,9,10,11,12,13
- **Triggered by**: independent red-team/blue-team review, 2026-06-21
- **What changed**: Adds P8 (wire the per-host emitters through init - revisits P4), P9 (real-host + cross-model verification, closes O-06/O-07/engine_stale), P10 (integration-seam sweep codebase-wide), P11 (concurrency/IO/failure sweep), P12 (security/trust hardening), P13 (UX + doc truth-up + release gate + gameplan close-out).
- **Why**: Review found init never references host_target/hosttargets/emit_mcp: the P4 emitters are tested but unreachable through the user-facing command, so a non-Claude host gets the AGENTS.md floor but no MCP registration (the tool is absent) - not functional end-to-end. The user also asked to apply the same red-team/blue-team, gate-verified method across the entire codebase.

### A-002 — Retire Tier-2 (auto-loaded MCP resource) from the injection ladder

- **Date**: 2026-06-21
- **Affected sections in GAMEPLAN.md**: Phase Breakdown (P3 exit criteria); the D-030 injection ladder; docs/CROSS-HOST.md §4
- **Affected phases**: 0,3
- **Triggered by**: Phase 0 primary-source capability audit, 2026-06-21 (C-02)
- **What changed**: Removed Tier 2 (an auto-loaded MCP resource as the portable substitute for hook injection) from the injection-parity ladder. The ladder is now Tier 1 (lifecycle hook) → Tier 3 (MCP prompt slash command) → Tier 4 (AGENTS.md floor). best_tier() never returns 2.
- **Why**: No verified host auto-loads MCP resources into model context — across Cursor, Copilot, Continue, Gemini, Windsurf, Cline, and Zed (no resources at all), resources are model-requested or manual @-mention only. The auto-load assumption had no primary-source basis (MCP resources are user/model-controlled by spec). Designing a delivery tier around an unverified host behavior is L-2. (This amendment was decided in P0 but never formally recorded as an A-NNN due to the O-08 cz_add_amendment arg-name drift; re-recorded in P10.)

### A-003 — Scope the host set from 13 candidates to 11 in-scope

- **Date**: 2026-06-21
- **Affected sections in GAMEPLAN.md**: Open Items O-01; Phase 0 Outputs (in_scope_hosts/dropped_hosts); docs/CROSS-HOST.md §3
- **Affected phases**: 0
- **Triggered by**: Phase 0 per-host capability matrix re-derivation, 2026-06-21
- **What changed**: Reduced the cross-host target set from 13 researched candidates to 11 in-scope: claude-code, kimi, copilot, codex, gemini-cli, windsurf, cline, amp, cursor, continue, zed. Dropped Roo Code (archived 2026-05-15) and deferred Aider (no native MCP client).
- **Why**: Roo Code was archived upstream (dead target); Aider has no native MCP client so it cannot reach even the floor tier via MCP — both fail the "mechanism exists on the target host" bar (L-2). Building the matrix from each host's own primary docs (the canonical modelcontextprotocol.io/clients matrix URL was dead, 308) surfaced both. (Decided in P0, never formally recorded as A-NNN due to the O-08 arg-name drift; re-recorded in P10.)

### A-004 — Promote the server-side session bootstrap to a full phase (P7)

- **Date**: 2026-06-21
- **Affected sections in GAMEPLAN.md**: Phase Breakdown (added Phase 7); the Floor-Release milestone sequencing
- **Affected phases**: 0,7
- **Triggered by**: Phase 0 ladder design review, 2026-06-21
- **What changed**: Promoted the server-side session bootstrap (the MCP server injecting status into the first non-status tool result on a hook-less host, to recover hook-like determinism) from an inline idea to a first-class phase, Phase 7, sequenced as a non-gating fast-follow after the Floor Release (P0-P2/P6).
- **Why**: On hook-less hosts the MCP server is the only automatic delivery path; making the bootstrap explicit gave it its own exit criteria (fires once per session, separate clauderizer_status field so the tool result is never contaminated per D-027, dedup via the P1 in-memory signal per INVARIANT-08, read-only per INVARIANT-06) and a clear non-gating position. (Decided in P0, never formally recorded as A-NNN due to the O-08 arg-name drift; re-recorded in P10.)

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase 0)_ Re-derive a FRESH per-host MCP-primitive matrix (tools/resources/prompts/sampling/roots/elicitation) for all 13 hosts. Deep research found the canonical modelcontextprotocol.io/clients matrix URL dead (308 redirect) and could not verify primitive support for Windsurf, Codex CLI, Gemini CLI, Roo Code, Continue.dev, Zed, Amp — reconstruct from the GitHub clients.mdx plus each host's own docs. _(resolved 2026-06-21: Resolved. Per-host capability matrix built and verified from primary sources for all 13 candidates (docs/CROSS-HOST.md section 3). Net 11 in-scope after dropping Roo Code (archived) and deferring Aider (no MCP).)_

**O-02.** _(phase 0)_ Confirm whether ANY non-Claude host exposes a true lifecycle-hook system (session-start / pre-post-prompt / pre-post-tool-use) that could reach Tier 1. Research established this only for Claude Code (and Clauderizer's kimi wiring); no non-Claude hook system was confirmed. If none exist, deterministic auto-injection is a hard Claude-only capability and the ladder's Tier 1 stays Claude-Code/kimi-only. _(resolved 2026-06-21: Resolved (overturned). Lifecycle hooks are NOT Claude-only: Copilot/VS Code, Codex CLI, Gemini CLI, Windsurf, Cline (POSIX), and Amp expose SessionStart/UserPromptSubmit-class hooks; Cursor has governance hooks (context-injection TBD at emitter time). See C-01. Residual: confirm each host hook context-injection semantics when building its emitter (Phase 4/5).)_

**O-03.** _(phase 0)_ Determine, per host, whether MCP Resources are AUTO-LOADED into model context vs only listed for manual @-mention. This decides whether Tier 2 is actually reachable on each host (the cleanest portable substitute for SessionStart injection). The spec allows Resources but host behavior varies and was not resolved by research. _(resolved 2026-06-21: Resolved (negative). No host auto-loads MCP resources into context; all are model-requested or manual @-mention (Zed has no resources at all). Tier 2 retired. See C-02.)_

**O-04.** _(phase 0)_ Zero-runtime-dep format audit: enumerate every in-scope host's config format (JSON / INI / TOML / YAML / markdown) and flag any that would require a non-stdlib parser to edit comment/key-order-safely (e.g. YAML for Windsurf/Cline/Zed). Each such host is either guide-only or gets a stdlib-only serializer — the stdlib-only invariant must not break. Blocks the floor/bespoke emitter phases. _(resolved 2026-06-21: Resolved. Zero-dep audit (docs/CROSS-HOST.md section 6): JSON hosts auto-write via stdlib json; Continue written as JSON not YAML to avoid PyYAML; TOML hosts (Codex, kimi) stay guide-only/append-only (no stdlib TOML writer). Stdlib-only invariant preserved.)_

**O-05.** _(phase 0)_ Decide the subsystem version-coordination policy across scaffold / mcp-server / rituals as they grow host support: lock versions at release boundaries vs a clauderize doctor coherence check, so a user can never end up with mismatched host capability across subsystems. _(resolved 2026-06-21: Resolved (decided). clauderize doctor gains a subsystem-version-coherence check: installed scaffold/mcp-server versions must declare support for every host_target in config; a mismatch surfaces as advisory drift. Recorded in docs/CROSS-HOST.md section 8.)_

**O-06.** _(phase 4)_ The repo's own committed .mcp.json carries a machine-specific absolute path (/home/ccusce/Clauderizer/.venv/bin/clauderizer-mcp) + the wsl.exe username shim — the exact path-leak P4's emitter refuses (is_path_safe, D-031). Non-portable for anyone cloning. Fix: gitignore the local .mcp.json or switch it to the portable uvx command. Deferred from P4 to avoid breaking the MCP server running this session. _(resolved 2026-06-21: Fixed in P9 commit: .mcp.json AND .claude/settings.json (both carried the machine-specific /home/ccusce/.venv path + wsl.exe shim) are now git rm --cached + gitignored. The dogfood repo keeps them LOCALLY (it must point at its own editable engine build) but never commits them; each clone regenerates via `clauderize init`. path_safety_audit is now gitignore-aware (audits only would-be-committed configs) and is clean on the real repo. Regression test: test_path_safety_audit_skips_gitignored_config.)_

**O-07.** _(phase 6)_ Manual consumption spot-check: install Clauderizer into 2-3 representative real hosts (e.g. Cursor, Copilot/VS Code) and confirm each actually READS the emitted config and the agent loads status. D-032: this consumption proof is irreducibly manual (no real proprietary host runs in CI); the automated gate covers only the wiring contract. Deferred to pre-GA.

**O-08.** _(phase 10)_ Silent contract drift in the cz_* ops surface. cz_add_amendment was called with a wrong arg name (rationale, vs the real triggered_by/what/why) in P0 AND in this amendment's first attempt — so the THREE P0 amendments (retire Tier-2, scope 13->11, promote P7) were never written as A-NNN records (their substance survives only in the P0 phase summary + D-034). cz_add_finding had the same kind of mismatch. For P10: (a) re-record the 3 missing P0 amendments; (b) add a test/guard that every cz_* op's advertised signature matches its implementation and that an ops-batch arg error is surfaced loudly, not swallowed as a single ok:false among successes (a wrong-arg op in a batch should be hard to miss). _(resolved 2026-06-21: Both parts done in P10. (a) The 3 missing P0 amendments are now first-class records: A-002 (retire Tier-2), A-003 (scope 13->11 hosts), A-004 (promote P7 server-side bootstrap). (b) Added tests/test_ops.py::test_no_op_dispatch_signature_drift — a static AST guard that every kwarg each cz_* op passes to an engine fn (mutations/handoff/preflight/cascade/status_bundle/index/query) is a real parameter; this catches the exact cz_add_amendment(`rationale`)/cz_add_finding drift class permanently. Independent review also confirmed all 31 current ops are clean and that batch arg-errors are surfaced loudly (top-level ok:false + exit 1, op names itself) — never swallowed.)_

**O-09.** _(phase 8)_ clauderize doctor (cli.py cmd_doctor) hard-checks the claude-code wiring only (.mcp.json registers clauderizer, SessionStart hook registered, hook wrapper). After `init --host cursor` (or any non-claude host) those files do not exist, so doctor reports false drift (exit 2) for a correctly-wired non-claude repo. P8 wires init but not doctor; making doctor verify the CONFIGURED host_target's wiring is Phase 13's exit criterion ("Doctor verifies the CONFIGURED host's wiring, not just Claude Code"). Branch cmd_doctor on config.host_target there. _(resolved 2026-06-21: Core complaint (doctor false-fails a healthy non-claude repo with exit 2) fixed in P8 review-commit 82328aa: cmd_doctor now branches on config.host_target — non-claude hosts verify their own per-host MCP config + floor instead of the Claude Code files. Remaining depth (full per-host launchability probing, not just presence) is Phase 13's exit criterion "Doctor verifies the CONFIGURED host's wiring, not just Claude Code" — tracked there, not as a duplicate open item.)_

**O-10.** _(phase 9)_ Confirm amp's real on-disk MCP config shape against a live Amp install. HOST_EMITTERS["amp"] uses a FLAT dotted settings.json key "amp.mcpServers" (VS Code-family convention); emit/detect/remove are internally consistent on it (locked by test_amp_emit_remove_roundtrip_is_consistent) and it matches the P4 doc-verified design, but a P8 independent review questioned whether Amp nests as {"amp":{"mcpServers":...}} instead. Unverifiable in CI (no real Amp host) — this is exactly P9's "fold per-host key/path corrections discovered live back into HOST_EMITTERS." If live Amp wants nesting, change servers_key handling (it is currently a flat key everywhere).

**O-11.** _(phase 9)_ MANUAL GATE (irreducibly manual per D-032/O-07 — needs a human at a real machine; cannot run in CI or from this agent session). To finish P9, the user must: (3) install Clauderizer into >=2 real hosts — `clauderize init --host cursor` and one of copilot/continue/zed in a real project — open each host, confirm it loads the emitted MCP config and the agent reaches cz_status; record per-host pass/residue (resolves O-07). (4) Drive the cz_* gameplan protocol end-to-end with >=1 non-Claude model (e.g. a Cursor/Copilot session on GPT/Gemini), note any adherence gaps as findings. (5) Fold any per-host key/path corrections found live back into HOST_EMITTERS (esp. O-10: amp's real settings.json shape). Also: restart this Claude Code session to clear engine_stale (the running MCP server holds pre-edit modules; a restart relaunches it from current source). The AUTOMATABLE parts of P9 are done: O-06 fixed, and the launched server verified to serve P3 prompts + P7 bootstrap + tools against a real stdio MCP client.

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
- [x] cz_status, cz_next_phase_context, cz_preflight and the other read tools proven idempotent and re-entrant by tests, with no hidden dependence on hook-injected context
- [x] Session-scoped, in-memory, read-only 'status-delivered' signal implemented (no config flag; never blocks; never mutates docs)
- [x] Write-first self-correction floor implemented and tested: a write tool with no prior status this session prepends a compact status summary to its result
- [x] Tool descriptions rewritten to work in both native-function-calling and prompt-mode and to survive prompt-format variation
- [x] Static check passes: the shared instruction/tool surface contains no Claude-specific syntax
- [x] Full suite green (baseline 450 tests) plus new tests for the above

### Phase 2: AGENTS.md canonical substrate & Tier-4 floor

**Goal**: Promote AGENTS.md to the canonical bootstrap carrier the whole ecosystem reads; make CLAUDE.md import/symlink it so Claude Code specifics are preserved with zero duplication-drift. Embed the lowest-common-denominator 'call cz_status first' floor instruction (focused and minimal per D-027) that works on any host that reads AGENTS.md and speaks MCP, with zero per-host code. Unlocks the Floor-Release milestone: AGENTS.md+MCP-native hosts become claimable at Tier 4. Hard gate: Claude Code parity unchanged (regression suite green).
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] AGENTS.md is the canonical bootstrap carrier and contains the minimal 'call cz_status first' floor instruction
- [x] The stanza is single-sourced (one template renders CLAUDE.md + AGENTS.md, L-16) so it cannot drift; symlink/@import rejected for the Windows dogfood host + parity (D-035)
- [x] The host-neutral floor instruction is present in the rendered CLAUDE.md + AGENTS.md and guarded by a test (full simulator round-trip deferred to P6)
- [x] Claude Code regression suite green - SessionStart/UserPromptSubmit digest path unchanged (parity invariant)
- [x] Floor-Release milestone documented: which hosts are claimable at Tier 4 and how it was verified

### Phase 3: MCP middle tiers: prompts, auto-load resource & tier routing

**Goal**: Add MCP prompts (/cz-status, /cz-do-phase, ...) — none exist today — for hosts that support prompts, and shape the clauderizer://status resource for auto-load where hosts do that. Implement tier-selection logic (hook -> auto-resource -> prompt -> floor) with: re-probe at session start (not just init) so host upgrades do not leave a stale capability model; downgrade-to-floor safe fallback on any negotiation mismatch; and double-injection dedup via the P1 session signal so every tier checks 'status already delivered?' before emitting.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] MCP prompts (cz-status, cz-next-phase) exposed by the server and listed on a prompt-supporting host (FastMCP list_prompts test)
- [x] Tier-selection implemented (best_tier: hook -> prompt -> floor); Tier-2 auto-resource retired per D-034 (no host supports it)
- [x] Capability is read fresh per call (stateless server = no stale cache) with safe downgrade-to-floor for unknown hosts (best_tier -> 4)
- [x] Tier-routing unit tests: correct tier per host profile; double-injection prevented via the P1 session signal

### Phase 4: Floor-host wiring emitters (AGENTS.md+MCP hosts) + uninstall & coexistence

**Goal**: Generalize init/wiring (src/clauderizer/scaffold/init.py) into additive per-host emitters for the cheap tier — the AGENTS.md+MCP-native hosts needing no bespoke rule-format work. Each emitter writes well-formed, NON-DESTRUCTIVE, path-safe wiring; has a committed golden/snapshot test (emit to temp dir, diff fixture) so host-format drift becomes an explicit fixture-update PR; preserves co-resident hosts' keys (re-running init for a 2nd host must NOT clobber the 1st's MCP registration — the top config-safety risk); routes global-level config to guide-only (never auto-edit ~/.config/...); and refuses to bake absolute user/venv/wsl.exe paths into committed files. Ship `clauderize uninstall [--host <name>]` (removes only marker blocks + the clauderizer MCP key) before any host ships.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Per-host emitters write well-formed, path-safe, non-destructive MCP wiring with the portable uvx command; each host's key/path is locked by a test
- [x] Re-running for a second co-resident host preserves the first host's registration; a user's other servers in a shared file survive (non-destructive, tested)
- [x] Global/user-level and TOML configs are guide-only; the emitter REFUSES an absolute/venv/wsl.exe command (path-safety test)
- [x] clauderize uninstall [--host] removes only the clauderizer MCP key, leaving every other server intact (CLI test); marker-block stripping reuses writer.upsert_marker_block (noted extension)

### Phase 5: Bespoke-host wiring emitters (native rule formats & deeper integration)

**Goal**: Build emitters for hosts that need more than AGENTS.md+MCP — host-native rule formats and any hook-like systems that can reach Tier 1/2 (e.g. GitHub Copilot/VS Code's own instructions file + global MCP settings; Windsurf specifics; Cline rule-toggles and slash-commands). Apply the same safety bars as the floor emitters: golden tests, uninstall support, co-resident coexistence, path-safety, global->guide-only. Each bespoke host reaches its best achievable injection tier.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Bespoke emitters: native-instructions floor auto-written for non-AGENTS.md hosts (Continue .continue/rules, Gemini GEMINI.md; marker-block, idempotent); hook setup guides for hook-capable hosts (Copilot/Codex/Windsurf/Cline/Amp) reaching Tier 1 via guided wiring (schemas unverified -> guide not auto-write, O-02)
- [x] Safety bars met: marker-block preserves user content (idempotent test), guides are non-destructive, path-safety + guide-only inherited from P4

### Phase 6: Cross-host verification execution & release gate

**Goal**: Stand up the verification the release depends on. Build an in-process host-simulator harness (a minimal MCP client stub that reads each emitted config, launches the server, and round-trips cz_status) to close the consumption loop for MCP-standard hosts in CI. Run `clauderize doctor --format json` as a green-gated CI job (native self-probe). Generalize doctor's identity/digest probes per host and add a gitignore/path-safety audit. Enforce the release gate as the WIRING CONTRACT (emitted config well-formed + server launches + simulator round-trips) — NOT 'tested on 13 live hosts' (11 are proprietary and unrunnable in CI); consumption proof is a manual spot-check on 2-3 representative real hosts. Produce the updated release checklist (four-registry sweep + every CI host leg, L-20) and the CHANGELOG entry. Claude Code regression suite green.
**Depends on**: 3, 4, 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Wiring-contract sweep (wiring_contract_sweep) verifies every auto-write host's emitted config is well-formed, path-safe, and launches clauderizer-mcp; runs in CI via the test suite. Literal cz_status round-trip via a launched server deferred (D-032 scopes the gate to the wiring contract)
- [x] path_safety_audit() scans committed configs for machine-specific paths (catches O-06); tested. Per-host doctor identity/digest generalization is a noted extension (existing doctor covers the Claude Code leg)
- [x] Wiring-contract gate enforced for every auto-write host (sweep test). Manual consumption spot-check on real hosts deferred to pre-GA (O-07; D-032 irreducibly manual)
- [x] CHANGELOG Unreleased section written with the cross-host deliverables; full suite green via cz_preflight. Four-registry release sweep is a release-time step (L-20), not a branch deliverable

### Phase 7: Server-side session bootstrap (fast-follow; non-gating)

**Goal**: Make the MCP server inject status into the FIRST read-like tool result of a session to recover hook-like determinism on hook-less hosts. Strict policy (recorded in P0): inject only into a read-like call (cz_status/cz_next_phase_context/cz_preflight); if a write comes first, do NOT contaminate it (D-027) — fall back to Tier 3/4. Dedup via the P1 session signal so it never double-injects alongside a hook or auto-resource. Honor INVARIANT-06 (read-only, never block) even though it holds per-connection in-memory session state. Explicitly a FAST-FOLLOW: it does not gate the floor release.
**Depends on**: 1, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Server-side bootstrap fires on the FIRST non-status tool call of a session (read OR write) on a hook-less host, attaching status as a SEPARATE clauderizer_status field - the tool's own result is never corrupted (D-027, 'not contaminated'). After the first call the signal stands down
- [x] Dedup via the P1 session signal: bootstrap never double-injects alongside a hook (hook hosts mark-and-stand-down on the first call); at most once per session (INVARIANT-08)
- [x] INVARIANT-06 honored: the signal is in-memory/read-only, the note never blocks the session, and stays minimal (D-027)
- [x] Confirmed non-gating: the Floor Release (P0-P2) shipped/committed before this phase

### Phase 8: Wire host_target end-to-end (make cross-host functional via init)

**Goal**: Revisit P4: the emitters are unreachable through init. Add `clauderize init --host <name>` that sets host_target, with cheap auto-detection when omitted and a friendly error listing valid hosts on an unknown name (no KeyError). Branch init's MCP/instructions step on host_target: claude-code keeps byte-identical current behavior (INVARIANT-07); an auto-write host calls hosttargets.emit_mcp + emit_instructions (where the host does not read AGENTS.md) and writes/prints the per-host hook setup guide; a guide-only host writes its setup guide. Make `clauderize uninstall` complete - MCP config + hooks + marker stanzas + .clauderizer - to match its name, preserving docs/ and unrelated entries. Prove it end-to-end with an integration test.
**Depends on**: 7.

| Task | Description | Effort |
|------|-------------|--------|
| 8.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderize init --host <name> sets host_target and emits that host's wiring (MCP config + native floor where the host does not read AGENTS.md + hook setup guide); omitting --host auto-detects, defaulting to claude-code with a nudge
- [x] Unknown host -> a friendly error listing valid hosts (no KeyError); guarded by a test
- [x] init on a Claude Code repo is byte-identical to pre-P8 output (parity regression test, INVARIANT-07)
- [x] Integration test: init --host cursor produces a .cursor/mcp.json that passes wiring_contract_sweep, and the host gets BOTH the floor and the MCP tools (no floor-but-no-tools)
- [x] clauderize uninstall [--host] removes the full footprint (MCP config + hooks + marker stanzas + .clauderizer), preserving docs/ and unrelated entries; tested

### Phase 9: Real-host & cross-model verification (close O-06, O-07; kill engine_stale)

**Goal**: Move from paper-verified to product-verified. Fix O-06 (the repo's own committed .mcp.json carries a machine-specific path). Restart/validate the live MCP server so the new prompts and the server-side bootstrap are exercised against a real MCP client, not just unit tests. Install into at least two real hosts (Cursor plus one of Copilot/Continue/Zed) and confirm each loads the emitted config and the agent reaches cz_status (closes O-07, the consumption proof). Drive the cz_* gameplan protocol with at least one non-Claude model to sanity-check the cross-model claim. Fold any per-host key/path corrections discovered live back into HOST_EMITTERS with a note.
**Depends on**: 8.

| Task | Description | Effort |
|------|-------------|--------|
| 9.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] O-06 resolved: no machine-specific path in any committed config (the dogfood .mcp.json is gitignored or portable)
- [ ] The live MCP server serves the new prompts and the server-side bootstrap, verified against a real MCP client (engine_stale cleared)
- [ ] At least 2 real hosts confirmed to load the emitted config and reach cz_status; per-host results recorded (O-07 resolved or residue tracked per host)
- [ ] At least 1 non-Claude model drives the gameplan protocol end-to-end; adherence gaps recorded as findings
- [ ] Any per-host key/path corrections from live testing folded back into HOST_EMITTERS with a note

### Phase 10: Adversarial sweep: integration seams & state (codebase-wide)

**Goal**: Generalize the merge_missing lesson across the whole engine. For every shared function many call sites depend on - config merge/load/save, the markdown writer, the graph index/rebuild, status_bundle, the ops registry, the hook dispatcher - run independent reviewers to hunt the places a newer field/branch/host/event must thread through but does not. Adversarially verify each finding (2 of 3 to confirm) and fix each confirmed seam with a regression test at the seam. Loop until a review round comes back dry.
**Depends on**: 8.

| Task | Description | Effort |
|------|-------------|--------|
| 10.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Documented seam audit across config merge/load/save, the markdown writer, graph index/rebuild, status_bundle, the ops registry, and the hook dispatcher
- [x] Each confirmed (2/3 adversarial) seam bug fixed with a regression test AT the seam
- [x] A final independent review round returns dry (no new confirmed seams)
- [x] Full suite green via cz_preflight

### Phase 11: Adversarial sweep: concurrency, I/O robustness & failure modes

**Goal**: Harden the engine against concurrent agents and hostile inputs codebase-wide. Stress the write lock (locking.py, H-05/H-10) under concurrent cz_* writes; verify partial-write/crash recovery and append-only integrity under interleaving; prove the hook handlers stay read-only and always exit 0 under every failure (INVARIANT-04/06); run the adversarial-input battery (L-24: non-UTF-8, BOM/CRLF, unhashable keys, empty, malformed frontmatter) across every file the engine parses; exercise the MCP wrapper under tool errors (generalize the pre-mark fix). Adversarially verify and fix confirmed failures.
**Depends on**: 8.

| Task | Description | Effort |
|------|-------------|--------|
| 11.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A concurrency stress test exercises the write lock under interleaved cz_* writes (H-05/H-10) without corruption or lost writes
- [x] An adversarial-input battery (non-UTF-8, BOM/CRLF, unhashable, empty, malformed frontmatter) covers every file the engine parses; each degrades gracefully
- [x] Every hook event handler proven read-only and exit-0 under induced failure (INVARIANT-04/06)
- [x] Confirmed failures fixed; full suite green

### Phase 12: Security & trust hardening

**Goal**: Enforce path-safety and non-destructiveness on ALL config emitters - including init's original .mcp.json/.claude writers, which today carry the O-06 machine-path leak - not just the new cross-host ones. Guarantee no machine-specific path or secret ever lands in a committable file; that uninstall fully reverses the footprint; and that the agent surface cannot be coerced into writing outside the repo or running arbitrary commands via config. Verify SECURITY.md and TRUST.md line-by-line against the code. Run an independent security-review pass and fix its findings.
**Depends on**: 8.

| Task | Description | Effort |
|------|-------------|--------|
| 12.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Path-safety enforced on ALL config emitters, including init's original .mcp.json/.claude writers (the O-06 class) - tested
- [x] No machine path or secret can land in a committable file; uninstall fully reverses the footprint (tested)
- [x] An independent security-review pass completed; its confirmed findings fixed
- [x] SECURITY.md and TRUST.md verified line-by-line against the code; full suite green

### Phase 13: UX completeness, doc truth-up & release gate; close the gameplan

**Goal**: Make the end user totally accounted for and the docs true. Walk every user scenario - new project, existing project, switch tools, dual-tool on one repo, clone, uninstall, broken-wiring recovery - and make each clean, discoverable (a --list-hosts; a doctor that verifies the CONFIGURED host, not just Claude Code), and documented. Truth-up every doc against the NOW-VERIFIED reality (no '11 hosts' claim beyond what P9 actually proved; redo the L-21 sweep). Assemble the release gate: the four version registries (L-08), every CI host leg (L-20), the CHANGELOG, and the wiring-contract + real-host evidence. Then close out the gameplan (post-mortem + promote enduring lessons to docs/LESSONS.md).
**Depends on**: 9, 11, 12.

| Task | Description | Effort |
|------|-------------|--------|
| 13.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Every user scenario (new/existing/switch/dual/clone/uninstall/recovery) walked, made clean + discoverable (--list-hosts, doctor per configured host), and documented
- [x] Doctor verifies the CONFIGURED host's wiring, not just Claude Code
- [x] Every doc claim matches verified reality (no '11 hosts' beyond what P9 proved); the L-21 sweep redone
- [ ] Release checklist complete: four version registries (L-08), every CI host leg (L-20), CHANGELOG, wiring-contract + real-host evidence
- [ ] Gameplan closed out: post-mortem written, enduring lessons promoted to docs/LESSONS.md
