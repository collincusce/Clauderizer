# Chat Handoff Index — abstract-index-fast-retrieval

> Last updated: 2026-06-25
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 626

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
| 0 | Branch, baseline &amp; cost-harness (fixture-first) | ✅ COMPLETE | 2026-06-25 | 2026-06-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Abstract index builder (data structure, dual parser, invalidation) | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Addressable fetch (cz_get) and abstract surfacing on cz_analyze | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Cost experiment and gain-gate verdict (KEEP/DISCARD) | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Realize the win in injected surfaces (handoff/status) and re-measure | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Write-time lesson-synthesis advisory (own fixture, own mini gain-gate) | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Upgrade path (init/reindex build, doctor detect) and dogfood on an isolated repo copy | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Release readiness: CI 9-cell, docs sweep, cross-platform, merge-ready | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-25

Stood up the experiment spine fixture-first, before any feature code. Captured the green baseline (626 -> 632 after adding the cost-harness self-tests). Built tests/benchmarks/cost.py: a deterministic token-cost harness (payload via metrics.token_estimate len//4, plus answer-accuracy and round-trips) modeling baseline (load every surfaced body, no addressable getter) vs candidate (compact abstracts + one cz_get per needed body). Pre-registered the KEEP gate in _experiments/PRE-REGISTRATION.md and froze it as cost.py constants (MIN_SAVING=0.30, accuracy non-regression, MAX_ROUND_TRIPS=2). Proved the harness DISCRIMINATES before the feature exists (L-40): on the synthetic 1-of-5 fixture the real mechanism saves 51.3% (KEEP), a no-op control saves 0.0% (DISCARD), and an accuracy trap that saves 69.5% by dropping the answer is vetoed by the accuracy guard (DISCARD) — gap 51.3pp, locked in CI by test_cost.py (6 tests).

A prerequisite blocker was found and fixed first: the dogfood preflight test command was bare `pytest`, not on the MCP server subprocess PATH (exit 127), so no baseline could be captured even though the suite was green via the venv; repointed to `.venv/bin/python -m pytest` (PATH-independent). Commits: c4386b2 (plan), e200f7b (preflight fix), 530b65d (harness). Next: Phase 1 builds the real abstract-index module (dual parser, mtime+hash+schema-version invalidation) — no consumer yet.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

### Category: Integration

**1.** A dogfood self-check that shells out (preflight's test command) must not depend on the ambient PATH. The MCP server spawns the test command WITHOUT an activated venv, so bare `pytest` exits 127 and preflight cannot capture a baseline even though the suite is green via `.venv/bin/python -m pytest`. Point profile.lock.toml's test command at the venv interpreter explicitly so preflight is robust across launch contexts. Note the shipped python profile template (src/clauderizer/profiles/python.toml) ships `test = "pytest -q"`, carrying the same latent fragility for any MCP-only python host — a candidate engine fix (prefer `python -m pytest`, or venv-detect). Sibling of L-23: the author's environment never exercises the real surface. *(evidence: .clauderizer/profile.lock.toml (e200f7b); cz_preflight exit 127 -> green 632 after the fix; src/clauderizer/profiles/python.toml:8)*
