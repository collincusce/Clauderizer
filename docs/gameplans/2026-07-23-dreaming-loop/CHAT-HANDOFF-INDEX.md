# Chat Handoff Index — dreaming-loop

> Last updated: 2026-07-24
> Status: Phase 1 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 948

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
| 0 | Dream journal substrate & the blessed dream write | ✅ COMPLETE | 2026-07-24 | 2026-07-24 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Capture ritual & read-only nudges | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | cz_dream — ripeness-gated dream assembly | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Durable dream proposals & unified triage | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | The dreaming ritual: skill, loop integration & headless recipe | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Dogfood, eval & ship 1.13.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-24

Landed the dream-journal substrate exactly on the telemetry pattern: new src/clauderizer/dreams.py reuses telemetry's sorted-key JSONL appender and torn-line-tolerant reader against a new paths.dreams_file (.clauderizer/dreams.jsonl, gitignored here and ensured by init in target repos — which also closed the pre-existing gap where init never gitignored telemetry.jsonl). The blessed write is mutations.add_dream (@_locked, so the dedupe read and append are one read-modify-write under H-05) surfaced as cz_add_dream (writes=True, centrally stamped, TOOL_NAMES parity kept); gameplan/phase default to the active gameplan's in-progress phase so capture is a two-argument call. Validation is reject-before-append per INVARIANT-03: closed kind vocabulary (friction/gap/surprise/correction/drift/win), 600-char/4-sentence/8-ref caps, and a conservative PII deny-list (emails, known secret-token shapes, absolute home paths — repo-relative paths pass). Duplicate content (whitespace-collapsed, keyed by gameplan+phase+kind+note) is a safe no-op; the same note in a later phase is deliberately new signal.

Evidence: 20 new tests in tests/test_dreams.py (round-trip byte-determinism, all reject classes, dedupe both ways, revision non-bump, registry/lock discipline, init gitignoring, contract key-set pin — the criterion's "corpus payload" is pinned engine-side in test_op_result_carries_schema_version_and_contract_keys; the external PhaseKeep corpus regenerates at the 1.13.0 release per its own capture script). Full suite exit 0 at 973 collected vs 953 pre-phase. Dogfooding started immediately: the first two real notes were captured through the headless clauderize-ops path with defaults resolving correctly (ids in Outputs Registry). Doctor's exit-3 is pre-existing environment noise (kimi-desktop pin serves another repo at 1.11.0), unrelated to this phase.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
