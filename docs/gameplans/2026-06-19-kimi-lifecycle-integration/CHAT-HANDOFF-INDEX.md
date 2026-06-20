# Chat Handoff Index — kimi-lifecycle-integration

> Last updated: 2026-06-19
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

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
| 0 | Bootstrap &amp; design lock | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Event-dispatching hook engine | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Claude Code wiring of new events | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-2-HANDOFF.md |
| 3 | AGENTS.md and kimi host target | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs, version bump, release to PyPI | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-19

Locked the design against confirmed host contracts (claude-code-guide for Claude Code's 24-event hook surface + SessionStart source=compact + PreCompact/PostCompact stdout NOT injected; kimi-cli docs for its 13 events with all stdout injected). Recorded D-025 (one event-dispatching hook entry; every handler read-only and exits 0), INVARIANT-06 (generalizes INVARIANT-04 to all events), and gameplan D1-D3 (per-host wiring to each host's real stdout contract; non-destructive kimi target = AGENTS.md stanza + emitted setup snippet, no global-config mutation; no enable/disable flag per INVARIANT-05). O-01 tracks the undocumented kimi MCP-registration TOML schema. Baseline full suite green at HEAD before any source change. Five phases (0-4) with machine-checkable exit criteria.

### Phase 1 — completed 2026-06-19

Shipped the event-dispatching hook engine. hook/dispatch.py routes the host's stdin hook payload on hook_event_name to read-only handlers in hook/handlers.py (session_start [source-aware: frames source=compact/clear], pre_compact [persist-now reminder + state], post_compact [re-digest], user_prompt_submit [auto-analyze, quiet-when-empty]). Empty/garbage/non-object stdin falls back to the SessionStart digest — the exact shape the hardened no-arg hook_digest_probe sends — so the H-08/H-09 legs are untouched. --version/--help answer the identity probe before any stdin/repo read (L-09/L-10). sessionstart.py became a back-compat shim; the clauderizer-hook entry point now targets hook.dispatch:main. 37 new diverse tests (routing, adversarial stdin per L-18/L-19, exit-0-on-handler-crash, read-only INVARIANT-06 snapshot, per-handler behavior, shim delegation). Full suite 389 passed / 4 skipped, no regressions.

### Phase 2 — completed 2026-06-19

Generalized init._register_hook to register the hook wrapper under both SessionStart and UserPromptSubmit (the same command), preserving foreign hooks per event, idempotent on re-run, and migrating the pre-0.14 SessionStart-only shape by adding UserPromptSubmit without duplicating SessionStart. PreCompact/PostCompact are intentionally not registered on Claude Code — their stdout is dropped there (D1); SessionStart(source=compact), already matcher-less in the registration, covers post-compaction re-injection. 5 new tests in test_init.py; full suite 394 passed / 4 skipped.

### Phase 3 — completed 2026-06-19

Added the cross-harness host target (D2). init injects the SAME host-agnostic Clauderizer stanza into AGENTS.md as into CLAUDE.md (one source, no drift — L-16), giving kimi (KIMI_AGENTS_MD) and other AGENTS.md-aware harnesses the memory pointer. init also emits .clauderizer/kimi-setup.md — a strictly non-destructive guide (a repo-local file, never the global ~/.kimi/config.toml) with [[hooks]] entries for all four events (kimi injects every hook's stdout, unlike Claude Code — D1), TOML literal-string commands pointing at the existing wrapper, and MCP-registration guidance that honestly cites O-01. Added RepoPaths.agents_md and RepoPaths.kimi_setup. 5 new tests; full suite 399 passed / 4 skipped; the generated TOML was validated to parse with tomllib.

### Phase 4 — completed 2026-06-19

Shipped 0.14.0 to PyPI. Bumped the version across pyproject + clauderizer.__init__ + CHANGELOG; subsys.scaffold 0.6.0→0.7.0 with the cascade resolved (feat.init-cli pin ^0.5.0 still satisfied). README updated (feature row + init tree). clauderize release-check green — all four registries unclaimed, clean tree, origin/main==HEAD. Committed f7da75a to main, pushed, tagged v0.14.0 (tag==pyproject, H-07 ok), pushed the tag, cut the GitHub Release → publish.yml OIDC build → clauderizer 0.14.0 live on PyPI (wheel + sdist; index latest=0.14.0). C-01 / lesson #1 (promoted): the release commit's three Windows CI cells went red AFTER publish on a Linux-centric test assertion (forward-slash hook path); the product was unaffected (the wheel ships no tests and kimi-setup generates correctly on Windows), fixed test-only in 7d708da → main CI 9/9 green. No re-release needed.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Before tagging a release, execute the suite on every host leg the CI matrix covers — a Linux-only green is a guess about Windows, and the Release→PyPI step is irreversible. A path/separator assertion in a test is itself a platform claim: assert the wrapper FILE (hook.sh|hook.cmd), never the slash. (promoted 2026-06-19: L-20)

**2.** Reference docs drift together on a taxonomy change. When hook events or the tool surface change, sweep every non-single-sourced present-tense doc at once: README's MCP-surface tool list, TRUST.md (what init writes / what executes), UPGRADING.md's uninstall script, and SECURITY.md's scope line. The single-sourced CLAUDE.md/AGENTS.md stanza (L-16) is safe; those four are not. Append-only history (CHANGELOG, gameplan handoffs and cascade reports) records the OLD counts on purpose — never 'correct' it to the new number. *(evidence: 0.14.0 docs audit (2026-06-20): README MCP surface listed 24 tools vs tools_list.py's 31; preflight 7-vs-8 checks; TRUST/UPGRADING/SECURITY still described pre-0.14 SessionStart-only wiring (no UserPromptSubmit / AGENTS.md / kimi-setup).)* (promoted 2026-06-20: L-21)
