# Chat Handoff Index — evidence traversal 1.14.0

> Last updated: 2026-07-25
> Status: Phase 5 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1002

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
| 0 | Single-source the status parser and expose defaulted status | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | One atomic symlink-refusing write path for tracked markdown | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Well-formedness at the write boundary | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Implement D-063 so the curator stops proposing from absent evidence | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Resolve H-20 with capability-not-presence engine identity | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Preserve foreign config and converge existing installs | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Restore full lesson propagation, close H-19, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-25

Single-sourced the entry-status grammar and made defaulting observable, which closed the reframing defect: cz_list_findings went from 21 findings all reading "active" with a null date to 17 resolved / 4 open with every date populated and 21/21 status_source="parsed". Three readers each carried their own **Status** pattern and only graph/abstract_index.py tolerated the "- **Status**:" list bullet that add_finding emits — so the fix was promoting the correct copy, not writing a new one. It lives in markdown/sections.py because that module imports only `re`: analyze.py imports graph.index, which forces abstract_index to import analyze lazily, so analyze structurally cannot host a module-level regex. Shipped the two seam tests (test_canonical_parsers, test_render_roundtrip), the per-register parse reconciliation, open-findings surfacing in cz_critique and the digest, and the shared L-24 adversarial fixture. Suite 1002 to 1016.

Two criteria closed as NOT-APPLICABLE rather than faked, and one open item deliberately left unresolved. (1) The contract-fixture regeneration criterion does not apply: that fixture's HARDENING corpus contains zero Status lines, so "active"/null is the honest output there, and test_contract_corpus compares a key SUPERSET which already tolerates the added status_source key — nothing to regenerate. (2) The criterion text says "20 findings, 3 open"; it is 21 and 4 because H-21 was recorded after the plan was written — correct evolution, not a miss. (3) O-04 (the 27 founding decisions carry no date) stays open by design: the reconciliation now reports them as "defaulted", which is the correct and honest classification, and backfilling dates is deferred to 1.14.1 because the ordering only matters to the parked ranker work. Every new test was demonstrated RED on a detached worktree at pre-1.14.0-writepath before being green here; that harness is recorded as an output for the remaining phases.

### Phase 1 — completed 2026-07-25

writer.write_atomic became the single byte-write for tracked content: refuse_if_symlink, sibling temp (never mkstemp, whose 0600 would re-permission every tracked doc), the target mode preserved, os.replace with a bounded Windows retry, unlink in a finally. Four sites that bypassed markdown/writer.py entirely — and therefore never ran refuse_if_symlink — now route through it; that bypass is why a planted symlink made cz_write_handoff write OUTSIDE the repo and report ok:true. No revision bump inside write_atomic: the callers already bump, which corrects all three planning drafts. An RLIMIT_FSIZE probe proves a failed write leaves a populated DECISIONS.md sha256-identical where pre-fix it destroyed 92,027 -> 38,334 bytes. The guard is path-shaped via the AST, not an allowlist, because ~30 write_text sites exist and an allowlist that size is a registry the next writer joins. The first CI matrix caught what no local run could: a POSIX-only module-level import disabled the entire test file on Windows, hiding the one behavior only Windows can verify.

### Phase 3 — completed 2026-07-25

Implemented what D-063 decided and nobody coded: the never-surfaced obsoletion arm is gone. It proposed DELETING lessons from the absence of a gitignored machine-local file, so on any fresh clone, teammate machine or CI runner it proposed obsoleting 100% of the corpus — measured 25 of 25, including a lesson promoted the day before and three that are the outputs of the consolidation ritual. Live repo went 6 obsolete proposals to 0; a fresh clone went 25 to 0 with all 25 lessons standing; the standing loop no longer consumes the corpus. Three companion fixes so the guard does not trade a false wipe for a false green: the surviving never-surfaced wording reads UNMEASURED with no suggested op, loop_step distinguishes no-evidence convergence from healthy convergence, and the digest's obsoletion INSTRUCTION is gated the same way — silencing the curator while leaving the surface that issues the instruction would have been a half-fix that fires on the very next fresh clone. Two existing tests pinned the pre-decision behavior and were retargeted to assert the decided contract rather than weakened. No config key added: INVARIANT-05 and D-015 forbid an enable/disable flag.

### Phase 2 — completed 2026-07-25

One shared normalizer with three field shapes, applied at all five render sites, closed the content-injection class. Before: a title containing a newline plus a heading returned ok:true, forged a genuine-looking D-900, absorbed the real entry's body, and advanced the next id to D-901 — 899 ids burned irreversibly in an append-only corpus with no repair op. After: one entry in, one entry out, ids sequential, the malicious text rendered as literal prose. Empty titles get a visible placeholder so no allocated id is ever unreachable, quoted lesson numbers no longer shift the sequence, and a pipe or newline in a phase name can no longer eat half the name or make a phase permanently untransitionable (H-02, which was marked resolved and live). Escaping is scoped to column zero because a mid-line bold Status label was probed and does not fool the readers; backslash-escape renders identically in CommonMark so the human view is byte-equivalent. The contract is normalize, never reject, so no write is lost and no mutation gains a hard block — recorded in D-066 and repeated in the phase record because this fix is one wrong INVARIANT-05 citation away from being killed by a reviewer.

### Phase 4 — completed 2026-07-25

doctor stopped reporting presence as capability on the path that matters most. The portable .mcp.json — the config most consumers get — was deliberately routed to hosts.verify_wiring, which on a native host is shutil.which(argv[0]); '✓ MCP server launchable — uvx' meant the string uvx resolved on PATH and nothing was ever spawned. It now completes an MCP initialize handshake and reports 'serverInfo clauderizer 1.13.0', warning at exit 3 on a served-vs-source skew — never a pass, never a failure, because a separately-installed server legitimately lags. hosttargets.verify_emitted_wiring was upgraded from a substring match to the same handshake, so a config naming a non-existent command now fails the contract where it passed for all eleven auto-write hosts. H-20 resolved with its own recorded fix and its own three regression tests, which three planning drafts had re-derived from scratch instead of reading. The handshake is memoized on (command, args), measured warm 1.0s and cold-cache 2.7s against an 8s budget, so --deep's nine identical entries cost one spawn. quickstart.yml gained an MCP leg that spawns the PUBLISHED server on a clean runner and asserts its identity and tool surface — the gap test.yml structurally cannot see (L-60), and precisely the gap that let this repo's hook and MCP client run different engines. Two plan corrections came out of the work: the CLAUDE_CODE skip must stay (C-01), and verifying identity means doctor spawns, so unit tests need a seam that reports 'skipped' rather than 'unverifiable' — being told not to look is a different claim from looking and not being able to tell.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A criterion that names a specific line to DELETE encodes an assumption about why that line exists, and deleting-to-satisfy is how a plan converts a guard into a regression. Before removing a guard a plan told you to remove, reproduce the behavior it produces: here the skip was not an oversight excluding a host from a check, it was structural, because the host has no entry in the registry the loop indexes. State criteria as the PROPERTY required ("the host INVARIANT-07 protects is identity-checked") rather than the EDIT imagined to produce it ("delete line N") — the property survives being wrong about the mechanism, and in this case was satisfied better by a different one.
