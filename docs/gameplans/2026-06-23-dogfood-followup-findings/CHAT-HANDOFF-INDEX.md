# Chat Handoff Index — dogfood-followup-findings

> Last updated: 2026-06-23
> Status: All 8 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 602

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
| 0 | Bootstrap and triage | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-0-HANDOFF.md |
| 1 | ops schema discoverability | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-1-HANDOFF.md |
| 2 | ops ergonomics and consistency | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cascade dedupe | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Profile-aware preflight | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Correctness and lifecycle | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-5-HANDOFF.md |
| 6 | Front-door and polish | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-6-HANDOFF.md |
| 7 | Documentation diligence and human-usability | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-23

Triaged the 12 dogfood follow-ups against shipped 1.0.3. F4 confirmed live (`clauderize ops --help` exposes no op/arg schemas; the unknown-op error's "see tools_list" points at a module, not a runnable command — ops.py:808). The rest reproduce by code-path argument: H-14/H-15 changed only init.py wiring + cli.py doctor, leaving the ops/cascade/profiles/serverInfo/scaffold paths untouched. Classification per D1: 10 fix-now (F1, F4–F12) mapped across P1–P6; the F13 set documented-as-intended in P7; 0 wontfix. Baseline pinned at 602 tests green. clean_tree is intentionally dirty (commit is the last step), so that preflight check is advisory here per INVARIANT-05.

### Phase 1 — completed 2026-06-23

Closed F4 (ops discoverability). Added `ops.op_schema(name)` and `ops.list_ops()` — they introspect each op's `inspect.signature` (required vs optional+default) and docstring (one-line summary) from the SAME shared REGISTRY the MCP server registers, so the CLI and agent surfaces cannot drift. Wired `clauderize ops --list` (tagged op list + summaries + required args) and `clauderize ops --schema <op>` (full args as JSON); `file` is now optional. Fixed the unknown-op error (ops.py) to point at `clauderize ops --list` instead of the dead "see tools_list" module reference. 5 new tests in test_ops_introspection.py, including a seam test that every op in REGISTRY introspects without error and is JSON-serializable (L-34). README documented in-phase per D-036 (command list + the "No MCP client?" section). Full suite 607 passed / 4 skipped. No entity status changed (feature addition), so no cascade.

### Phase 2 — completed 2026-06-23

Net result: one real fix (F9), one false finding retired (F8), one already-covered (F11). F8 ("ops exits 0 on ok:false") did not reproduce — verified with &&/|| that `clauderize ops` already exits non-zero on any ok:false; the dogfood's repro used `; echo $?` over the WSL shim and read the outer shell's exit (L-29). Recorded as C-02; --strict not built and O-01 (caller audit) resolved as moot. F9 (cascade-closure was non-obvious): cz_resolve_cascade now spells out the two-part close — a verdict for every dependent AND updates_applied (or "none") / updates_deferred — in its result `summary` (so a pending report says exactly what's missing) and in its docstring (which surfaces via `ops --schema`). New fixture-independent test in test_cascade_reports.py. F11 (arg-vocab) needs no code: P1's `ops --schema <op>` now makes each op's real accepted args discoverable, which was the underlying confusion. The `--strict` exit criterion is intentionally left unchecked (moot per C-02). Suite 608 passed / 4 skipped.

### Phase 3 — completed 2026-06-23

Fixed the double-cascade (F6) at the source. cz_transition_status auto-cascades; following the docs to then run cz_cascade for the same change wrote a second report because the two used different transition labels ("status a -> b" vs a hand-typed "a -> b") and the filename only sequenced. cz_cascade now looks for a pending report already covering the entity — matching the report header's entity prefix, transition-agnostic, with a trailing-space boundary so subsys.web doesn't match subsys.web-ui — and reuses it (returns reused:true, creates nothing) with a message pointing to cz_resolve_cascade. Its docstring now says transitions already cascade, so the manual call is only for separate edits (surfaces via ops --schema). New helper ops._pending_report_for + a fixture-backed test in test_cascade_reports.py. The auto-cascade path (cz_transition_status) and direct C.run are unchanged. Suite 609 passed / 4 skipped. No entity status changed, so no cascade.

### Phase 4 — completed 2026-06-23

Closed F5 (the generic-profile preflight gap). When init runs on an empty dir the profile is detected as 'generic' and profile.lock's test/build commands are blank, then preserved on re-init — so the tests/build preflight checks were permanent silent no-ops in a real (e.g. Python) repo. Added `preflight._generic_profile_hint(root, kind)`: when the command is empty AND the profile is 'generic', it runs the detector against the current tree, and if that now yields a real language with a command, the skip detail becomes an advisory naming the language and the remedy (fill profile.lock, or delete it and re-run `clauderize init`). It only READS the detector — never rewrites a user's profile.lock — and stays a 'skip' (advisory, never a hard block, INVARIANT-05). Two tests in test_preflight_profile_hint.py (fires for a pyproject.toml repo, silent for a language-less dir, writes nothing). Suite 611 passed / 4 skipped. No entity status changed, so no cascade.

### Phase 5 — completed 2026-06-23

Two small fixes. F7 (serverInfo version): FastMCP has no public version parameter, but the lowlevel `Server` it wraps does — build_server now sets `mcp._mcp_server.version = __version__` inside a try/except so a future SDK change can't break startup (worst case it reports the SDK version as before). serverInfo.version now matches `clauderize --version`; verified by test_serverinfo_version.py (importorskip mcp). F10 (entity retirement): rather than add a delete verb (memory is append-only, INVARIANT-03), `cz_transition_status` IS the retire verb — transition an entity to `retired`/`obsolete`. Those statuses were added to _STALE_STATUSES (demoted in rank_relevant, like superseded decisions) and _SHAKY_STATUSES (cascade flags dependents of a retired foundation); the cz_transition_status docstring now spells out retiring as the sanctioned, no-delete cleanup (surfaces via `ops --schema`). Tests: a retired entity ranks below an active peer of equal overlap. Suite 614 passed / 4 skipped. No entity status actually changed in the engine repo, so no cascade.

### Phase 6 — completed 2026-06-23

Code-only phase (docs go to P7 per the two-layer split, D-039). F1: a `clauderizer` console-script alias in pyproject so the intuitive `uvx clauderizer init` resolves; `clauderize` remains canonical; release-time `uvx` check will confirm end-to-end. F12: (a) the stub-placeholder-after-first-write was already correct on HEAD — `sections.append_to_section` replaces a lone `_(…)_` placeholder — so I added a regression test rather than code (the dogfood saw 1.0.2 behaviour); (b) `cz_add_amendment` now coerces list `affected_sections`/`affected_phases` to a readable inline list instead of emitting a Python literal `['…']`; (c) the amendment's cascade line changed from a perpetual `_pending — run cz_cascade_` to a conditional "if this amendment changed a tracked entity, run cz_cascade", which is what the dogfood misread as a stale TODO. Updated the one existing test that asserted the old wording (the shared-render seam, L-34). 3 new tests in test_p6_polish.py. Two exit criteria deferred to P7: F13 (documenting the intentional-by-design behaviors) and the 1.0.4 CHANGELOG — both are product-doc work that belongs in the human-readability sweep. Suite 617 passed / 4 skipped.

### Phase 7 — completed 2026-06-23

Documentation human-readability sweep, scoped to the product layer (D-039). Deliverables: the 1.0.4 CHANGELOG entry in plain language (no F-/H-/D- codes); a README de-jargon pass removing internal IDs from human-facing prose (the MCP-surface "INVARIANT-05" citations became "advisory — they surface findings, you decide"; the Maturity "G1–G7" became "the 1.0 readiness gates"); plain-language notes for the four intentional behaviors a fresh reader flagged (AGENTS≡CLAUDE byte-identical, .mcp.json gitignore vs the commit step, hook-every-prompt with once/session dedup, saas empty stubs + "start at standard"); and a `clauderize doctor` step added to the empty-folder quickstart so a newcomer verifies the MCP wiring. Verified with a fresh-human-reader subagent (read-only): it confirmed both quickstarts are concrete and well-ordered, that `ops --list` enumerates 38 ops matching the README's "38 tools", and surfaced the punch-list I then fixed. One observation it raised — the docs describe 1.0.4 while the installed binary is 1.0.3 — is the expected in-flight state and resolves when 1.0.4 ships (the next step). Suite 617 passed / 4 skipped. Docs only; no entity status changed, no cascade owed.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When the user says docs must be human-usable, it is about plain-prose STYLE for a human reader — there are no agent-only docs and no second "agent" audience to serve; do not invent a dual-audience framing.

**2.** Exit-code findings gathered via `…; echo $?` over the WSL shim are suspect (L-29 $?-in-outer-shell). Re-verify with `(cmd) && echo OK || echo FAIL` before acting; F8 was a phantom bug from exactly this.
