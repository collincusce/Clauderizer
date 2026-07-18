# bespoke-auto-write-host-framework Gameplan

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

**O-01.** _(phase 2)_ Decide the default policy for applying the extracted MCP handshake to the 8 HOST_EMITTERS auto-write hosts in doctor: full handshake for all enabled hosts adds latency (each spawn up to the timeout; portable-uvx entries do a real resolve) and could add 'unverifiable' noise. Options: (a) keep presence-check default + handshake opt-in (e.g. `doctor --deep`); (b) handshake only machine-specific/local-path commands, presence for portable uvx; (c) handshake all with a short timeout. Pick in Phase 2 to avoid regressing doctor UX (L-07: don't add noise to healthy sessions). _(resolved 2026-07-17: Decided: doctor keeps PRESENCE-check by default for the HOST_EMITTERS auto-write hosts (verify_wiring already launch-probes the session host's wiring; a full handshake per enabled host adds latency for little gain — L-07). The shared mcp_probe handshake is wired into that path as an opt-in `clauderize doctor --deep`, which spawns each registered emitter host's command and completes an initialize handshake (capability, not presence). Bespoke hosts (kimi-desktop) always get the handshake since their command is machine-specific with no other launchability check. Tested: test_doctor_deep_handshakes_auto_write_host (default presence-only, --deep adds the handshake verdict).)_

## Phase Breakdown

### Phase 0: Extract host-agnostic MCP-verification + command-composition primitives

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] The MCP initialize-handshake verifier (handshake_probe + _spawn_target + _server_info + _default_run) lives in a host-agnostic home and operates on a generic {command,args} entry
- [x] Windows/WSL command composition (native-exe probing + C:\↔/mnt translation) is a shared helper usable by any host, not kimidesktop-private
- [x] kimidesktop consumes the extracted primitives; composition against the live env is byte-identical to before (verified), and the D-055 kimi-desktop tests stay green
- [x] No behavior change: full suite green (>= 873 passed), Claude Code wiring untouched

### Phase 1: BespokeHost protocol + registry; port kimi-desktop as first implementation

**Goal**: Define a minimal BespokeHost protocol/base capturing the variable parts (id, opt_out_env, servers_key, config discovery, topology-aware compose_entry, setup_guide, optional unservable-guidance hook) over shared machinery (detected-only, non-destructive atomic idempotent merge, self_heal wrapper, handshake verification, wire() status contract) + a BESPOKE_HOSTS registry. Port kimi-desktop to be the first BespokeHost implementation. Behavior-preserving.
**Depends on**: Extract host-agnostic MCP-verification + command-composition primitives.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A BespokeHost protocol/base defines the variable members (id, opt_out_env, servers_key, config discovery, compose_entry, setup_guide, optional unservable-guidance hook)
- [x] Shared machinery (detect / non-destructive atomic idempotent merge / self_heal / handshake verify / wire status contract) operates on any BespokeHost, not kimidesktop-specific
- [x] kimi-desktop is expressed as the first BespokeHost implementation and registered in BESPOKE_HOSTS
- [x] Behavior-preserving: the D-055 acceptance criteria (byte-identical composition, self-heal, handshake, UNC guidance) still hold; full suite green
- [x] The protocol is minimal (only what kimi-desktop actually varies) and the registry is a plain dict — no plugin/entry-point system

### Phase 2: Rewire entry points to the registry; offer the handshake to the generic host path

**Goal**: init/doctor/status/uninstall iterate BESPOKE_HOSTS instead of hardcoding kimidesktop (behavior identical for the single registered host). Make the extracted MCP-handshake primitive available to the existing HOST_EMITTERS per-host doctor verification (verify_emitted_wiring / the doctor per-host loop) — decide the default policy in-phase to avoid doctor latency (e.g. capability-check available/opt-in, honest unverifiable for unreachable hosts), never regressing existing behavior.
**Depends on**: BespokeHost protocol + registry; port kimi-desktop as first implementation.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] init, doctor, status, and uninstall iterate BESPOKE_HOSTS instead of hardcoding kimidesktop; behavior for the single registered host is identical (verified live)
- [x] The extracted handshake primitive is available to the HOST_EMITTERS per-host verification path, with an in-phase-decided default policy that does not add unacceptable doctor latency or false verdicts
- [x] A second (test-only) BespokeHost registered in a test proves the registry/iteration is genuinely generic (lifecycle runs for it without kimidesktop-specific code)
- [x] No regression: existing per-host doctor behavior and the D-055 kimi-desktop guarantees hold; full suite green

### Phase 3: Extension recipe doc + CHANGELOG + cascade + close-out

**Goal**: Write a concise "how to add a bespoke auto-write host" recipe (names the BespokeHost protocol members + the shared primitives to reuse). Update CHANGELOG (fold into the unreleased 1.10.0 entry). Full test run; cascade over D-056 / subsys.scaffold / subsys.mcp-server resolved; gameplan closed with a post-mortem. Confirm the D-055 kimi-desktop acceptance criteria still hold (behavior-preserving).
**Depends on**: Rewire entry points to the registry; offer the handshake to the generic host path.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A concise 'how to add a bespoke auto-write host' recipe exists (names the BespokeHost members + shared primitives to reuse), and a doc-content test pins it
- [x] CHANGELOG's unreleased 1.10.0 entry mentions the framework; no new version bump
- [x] cascade over D-056 / subsys.scaffold / subsys.mcp-server resolved
- [x] The D-055 kimi-desktop acceptance criteria re-verified live (byte-identical composition, self-heal, handshake, UNC guidance); full suite green; gameplan closed with a post-mortem
