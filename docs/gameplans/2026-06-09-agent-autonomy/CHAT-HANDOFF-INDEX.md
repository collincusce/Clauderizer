# Chat Handoff Index — agent-autonomy

> Last updated: 2026-06-09
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 162

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
| 0 | Serialized tracked writes | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CLI write parity: clauderize ops | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wiring truth: session-host-of-record | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cold-start breadcrumb hook wrapper | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Stale-engine proof, amendment pointer, 0.7.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-09

Closed H-05 by serializing every tracked write through an advisory file lock. src/clauderizer/locking.py implements write_lock() over .clauderizer/write.lock: O_CREAT|O_EXCL create with holder metadata (pid, host, since/ts, nonce) inside, bounded polling up to acquire_timeout (10s), and stale takeover (30s) done by atomic rename-to-trash so two reclaimers can never double-unlink a rival's fresh lock; a post-create nonce read-back closes the residual misjudged-takeover window. Contention surfaces as LockHeld — retryable, naming holder pid/host/since and the wait. All 18 public mutations.* functions acquire it via the @_locked decorator, spanning the full read-modify-write (IDs are allocated from the read that the final section write trusts, so locking individual writer calls would not have fixed H-05); the lock is reentrant per thread because mutations compose mutations (consolidate_lessons -> add_lesson), threads of one process serialize on a per-path RLock, and read tools never touch it (L-03).

Suite went 139 -> 148. The load-bearing regression spawns 8 real writer processes that block on a GO sentinel and race add_lesson on one repo: 8 distinct sequential numbers, 8 surviving appends, no duplicates anywhere in the section. Also pinned: crashed-holder delay bounded by stale_timeout (exit criterion 2), LockHeld shape, release-on-exception, reentrancy, thread serialization, and no lock residue after mutations. H-05 was resolved through the locked path itself (task 0.4) by a fresh-process write, because the session's live MCP server still held the pre-lock module in memory — the lock guards MCP writers from the next server start onward.

### Phase 1 — completed 2026-06-09

Closed L-05 structurally: every tracked write is now reachable without an MCP client. src/clauderizer/ops.py is the single dispatch surface — the 24 tool bodies moved there verbatim as module-level functions whose names, signatures, and docstrings ARE the tool contract; mcp_server.py now registers those exact function objects in a loop (schemas derive from the same callables the CLI executes — identity by construction, not equality by test), and `clauderize ops <file.json|->` executes JSON batches of {op, args} against the same registry with per-op results and meaningful exit codes (0/1/2). Args-in-files is deliberate: it bypasses the PS 5.1 quoting hazards that motivated the shim era, and the reader tolerates BOMs (utf-8-sig + stdin strip). Phase 0's deferred lock residue closed along the way: cascade-report writes, handoff regeneration, and the create-gameplan config flip now serialize on the write lock inside their op bodies (covering MCP and CLI identically), and preflight's baseline refresh locks at the write site — skipping self-healingly under contention rather than holding the lock across a minutes-long test run or failing the ritual.

Suite 148 → 162 (+14 in tests/test_ops.py): registry==TOOL_NAMES enumeration parity, MCP-vs-ops read and write parity on twin repos, batch continues-after-failure semantics, tool-level ok:false counting as failure, CLI file/stdin/BOM/exit-code behavior, a cold-process invocation, lock coverage of the non-mutation writes, dry-run lock-freedom (L-03), and the baseline contention-skip. Docs: the CLAUDE.md stanza and GAMEPLAN-PROCEDURE 1.2.0 (new "Recording Without MCP" quick-reference section) name clauderize ops as the canonical fallback, retiring shim guidance. Dogfood (task 1.5): a real Outputs Registry entry (mcp_less_write_demo) was recorded on this repo by `clauderize ops /tmp/dogfood_ops.json` in a fresh process with the MCP server never spawned — the exit-criterion evidence, alongside the in-test cold-process run.

### Phase 2 — completed 2026-06-09

Closed H-04's residuals by making the session host a recorded, first-class fact. New src/clauderizer/hosts.py owns the vocabulary (native | windows-wsl:<distro>), the adoption heuristic (existing wsl.exe wiring's -d arg beats environment sniffing — the env said "Ubuntu" while the working wiring said "ubuntu"), shim composition (command/args split for .mcp.json, one command string for the hook, no double-wrapping), and two probe primitives: spawn_probe (init's pre-write gate) and verify_wiring (doctor's three-state verdict). init resolves the host (flag > config record > adopt wiring > native), records it in [host] session_host, and refuses to write any composed command that fails a real --version spawn — the exact H-04 mis-composition ('clauderize clauderizer-mcp', exit 2) now raises WiringRefused with nothing written. doctor grew to 14 checks and certifies launchability FOR the recorded host by actually round-tripping through wsl.exe interop (showing the served engine version), or honestly exits 3 with "unverifiable from this host". Both entry points answer --version/--help deterministically so probes prove launch, not EOF luck.

Exit criteria all green: plain `clauderize init` on this repo regenerated the hand-maintained wiring byte-identically (.mcp.json and settings.json "kept"; config gained only the session_host line) — the hand-wiring era ends with no migration step; doctor invoked from PowerShell through the shim certified 14/14 with end-to-end round-trip evidence, exit 0; suite 195 green (162 + 33); H-04 resolved via clauderize ops in a fresh process. Documented residual: a mid-session wiring repair still needs a session restart to attach MCP tools (harness enumerates servers once at session start).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Integration

**1.** A long-running MCP server executes the modules it imported at session start: after editing engine code, in-session cz_* writes still run the pre-edit code. Any dogfood or verification that must traverse a new code path needs a fresh process (stdio probe today, clauderize ops after Phase 1) — otherwise it silently exercises the old path while appearing to test the new one.

**4.** An exit-0 probe only guards what the probed surface actually distinguishes: clauderizer-mcp --version exited 0 BEFORE --version existed (FastMCP treats EOF-on-devnull as clean shutdown), so the spawn test would have passed by accident on a server that ignored the flag. Before building a guard on an exit code, run the probe against the unfixed binary and confirm it fails/behaves as assumed — D5's "prove the guard fires" applies to the probe itself.

### Category: Design

**2.** When two transports must expose the same operation surface, register the same function objects on both rather than testing two implementations for equality: schemas and behavior stay identical by construction, and the parity test reduces to one enumeration check (registry keys == published tool names). Wrapper layers for cross-cutting concerns (locking, context) belong inside the shared bodies, not around them — introspection-based schema derivation makes wrappers a drift risk.

**3.** When retrofitting a host-of-record (or any "which environment is this for" field) onto an existing install, the most reliable detector is the artifact that already works: the hand-maintained wiring's own -d argument named the distro correctly where environment sniffing disagreed on case (WSL_DISTRO_NAME=Ubuntu vs the wiring's ubuntu — only the former breaks byte-identical regeneration). Adopt observed-working state first; derive from the environment only as fallback.
