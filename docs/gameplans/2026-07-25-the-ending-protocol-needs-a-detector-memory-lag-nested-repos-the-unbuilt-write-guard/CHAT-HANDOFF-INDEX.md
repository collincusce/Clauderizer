# Chat Handoff Index — the ending protocol needs a detector — memory lag, nested repos, the unbuilt write guard

> Last updated: 2026-07-25
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1074

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
| 0 | Memory-lag detection so a session cannot silently drift from the repo | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Nested clauderized repos stop contradicting each other | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Build the write guard 1.14.0 specified and did not ship | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Close the graph drop gap and the init spawn-test carried from 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Close out and ship 1.14.1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-25

Built the detector the ending protocol never had (H-22, D-069). `rituals/memory_lag.py` answers one question — does the tracker still describe the repo? — and it answers it from git rather than from the tracker asserting itself (D-065). The anchor is the last commit that TOUCHED the phase tracker, which is "the last recorded state change" read as evidence instead of trusted as a date someone typed into a cell; work is commits past that anchor touching anything outside the docs tree and `.clauderizer/`; lag is work landing while the tracker still reads the phase unstarted. It surfaces as a conditionally-emitted `⚠ Memory lag:` digest line naming the phase and the commit count, and as a `cz_preflight` **warn** carrying the identical sentence from `memory_lag.describe` — one claim, one wording, two surfaces, pinned by a test (L-55). Advisory throughout: it never fails pre-flight and never blocks a transition (INVARIANT-05), it is read-only and swallows exceptions so a hook can call it (INVARIANT-06), and it emits zero bytes when memory is current, which the existing golden digest gate plus a new git-present-vs-git-absent byte-identity test both hold (INVARIANT-08). No config key, no persisted flag.

The scope gate is the design decision worth flagging forward: the detector fires only when the tracker claims a phase has NOT begun. An in_progress phase is supposed to accumulate commits, so firing there would have made it noise, and noise gets ignored — but the honest cost is that a phase left marked in_progress long after it was truly finished is not detected, because git cannot tell "still working" from "done but unrecorded". That limit is written into the module docstring and the H-22 resolution rather than papered over. Evidence: 11 tests, suite 1074 → 1085. RED was demonstrated substantively, not just by ImportError — a probe built the lagging fixture and ran it against the pre-1.14.1 engine at efdf210, which reported a clean `preflight PASS` and no line at all while a `src/` commit sat past a NOT STARTED phase. The historical test replays this repo's own `eac1c9a`, parsing the phase state from the tracker as it stood at that commit, and asserts the detector fires on the failure that motivated it. Then it caught its own author: with phase 0 still reading READY after commit 61317f5, `clauderize status` named it.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**1.** A drift detector earns its line in the digest by being QUIET, and quiet comes from gating on the state that asserts nothing-has-happened — not from tuning a threshold. Memory-lag fires only where the tracker claims a phase has not begun; gating instead on "in_progress phase with N commits" would fire on every normal working session, and a detector that cries wolf is worth less than none. Two corollaries. (1) Anchor the claim to the artifact's own git history — the last commit that TOUCHED the tracker — never to a date cell the writer typed, so the signal is evidence read rather than the tracker vouching for itself (D-065); this also makes "the same repo with the state recorded produces nothing" fall out for free, because recording it moves the anchor. (2) State the scope limit in the module docstring and the finding resolution instead of widening the claim to cover it: git cannot distinguish "still working" from "done but unrecorded", so a stale in_progress phase is undetectable, and saying so is stronger than a fuzzy staleness score that pretends otherwise. *(evidence: Phase 0, commit 61317f5: src/clauderizer/rituals/memory_lag.py UNSTARTED_STATES gate; tests/test_memory_lag.py::test_silent_for_an_in_progress_phase pins the quiet case, ::test_silent_once_the_tracker_records_the_work pins the anchor-moves case; H-22 resolution records the limit)*

### Category: Testing

**2.** "Demonstrated RED on the pre-fix tree" is satisfied by an ImportError only in the letter. A new module means the new test file cannot even collect on the old tree, which proves the module is absent — not that the BEHAVIOR was absent, which is the thing the criterion is actually about. Build the red demonstration as a standalone probe that uses ONLY APIs present on both trees, drives the same fixture the tests build, and prints the old engine's actual answer. Here that turned a collection error into the real finding: the pre-1.14.1 engine reported `preflight PASS` and a digest with no lag line, against a repo whose tracker read NOT STARTED with a src/ commit sitting past it — the 1.14.0 failure reproduced on demand, in the old engine's own words. Run the same probe post-fix and the two outputs are the before/after the phase summary needs. Prefer `git clone --local --no-checkout` + `checkout --detach` over `git worktree add` for the isolated old tree: a clone writes nothing into the real repo's .git, so the isolation is structural rather than promised (L-29). *(evidence: Phase 0: scratchpad red_probe.py run under PYTHONPATH=<clone>/src at efdf210 vs the working tree; recorded in output RED_BEFORE_GREEN_HARNESS)*
