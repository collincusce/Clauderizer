# Chat Handoff Index — stranger-readiness

> Last updated: 2026-06-10
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 257

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
| 0 | The stranger's first hour: quickstart truth, live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Upgrade and uninstall stories, walked live | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Trust model on the record (TRUST.md + SECURITY.md) | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Troubleshooting runbook from the scar tissue | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | README positioning pass + B5 consolidation | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Walked the stranger's first hour in a fresh-HOME simulation (D1's local vehicle) and fixed everything it hit. The published quickstart command was broken outright — `uvx clauderize init` resolves no such package — and the walk found three defects deeper than the spelling: a bare `clauderize doctor` that doesn't exist on a uvx-only PATH; init under uvx wiring the ephemeral uv-cache path into .mcp.json and the hook wrapper, so `uv cache clean` killed the MCP wiring and replaced every digest with an engine-unreachable breadcrumb until re-init; and cold-cache uv progress noise riding the wrapper's stderr-rerouting (L-07) straight into session context, in front of the --version identity line the probes parse. Fixes: the README's four occurrences plus pyproject's comment now carry `uvx --from clauderizer clauderize init` (with a zero-install note covering every bare `clauderize` in the docs); `_under_uv_cache()` makes invocation resolution refuse cache-resident bindir AND which() results, wiring the durable absolutized `uvx -q --from clauderizer` form instead — proven live pre-release by running init via a locally built wheel: the wiring came out durable and the digest returned PURE after `uv cache clean`, self-healing by re-resolution. Suite 261 → 264 (three resolution tests).

The walk is now a permanent guard: .github/workflows/quickstart.yml runs the README's exact install path against the PUBLISHED package on a clean runner (push + weekly cron + dispatch), with a doc-drift grep tying CI to the documented command and a SELF-ARMING cache-clean assertion — it explains itself on 0.9.0 (which predates the fix) and hard-asserts from the next release. First quickstart run green (27316260960); the 9-cell matrix green on the same commit (27316260956, third consecutive all-green today). Known state recorded: published 0.9.0 still wires ephemerally; the fix ships with GP-C's flip release, and doctor catches the 0.9.0 failure shape as drift meanwhile.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Distribution claims need distribution execution: the author's repo never exercises the published install path (an editable venv is not `uvx --from PyPI`), so the front door was broken in four documented places — and the wiring it produced died on a cache clean — while every test passed. Walk the published artifact from a fresh environment, fix what it hits at the right layer, then pin the walk as a CI job that executes the doc's exact text (doc-drift grep included), with assertions that self-arm when unreleased fixes ship.
