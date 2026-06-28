# integrity-patch — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-28

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Branch, baseline, and measure the tokenizer divergence | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Unify the canonical tokenizer | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Code coherence and small traps | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Test integrity | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs refresh to 1.3.0 | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close and 1.3.1 patch release | ✅ COMPLETE | 2026-06-28 | 2026-06-28 | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_suite: 711 passed / 4 skipped (cz_preflight 2026-06-28 on fix/integrity-patch; baseline updated 0->711). Matches the 1.3.0 union suite (PR #16).
redundancy_measurement: Over the 30 active L-NN lessons (435 pairs), redundant_pairs at threshold 0.6: FORK=0, CANONICAL(analyze._tokens)=0. Sweep thr in {0.3..0.7}: BOTH tokenizers yield 0 pairs at every threshold. Max pairwise Jaccard: FORK 0.2037, CANON 0.1892 (fork runs ~0.01-0.02 higher because retained shared stopwords inflate the intersection). Even at 0.40 (the write-time advisory threshold): CANON=0 pairs.
divergence_finding: The audit's predicted symptom ("the fork HIDES near-dupe pairs the canonical tokenizer would surface") is FALSIFIED by measurement: neither tokenizer surfaces any pair at any sane threshold, because the 30 lessons are long, detail-dense paragraphs with no lexical near-duplication over full text (max ~0.20 Jaccard). The fork-vs-canonical divergence is real in the VALUES (fork slightly higher via stopword inflation) but ZERO in reported pairs at 0.6. The genuine integrity defect is incoherence, not under-counting: TWO definitions of near-duplicate coexist (corpus_health: fork tokenizer @0.6; analyze.near_duplicate_lessons: canonical @0.40).
O-01_recalibration_direction: Recommendation for Phase 1: do NOT keep 0.6. Single-source the threshold by importing analyze._LESSON_DUP_JACCARD (0.40) into telemetry, so corpus_health/curate share ONE definition of near-duplicate with the write-time advisory (analyze.near_duplicate_lessons). Justified by data + coherence, not taste: aligning to 0.40 yields 0 false positives on the real corpus (CANON@0.40 = 0 pairs) while removing the 0.6-vs-0.40 contradiction. Honest consequence: the 30-lesson bloat is volume/conceptual overlap, NOT lexical duplication — the lexical gate correctly reports 0; consolidation will need semantic judgment by the curator, not a threshold tweak.
```

### Phase 1 Outputs

```
post_fix_corpus_health: After unifying the tokenizer + threshold: cz_corpus_health reports 30 active lessons, redundant_pairs=0 (honest 0 — same canonical analyze._tokens basis as analyze.near_duplicate_lessons + the abstract index token_set; threshold now 0.40). never_surfaced=6. Full suite 714 passed / 4 skipped (711 baseline + 3 new guard tests in test_canonical_tokenizer.py).
```

### Phase 5 Outputs

```
release_1.3.1: SHIPPED 2026-06-28. Squash-merged PR #17 to main (commit ffb3e6f); 9-cell CI green on the release commit (run 28334191426, all 3 OS × 3.11/3.12/3.13). release-check exit 0 (four registries unclaimed, origin/main==HEAD). Tag v1.3.1 on ffb3e6f (full SHA; tagged tree version 1.3.1). GitHub Release v1.3.1 "Integrity patch" (latest, non-prerelease). publish.yml OIDC success (run 28334267359). Verified: PyPI info.version=1.3.1; uvx --refresh resolves clauderizer to 1.3.1. Tool surface 42 unchanged; suite 716 passed / 5 skipped.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: The findings/phases name the redundancy metric "corpus_health._jaccard" / "corpus_health._tokens", implying a corpus_health.py module is the edit target.
**What was actually correct**: There is NO corpus_health.py module. The entire redundancy stack lives in src/clauderizer/telemetry.py: _REDUNDANCY_THRESHOLD=0.6 (line 36), the divergent _tokens fork (lines 108-110 — re.findall(r'[a-z0-9]+'), keep len>2, NO stopwords), _jaccard (113-116), and TWO identical pair-loop call sites — corpus_health() at telemetry.py:149/153 (feeds cz_corpus_health's redundant_pairs) and curate_proposals() at telemetry.py:327/331 (feeds cz_curate's consolidate proposals). lesson_health()/loop_step reach it transitively. The canonical tokenizer is analyze._tokens (analyze.py:43-48 — drops _STOP, keeps len>=4 OR has-digit).
**Why**: Phase 1's actual edit target is telemetry.py (replace the local _tokens with the canonical analyze._tokens at both sites and recalibrate the threshold), not a non-existent corpus_health.py — verified by grep across src/ (the cz_corpus_health op in ops.py:863 calls telemetry.corpus_health). Without this the executing session hunts a phantom module.
