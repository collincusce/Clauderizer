# Chat Handoff Index — integrity-patch

> Last updated: 2026-06-28
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 711

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
| 0 | Branch, baseline, and measure the tokenizer divergence | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Unify the canonical tokenizer | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Code coherence and small traps | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Test integrity | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs refresh to 1.3.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close and 1.3.1 patch release | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-28

Established the baseline and measured the tokenizer divergence fixture-first (L-39/L-40). Baseline suite = 711 passed / 4 skipped (cz_preflight, recorded as output baseline_suite). A throwaway measurement script imported the real lesson parser + both tokenizers and computed redundant pairs over the 30 active L-NN lessons (435 pairs) at thresholds 0.3–0.7. Result: FORK and CANONICAL(analyze._tokens) both report 0 redundant pairs at EVERY threshold; max pairwise Jaccard is 0.2037 (fork) / 0.1892 (canonical). The audit's predicted symptom ("the fork hides near-dupe pairs the canonical tokenizer would surface") is FALSIFIED — the 30 lessons have no lexical near-duplication over full text. The genuine defect is incoherence: TWO definitions of "near-duplicate lesson" coexist — corpus_health (fork tokenizer @0.6) vs analyze.near_duplicate_lessons (canonical @0.40). O-01 recalibration redirected accordingly (A-001): Phase 1 single-sources both the tokenizer (analyze._tokens) AND the threshold (analyze._LESSON_DUP_JACCARD = 0.40); aligning to 0.40 costs 0 false positives on the real corpus. The script was deleted; tree clean.

### Phase 1 — completed 2026-06-28

Resolved the keystone finding (D-041). Deleted the divergent local telemetry._tokens and replaced it with `from .analyze import _tokens` (import identity), so corpus_health / curate_proposals tokenize through the single canonical tokenizer shared by analyze.rank_relevant, analyze.near_duplicate_lessons, and the abstract index token_set. Recalibrated the redundancy threshold by data (O-01 → D3): `_REDUNDANCY_THRESHOLD = analyze._LESSON_DUP_JACCARD` (0.40), single-sourcing it with the write-time advisory rather than keeping the incoherent 0.6. Added tests/test_canonical_tokenizer.py (3 guards: exactly one `def _tokens` in src/, telemetry._tokens is analyze._tokens, threshold == analyze._LESSON_DUP_JACCARD) so a third fork cannot reappear — the enforcement that makes D-041 machine-checked and O-04 viable. Post-fix cz_corpus_health honestly reports 0 redundant pairs over the live 30-lesson corpus (the bloat is volume/conceptual, not lexical). Full suite 714 passed / 4 skipped (711 + 3 guards). No circular import (analyze does not import telemetry). No user-facing behavior change beyond the advisory redundancy basis (D2).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
