# dogfood-followup-findings — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-23

## Phase Status

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

## Outputs Registry

### Phase 0 Outputs

```
triage: All 12 follow-ups reproduce on 1.0.3 (F4 live-confirmed: `ops --help` has no op list; ops.py:808 "see tools_list" is a dead module ref). Fix-now (10): F4->P1; F8/F9/F11->P2; F6->P3; F5->P4; F7/F10->P5; F1/F12->P6. Document-as-intended (F13 set)->P7. 0 wontfix. Baseline 602 tests green.
```

### Phase 1 Outputs

```
ops-discoverability: F4 closed. Added `clauderize ops --list` (read/write-tagged op list + one-line summaries) and `--schema <op>` (required/optional args as JSON), via ops.list_ops()/op_schema() introspecting the shared REGISTRY (no second schema to drift). Unknown-op hint now points at `clauderize ops --list` (dead 'tools_list' ref gone). +5 tests incl. an all-ops introspection seam test (L-34); README documented in-phase (D-036). Suite 607 green (was 602).
```

### Phase 2 Outputs

```
ops-ergonomics: F8 was a FALSE finding (C-02: the dogfood's "exit 0 on ok:false" was the L-29 $?-in-outer-shell trap) — `clauderize ops` already exits 0/1/2 correctly, so no code, --strict de-scoped, O-01 moot. F9 fixed: cz_resolve_cascade now states the exact close-contract (verdicts + updates_applied/deferred) in BOTH its result message and docstring — no more silent "still pending" guessing; +1 test. F11 satisfied by P1's --schema (the real accepted args are now discoverable; no arg-vocab change needed). Suite 608 green.
```

### Phase 3 Outputs

```
cascade-dedupe: F6 closed. A manual cz_cascade now reuses an existing PENDING cascade report for the same entity (matched transition-agnostically — a transition cascades as "status a -> b" but a hand call types "a -> b") instead of writing a duplicate "needs review" report; the cz_cascade docstring now states transitions auto-cascade. New `_pending_report_for` helper + 1 test. Suite 609 green.
```

### Phase 4 Outputs

```
profile-aware-preflight: F5 closed. When profile='generic' leaves the test/build command empty but the repo now detects as a real language (e.g. pyproject.toml → python), preflight's skip detail becomes an advisory naming the language and the fix (set the command in profile.lock, or delete it and re-run init) instead of a silent no-op. Read-only and advisory (INVARIANT-05) — `_generic_profile_hint` only reads the detector, never rewrites profile.lock. +2 tests. Suite 611 green.
```

### Phase 5 Outputs

```
correctness-lifecycle: F7: MCP serverInfo.version now reports clauderizer's version — set on the wrapped lowlevel server (mcp._mcp_server.version), guarded, since FastMCP has no public version param; test confirms. F10: retiring an entity = `cz_transition_status(id, to_status="retired"|"obsolete")` — those statuses now demote in ranking (_STALE_STATUSES) and flag shaky in cascade (_SHAKY_STATUSES); the docstring documents it as the append-only alternative to deleting a tracked doc (INVARIANT-03). +3 tests. Suite 614 green.
```

### Phase 6 Outputs

```
front-door-polish: F1: added a `clauderizer` console-script alias (pyproject) so `uvx clauderizer <cmd>` works; `clauderize` stays canonical. F12: amendment list args now render as a readable inline list (not a Python literal) and the amendment cascade line is a conditional prompt, not a false "pending" TODO; the stub-placeholder-on-first-write was ALREADY correct on HEAD (append_to_section replaces it) — locked with a regression test. +3 new tests, 1 existing test updated to the new amendment wording (L-34 seam). F13 (document intentional behaviors) and the 1.0.4 CHANGELOG are deferred to P7 (the docs sweep, per D-039). Suite 617 green.
```

### Phase 7 Outputs

```
docs-sweep: Human-readability sweep of the product docs (D-038/D-039). Wrote the plain-language 1.0.4 CHANGELOG; de-jargoned the README (removed INVARIANT-05 / G1–G7 / D-NNN citations from human-facing prose); documented the intentional behaviors a newcomer trips on (AGENTS.md is a byte-identical copy of CLAUDE.md; .mcp.json is gitignored when machine-specific; the hook fires every prompt but the digest injects once/session; saas scaffolds empty stubs, so start at standard); added a `doctor` step to the empty-folder quickstart. A fresh-human-reader subagent verified onboarding and confirmed `ops --list` (38) matches the README's "38 tools". Suite 617 green.
```

## Corrections Log

### C-01 — Phase Documentation diligence and human-usability

**Phase**: Documentation diligence and human-usability
**What gameplan said**: D-036 framed documentation as a "dual-audience (agent + human)" deliverable; I read the user's "docs must be human-usable as well" as a request to serve a second (human) audience alongside agent-oriented docs.
**What was actually correct**: There are no agent-only docs. ALL docs are written for a human reader in plain prose. The user's point was about STYLE — the documentation the agent produces reads like an agent wrote it (shorthand, F-/H-/D- codes, internal jargon) and must instead read like a human wrote it for a human. Agents get their machine contract from the MCP tool schemas + cz_* descriptions, never from prose docs.
**Why**: Misread "human-usable as well" as additive (a second audience/tier) rather than corrective (write the docs in human prose, not agent shorthand). Corrected by D-037 (supersedes D-036).
**Lesson**: When the user says docs must be human-usable, it is about plain-prose STYLE for a human reader — there are no agent-only docs and no second "agent" audience to serve; do not invent a dual-audience framing.

### C-02 — Phase ops ergonomics and consistency

**Phase**: ops ergonomics and consistency
**What gameplan said**: F8: `clauderize ops` exits 0 even when a result is ok:false (so add an opt-in --strict, per D2).
**What was actually correct**: Not a bug. On current code `clauderize ops` already exits non-zero when any op returns ok:false (cmd_ops returns `0 if all_ok else 1`; run_batch sets all_ok False on any ok:false) and 0 on success — verified live with &&/|| (never $?). The dogfood's "exit 0" repro used `echo $?` through the WSL shim, which read the OUTER shell's exit, not WSL bash's (the L-29 trap). F8 de-scoped; --strict not built; O-01 (caller audit) moot since the default already signals failure.
**Why**: A subagent finding asserting an exit code via `; echo $?` over `wsl.exe bash -lc` is unreliable (L-29: $VAR/$? expand in the outer Git-Bash). Verify exit-code claims with &&/|| or a file, never $?.
**Lesson**: Exit-code findings gathered via `…; echo $?` over the WSL shim are suspect (L-29 $?-in-outer-shell). Re-verify with `(cmd) && echo OK || echo FAIL` before acting; F8 was a phantom bug from exactly this.
