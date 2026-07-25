# Chat Handoff Index — clear the findings backlog to zero and give the register a detector

> Last updated: 2026-07-25
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1164

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
| 0 | Engine identity — the digest says when it is not the build the working tree describes | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Planning surfaces the lessons that govern planning (H-25) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | The digest nudges on the cost it names, and the register stops being write-only (H-26 + the aging detector) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Two core-path lows: a symlinked parent directory, and a gameplan that cannot be closed (H-16 + H-21) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Subsystem docs get an executable seam against their module (H-24) | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close out and ship 1.14.2 with the backlog at zero | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-25

Closed the finding that made every other 'verified live' claim through MCP unfalsifiable. engine_identity.serving_build compares the running module's import location and version against the repo's src/clauderizer, which the process already has in hand -- no spawn, no handshake, so it stays read-only and hook-safe. That is deliberately a DIFFERENT question from H-20's doctor probe: doctor asks whether some other registered command is launchable and must spawn it; this asks whether the process executing right now is the build the tree describes, and a process can simply look.

Two design points earned their keep. The PATH is the disambiguator, not the version: during 1.14.1's development the served build and the tree both reported 1.14.1 while being different builds, so a version-only check would have called the exact failure healthy -- pinned by a test. And the detector is silent in both ordinary cases, a consumer repo with no engine source and a process already running the tree, which keeps INVARIANT-08 byte-identity and was verified live at zero warning lines against this repo. The RED was behavioral per the tightened standing oracle: on the pre-1.14.2 tree the bundle key is None and the digest line absent, while engine_source_newer_than returns False on BOTH trees -- that last one is pinned as its own test, because the tempting wrong fix is to tighten the mtime check, and mtimes cannot see this by construction for an installed package. Suite 1164 -> 1177. The same deployment gap as H-23 applies and is recorded rather than glossed: this reaches the MCP surface only when 1.14.2 publishes.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** When a component can answer a question about ITSELF, do not build a probe to ask it from outside. Doctor verifies another command by spawning it and completing a handshake, which is right because that command is a different process -- and the reflexive version of the same question needs none of that: a process already knows where its own module was imported from and what version it carries, and the source it should be running is on disk beside it. The self-check is therefore cheap, synchronous, exception-free and safe inside a hook, where a spawn probe would be none of those. Corollary that decided the design here: compare the PATH, not just the version. The failure being fixed had both sides reporting the same version string while being different builds, so a version-only check would have certified the exact situation as healthy. *(evidence: Phase 0 of the 1.14.2 backlog gameplan: engine_identity.serving_build vs the H-20 doctor handshake; tests/test_serving_build_identity.py::test_it_fires_even_when_the_versions_agree)*
