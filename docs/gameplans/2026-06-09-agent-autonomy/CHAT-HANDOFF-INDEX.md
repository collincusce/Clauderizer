# Chat Handoff Index — agent-autonomy

> Last updated: 2026-06-09
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 211

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
| 3 | Cold-start breadcrumb hook wrapper | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Stale-engine proof, amendment pointer, 0.7.0 | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-4-HANDOFF.md |

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

### Phase 3 — completed 2026-06-09

Closed H-01's residue: a cold session whose engine cannot launch now learns why. Premise proven live before building (lesson #4): a dead console script through the direct wiring puts its error on stderr and NOTHING on stdout — and stdout is the only channel the harness injects into session context. The fix is a thin wrapper one layer below the engine: init writes .clauderizer/hook.sh (hook.cmd for native-win32), bakes the unshimmed engine argv into it, spawn-tests the registered wrapper command, and registers it as the SessionStart hook. The wrapper captures the engine's combined output, passes it through on success, forwards args (so --version probes stay deterministic through the wrapper), and on any failure prints "[Clauderizer] engine unreachable: exit N from <engine> — run clauderize doctor" plus the captured error — on stdout, always exit 0. doctor grew to 16 checks: wrapper presence (missing = drift), freshness (baked engine argv vs a fresh resolution = "?" when the engine moved), and a re-init nudge for pre-wrapper direct wiring; the hook launch verdict now certifies the entire chain wsl.exe → /bin/sh → hook.sh → engine.

One deliberate deviation from D4's letter (correction): for windows-wsl the wrapper is WSL-side sh registered behind the wsl.exe shim, not a Windows .cmd — a cmd wrapper started in this repo's \\wsl.localhost UNC cwd would inject a "UNC paths are not supported" warning into every HEALTHY session and resets cwd, while only covering "wsl.exe dead but cmd alive", a state in which the UNC repo is unreachable and no session starts here anyway. Exit criteria green: live demo on a scratch repo (engine binary renamed, registered command run verbatim from PowerShell) recorded as H-01's closure evidence — before: exit 127/empty stdout; after: exit 0/breadcrumb; the remaining silent boundary (wrapper shell or wsl.exe itself dead, wrapper file deleted) documented explicitly in H-01's resolution; suite 211 green (195 + 16); this repo upgraded by re-init (only hook.sh + settings.json changed), doctor 16/16 exit 0 through the shim.

### Phase 4 — completed 2026-06-10

Phase 4 proved the last unproven guard and staged the release. The stale-engine thread closed with recorded evidence (H-06): verify_wiring now demands the round-trip identify its engine — a scratch repo pinned to uvx clauderizer[mcp]==0.5.0, which init legitimately writes because both 0.5.0 entry points pass exit-code probes (the lesson-#4 accident, observed live), fails BOTH of the current doctor's launch checks loudly (exit 2), while by-name uvx resolves PyPI latest and this repo's healthy wiring certifies 16/16. The same identity check killed a false green nobody had named: the D4 wrapper's always-exit-0 contract had turned a dead engine into a green hook verdict (lesson #7). cz_add_amendment's cascade pointer became conditional-and-honest (procedure 1.2.1), A-001's dangling pointer healed via an entry-anchored locked write, and the 0.6.0 post-mortem's open threads are all annotated closed-with-evidence or restated as Open Items O1/O2.

The release renumbered mid-close-out: the staged 0.7.0 collided with a pre-existing published GitHub Release v0.7.0 at the Phase-0 commit (source 0.6.0) whose PyPI publish had failed as a silent duplicate — found only when the user asked, because the Phase-4 sweep had checked source/captures/PyPI/uvx but never remote tags or Releases (C-04, H-07, lesson #9: a version is a claim across four unsynced registries). Resolution per user choice: retire 0.7.0 (CHANGELOG tombstone), ship as 0.8.0, and publish.yml now refuses tag/source skew up front. Final state: suite 215 green, doctor 16/16 certifying '(clauderizer 0.8.0)' through the shim, H-01..H-07 resolved. The v0.8.0 tag remains gated on a restart-validated cold start — this session, the first wrapper-era harness run, received no [Clauderizer] digest while the registered command works perfectly manually (restart_validation_observation). Next session: check the digest, then push main, tag v0.8.0, cut the GitHub Release (the gate now guards it), and close the gameplan.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**8.** init's refresh boundary is per-asset and a release must know it: create_if_absent assets (the installed GAMEPLAN-PROCEDURE.md) never track template bumps on re-init — by design, since host repos may hold annotated copies — so the engine repo's release flow syncs its own installed copy explicitly (template -> docs/gameplans/, done for 1.2.0 and 1.2.1). Releasing = bump pyproject + __version__ + pip install -e . (dist-info skew, H-03) + CHANGELOG + procedure-copy sync + re-init + restart-validated cold start BEFORE the tag; publishing fires on the GitHub Release (publish.yml Trusted Publishing), not the bare tag.

**9.** A version number is a namespace claim across FOUR registries that do not sync — source (pyproject/__version__), remote git tags, GitHub Releases, and the PyPI index — and staging a release means sweeping all four with fresh eyes: git tag -l AND git ls-remote --tags origin (tags can exist remote-only), the Releases API (a Release can exist for an unpublished version), and PyPI queried directly (uvx by-name answers from uv's cache and can hide a recent attempt). Phase 4 swept three, read 'by-name resolves 0.6.0' as confirmation, and double-claimed 0.7.0 — when that uvx result was actually the symptom of a failed v0.7.0 publish (H-07).

### Category: Integration

**1.** A long-running MCP server executes the modules it imported at session start: after editing engine code, in-session cz_* writes still run the pre-edit code. Any dogfood or verification that must traverse a new code path needs a fresh process (stdio probe today, clauderize ops after Phase 1) — otherwise it silently exercises the old path while appearing to test the new one.

**4.** An exit-0 probe only guards what the probed surface actually distinguishes: clauderizer-mcp --version exited 0 BEFORE --version existed (FastMCP treats EOF-on-devnull as clean shutdown), so the spawn test would have passed by accident on a server that ignored the flag. Before building a guard on an exit code, run the probe against the unfixed binary and confirm it fails/behaves as assumed — D5's "prove the guard fires" applies to the probe itself.

### Category: Design

**2.** When two transports must expose the same operation surface, register the same function objects on both rather than testing two implementations for equality: schemas and behavior stay identical by construction, and the parity test reduces to one enumeration check (registry keys == published tool names). Wrapper layers for cross-cutting concerns (locking, context) belong inside the shared bodies, not around them — introspection-based schema derivation makes wrappers a drift risk.

**3.** When retrofitting a host-of-record (or any "which environment is this for" field) onto an existing install, the most reliable detector is the artifact that already works: the hand-maintained wiring's own -d argument named the distro correctly where environment sniffing disagreed on case (WSL_DISTRO_NAME=Ubuntu vs the wiring's ubuntu — only the former breaks byte-identical regeneration). Adopt observed-working state first; derive from the environment only as fallback.

**5.** Know which output channel your consumer actually reads before designing failure reporting: the harness injects only a hook's stdout into session context, so a dying hook's perfectly informative stderr was indistinguishable from silence. A breadcrumb wrapper is therefore channel REROUTING (capture 2>&1, reprint on stdout, exit 0) at least as much as failure detection — and the same applies to any tool whose stderr goes somewhere humans don't look.

**6.** Place a reliability wrapper on the deepest layer whose failure still leaves the system reachable, not automatically on the consumer's host: for split-host wiring, a Windows-side cmd wrapper would add noise (UNC cwd warning into every healthy session) and fragility (cwd reset) while only covering states in which the repo itself is unreachable. Coverage analysis beats "host-native by default" — enumerate which failure modes each candidate layer can actually observe AND report through a channel the consumer reads.

**7.** Locally-sound guard contracts can compose into a false green: the D4 wrapper's always-exit-0 design (correct for hook stdout capture) silently defeated the spawn probe's exit-0-means-launchable assumption, so doctor certified a DEAD engine ('verified end-to-end' with a breadcrumb as the evidence string). When a new layer wraps a probed surface, re-derive what the outer signal still distinguishes — and prefer in-band identity (the output must claim who it is) over exit codes, which only say that something ran.
