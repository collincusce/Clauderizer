# Chat Handoff Index — Empirical self-improvement loop - telemetry-gated curator and loop-gameplan primitive

> Last updated: 2026-06-21
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 548

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
| 0 | Telemetry substrate & baseline | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Utility & failure-risk scoring (advisory) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The Curator - propose-confirm maintenance pass | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Empirical-gated promotion & typed-edge risk surfacing | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | The loop-gameplan primitive | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, dogfood & ship | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-21

Phase 0 shipped the telemetry keystone: a deterministic, append-only memory-telemetry log (.clauderizer/telemetry.jsonl) plus the read-only cz_corpus_health surface, wired into the two blessed writes that already exist - cz_write_handoff logs which lessons/invariants a handoff surfaced; cz_transition_phase logs each phase's outcome + exit-criteria checked/total. This closes the one verified gap (no persisted empirical signal) that made Phase 1 scoring and the Phase 2 curator impossible. Constitution-clean: stdlib-only/no-ML (D-018), append-only (INVARIANT-03), advisory read-only surface (INVARIANT-05), never written from a hook (INVARIANT-06). Baseline captured pre-loop: 20 active lessons, 0 redundant, 20 never-surfaced, 0 events. Suite 548 -> 554 green (+6 tests, exit 0). Next: Phase 1 turns this signal into per-lesson utility/failure-risk scoring.

### Phase 1 — completed 2026-06-21

Phase 1 turned raw telemetry into per-lesson empirical health via the read-only cz_lesson_health op (tool surface 32->33). utility = fraction of a lesson's RESOLVED surfacings that preceded a passing phase (join key (gameplan,phase) across surfaced+outcome events); plus failure_risk, surfaced/resolved counts, last_surfaced recency, and an advisory signal (never-surfaced | low-utility-review | promotion-candidate) - INVARIANT-05: it surfaces candidates, the agent (and Phase 2's curator) decides. Validated by a deterministic labeled-sample held-out-judgment eval: good lesson 1.0+promote, bad 0.0+review, unused never-surfaced; window-recency confirmed. Deterministic, stdlib-only (D-018), no writes. Suite 554 -> 559 passing (+5 tests), green.

### Phase 2 — completed 2026-06-21

Phase 2 shipped the Curator: cz_curate (read-only, tool surface 33->34) PROPOSES a corpus-maintenance batch from telemetry-derived health, exactly like cz_mine_failures - it never writes. Four action kinds, each with evidence and the blessed cz_* op to apply it: consolidate (lexically redundant project-lesson pair -> obsolete the dup into the higher-utility kept lesson), obsolete (never-surfaced, or utility<=0.2 over >=2 resolved surfacings), flag (0.2<utility<=0.5, review-only), promote (high-utility gameplan lesson -> L-NN). This is SkillOps-style library-time maintenance realized the Clauderizer way: propose-confirm, the agent decides (INVARIANT-05). Validated by an A/B - applying the proposals via cz_obsolete_lesson drops redundant_pairs 1->0 and shrinks the active set while the kept lesson still surfaces for its topic (recall@k preserved). Resolves O-02 (nothing auto-applies). Deterministic, no ML (D-018). Suite 559->565 passing green.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
