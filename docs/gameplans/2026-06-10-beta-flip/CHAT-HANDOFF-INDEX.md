# Chat Handoff Index — beta-flip

> Last updated: 2026-06-10
> Status: All 3 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 260

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
| 0 | Burn-down: structural guards before the flip | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | The flip release: 0.10.0, Development Status :: 4 - Beta | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | B6 evidence: the armed guard fires green; all six gates hold | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Landed every burn-down item — the must-have and both best-efforts — before the flip, so the release artifact carries its own guards. The bare-IO tripwire (test_io_discipline.py) proved itself per L-10 in the most satisfying way available: on its very first sweep of the repo it caught three real stragglers the B2 sed pass had missed (bare write_text calls — the sed had only fixed read_text), plus one prose false positive that tightened the regex (no space before the paren). The MCP-staleness nudge closes the long-standing dogfooding sharp edge: cz_status now compares engine source mtimes against the process's import time and warns — in the digest, with the clauderize ops escape hatch named — exactly when a long-lived server is running code older than what's on disk, while fresh CLI/hook processes and installed packages never trigger it. And release-check gained the G7-between-sibling-docs tripwire: a README that exists but never names `clauderize release-check` is a staging failure, proven firing in both directions.

One same-class bonus while in there: subprocess text=True (locale decode — mojibake or outright raise on win32 for non-ASCII tool output) replaced with pinned utf-8 in preflight's runner and release-check's git wrapper. Suite 264 → 270, all green, pushed as cfe9743. Phase 1 — the flip release — is unblocked.

### Phase 1 — completed 2026-06-10

Shipped the flip: clauderizer 0.10.0 is live on PyPI carrying "Development Status :: 4 - Beta" — verified on the published artifact itself via importlib.metadata, not assumed from the source. The third consecutive zero-incident release: fresh-eyes tag sweep, staged commit with all four surfaces (version, classifier, the README maturity section renamed to "beta, with receipts" and naming the flip as gate B6, the CHANGELOG retitle), editable reinstall, byte-idempotent init, doctor exit 0 with zero open findings (the B6 precondition), push first, release-check exit 0 before any tag existed — now NINE checks, with Phase 0's README-names-the-ritual guard green on its first real staging — then tag, Release ("v0.10.0 — Beta"), the publish gate, Trusted Publishing with digital attestations, and a fresh uvx --refresh resolve. The release notes lead with what the classifier claims and link the public evidence table.

Phase 2 inherits the one assertion nothing could check until now: quickstart.yml's cache-clean guard, self-disarmed through the 0.9.0 era, arms automatically against this artifact.

### Phase 2 — completed 2026-06-10

Closed the loop on B6 with the guard that waited for it. The first quickstart dispatch, ninety seconds after publish, honestly self-disarmed — the fresh runner's index view still answered 0.9.0 (PyPI propagation lag), and the step said so instead of going red or falsely green, which is the self-arming design doing precisely its job. Once the index propagated, the armed run passed: uv cache clean followed by a pure digest against published 0.10.0 (run 27320342612) — the ephemeral-wiring fix proven in the wild on the same run that proves the install path. The local fresh-HOME walk confirmed the whole chain: fresh index resolve → 0.10.0, the durable uvx -q wiring on both surfaces, doctor exit 0, cache-clean survival via PyPI re-resolution. The classifier was verified on the published artifact's own metadata. All six beta-gate rows now carry dated artifacts.

One self-inflicted finding for the post-mortem: the PyPI-propagation Monitor I armed never fired because its grep assumed pretty-printed JSON while PyPI serves minified — L-10 (prove the probe) violated by my own monitoring probe, caught only because the timeout prompted a direct inspection. The carried residual remains G6's literal native-harness cold start; nothing else defers — all three burn-down items landed in Phase 0.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
