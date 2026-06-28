# integrity-patch — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-28

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Branch, baseline, and measure the tokenizer divergence | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |
| 1 | Unify the canonical tokenizer | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Code coherence and small traps | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Test integrity | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs refresh to 1.3.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close and 1.3.1 patch release | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

_(Concrete values produced by completed phases that later phases need.)_

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: The findings/phases name the redundancy metric "corpus_health._jaccard" / "corpus_health._tokens", implying a corpus_health.py module is the edit target.
**What was actually correct**: There is NO corpus_health.py module. The entire redundancy stack lives in src/clauderizer/telemetry.py: _REDUNDANCY_THRESHOLD=0.6 (line 36), the divergent _tokens fork (lines 108-110 — re.findall(r'[a-z0-9]+'), keep len>2, NO stopwords), _jaccard (113-116), and TWO identical pair-loop call sites — corpus_health() at telemetry.py:149/153 (feeds cz_corpus_health's redundant_pairs) and curate_proposals() at telemetry.py:327/331 (feeds cz_curate's consolidate proposals). lesson_health()/loop_step reach it transitively. The canonical tokenizer is analyze._tokens (analyze.py:43-48 — drops _STOP, keeps len>=4 OR has-digit).
**Why**: Phase 1's actual edit target is telemetry.py (replace the local _tokens with the canonical analyze._tokens at both sites and recalibrate the threshold), not a non-existent corpus_health.py — verified by grep across src/ (the cz_corpus_health op in ops.py:863 calls telemetry.corpus_health). Without this the executing session hunts a phantom module.
