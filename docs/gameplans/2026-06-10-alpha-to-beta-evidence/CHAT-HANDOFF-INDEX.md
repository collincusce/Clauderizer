# Chat Handoff Index — alpha-to-beta-evidence

> Last updated: 2026-06-10
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 255

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
| 0 | Beta gates on the record; ship 0.9.0 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CI proves the OS matrix; win32 leg executed for real | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | G6: native-leg cold-start evidence | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Foreign-repo live loop: node profile end-to-end | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Beta-evidence consolidation; scope gameplans B and C | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Shipped 0.9.0 — the harness-truth backlog (shape-C wiring, D-010 consumer-leg probes, release-check, RELEASING.md, [memory] config) is now public — and put the beta gates on the record: D-012's B1–B6 written into docs/RELEASING.md beside the 1.0 gates, with the evidence table Phase 4 will complete. The ritual ran exactly as written and boring on purpose: push the backlog first, stage (three version surfaces + editable reinstall + CHANGELOG retitle), doctor exit 0 with the executor-leg probe already claiming identity clauderizer 0.9.0, release-check exit 0 before any tag existed (all four registries swept fresh and unclaimed), tag the pushed commit, cut the Release, watch the tag==source gate pass — its first green passage on a legitimate release — and verify fresh resolution via uvx --refresh. Zero incidents, against two prior releases (0.7.0, 0.8.0) that each had same-day incidents; the machinery built to prevent those shapes was load-bearing, not decorative.

B1 is satisfied with dated artifacts (staged commit bdac36b, publish run 27311516131, the Release URL, the fresh-resolve output). One forward-looking catch for Phase 1: the publish run's annotations warn that checkout@v4 / upload-artifact@v4 / setup-uv@v5 run on deprecated Node 20 (forced to Node 24 from 2026-06-16) — the test.yml rework should bump action versions while it is in there.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
