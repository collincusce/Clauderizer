# Chat Handoff Index — windows-field-fixes-1.5.2

> Last updated: 2026-07-02
> Status: Phase 1 ready

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
| 0 | Repro & fix all four field bugs | ✅ COMPLETE | 2026-07-02 | 2026-07-02 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Ship 1.5.2 | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-02

All four field bugs reproduced and fixed with regression tests (+11, suite 775). (1) cp1252: new _stdio.harden_stdio switches stdout/stderr to errors=replace at the clauderize and clauderizer-hook entry points — glyphs degrade to ? instead of crashing, UTF-8 consoles untouched, MCP protocol channel deliberately left alone; PYTHONIOENCODING workaround obsolete. (2) frontmatter: _scalar parses inline flow lists — depends_on: [] is [] not the string whose characters became phantom deps. (3) heading tolerance: find_section gains fuzzy tiers (case-insensitive exact, word-boundary title-prefix) as OPT-IN, enabled only at the three corpus-append sites — the first global cut was caught by the back-compat golden shifting handoff composition (lesson #1 recorded); newest-first insertion order deliberately out of scope. (4) --run-cmd help now says launcher PREFIX, not binary path.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A tolerance/fuzz added to a shared parser must be OPT-IN at the call sites that need it, not a global default — the back-compat golden caught the first cut of the heading-title tolerance silently changing handoff composition ("Phase 1" prefix-matched "Phase 1: Wire it up", handoff token estimate 350→381) before it could ship. Scope the fuzz (fuzzy=True at the three corpus-append sites), keep every read path byte-identical, and let the golden arbitrate. This is the payoff of the golden-snapshot gate: it converts an invisible behavior drift into a red test within one suite run. *(evidence: tests/test_back_compat_focus.py failure on first fuzz cut (handoff_est_tokens 350→381); fix = find_section(fuzzy=False default) + fuzzy=True only at mutations.py Decisions/Invariants/Risks appends; suite 775)*
