# headroom-borrowed-ideas — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-19

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Baseline & methodology | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Idea 1 — Prefix-stability (CacheAligner analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Idea 2 — Relevance-ranked handoff (IntelligentContext analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Idea 3 — Failure-miner (headroom learn analog) | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Consolidate survivors & close | ✅ COMPLETE | 2026-06-19 | 2026-06-19 | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests: 305 passing (green) on branch 2026-06-19-headroom-borrowed-ideas; pre-flight refreshed stale digest figure 300→305. clean_tree fail is benign (uncommitted gameplan scaffold + active-gameplan pointer in config.toml).
```

### Phase 1 Outputs

```
prefix_stability_measured: Digest current-order common-prefix=65 chars (7.3%, ~16 tok); stable-first reorder=786 chars (78.9%, ~196 tok); but full digest is only ~888 chars (~222 tok). Handoff phase1-vs-phase3 common-prefix=43 chars (different phases share almost nothing by design; same-phase handoffs are byte-identical = already fully cached). Harness: docs/gameplans/2026-06-19-headroom-borrowed-ideas/_experiments/measure_prefix.py
```

### Phase 2 Outputs

```
tests_after_idea2: 312 passed, 4 skipped (was 305 baseline; +7 new in tests/test_handoff_relevance.py). Idea #2a covered: pointer surfaces most-relevant-first, two phases reorder differently, ALL lessons survive (count-in==count-out), obsolete excluded from pool, pointer absent when <=k or no query, and assemble inserts the pointer + keeps all 6 lessons via the real assembler.
```

### Phase 3 Outputs

```
miner_precision: 62 proposals across 10/11 real transcripts after deny-list tuning (~6/session; 50 tool-fix, 12 test-fix, 0 user-correction). Dogfood on THIS session: 2/2 true positives (gh-not-found→curl fix; git UNC-path→wsl.exe fix), 0 false positives. Labeled sample (20 proposals, 2 real dev sessions): ~16 genuine failure→fix worth a glance → ~80% precision. Rediscovers real adopted lessons (H-08 wsl.exe shim exit-127, git dubious-ownership, uvx/env, multiple pytest fail→pass). Detector C (user corrections): 0 recall on this corpus (high precision, few strongly-cued corrections). Harness: _experiments/run_miner.py.
tests_after_idea3: 320 passed, 4 skipped (305 baseline + 7 idea#2 + 8 idea#3). New: tests/test_failure_miner.py covers tool-error→fix, test fail→pass, user-correction, noise exclusion, benign-search-error exclusion, no-fix→no-proposal, long-prose-not-a-correction, and propose-only drafts.
```

### Phase 4 Outputs

```
final_tests: 345 passed, 4 skipped (305 baseline + 7 idea#2 + 8 idea#3 + 2 op tests + 17 C-01 robustness + 6 C-02 post-verification hardening). Registry/tool-name parity holds; 31 tools. subsys.rituals 0.7.0, subsys.mcp-server 0.5.0. (Prior figure 322 predated C-01's +17 and C-02's +6.)
```

## Corrections Log

### C-01 — Phase 3

**Phase**: 3
**What gameplan said**: O-03 resolved: the failure-miner degrades gracefully on unrecognized record shapes / transcript schema drift.
**What was actually correct**: Post-close diverse/adversarial testing found two robustness gaps in learn._iter_records: (1) a valid-JSON-but-non-dict line (42, "x", [1,2], null) crashed with AttributeError when mine() called .get on it; (2) a leading UTF-8 BOM made the first line's json.loads fail, silently dropping the first record. Fixed by opening utf-8-sig and yielding only dict records; added tests/test_diverse_robustness.py (17 tests). Suite 322→339 passed.
**Why**: O-03's resolution was verified only against garbled/partial lines, not against valid-JSON-non-object lines, BOM, or CRLF — the graceful-degradation claim outran the input diversity it was actually tested against.
**Lesson**: A 'degrades gracefully' claim is only as strong as the input diversity it was tested against: exercise non-dict valid JSON, BOM/CRLF, unicode, and empty input before resolving a schema-tolerance item. Adversarial input tests belong in the same phase that makes the robustness claim.

### C-02 — Phase 3

**Phase**: 3
**What gameplan said**: O-03 resolved and C-01 hardened learn._iter_records (non-dict valid-JSON lines, BOM); the failure-miner is claimed to degrade gracefully on transcript schema drift and to mine at ~80% precision (precision-over-recall).
**What was actually correct**: A second, independent post-close adversarial pass (this verification session) found C-01 had closed only the parse-step gaps; three crash vectors still escaped through cz_mine_failures on real-transcript shapes: (1) non-UTF-8 bytes -> UnicodeDecodeError, a ValueError that slipped mine_dir's OSError-only net (decode happens during iteration, OUTSIDE the json.loads try); (2) an unhashable tool_use_id (list/dict) used as a dict key -> TypeError; (3) a non-str `text` in a content list, str-joined -> TypeError. Plus one precision miss: `\d+ failed` flagged a clean "0 failed"/"305 passed, 0 failed" run as a failure (3 false positives on the real corpus). All four fixed at the source (open(..., errors="replace"); isinstance guards on tool_use_id and text; [1-9]\d* failure-count grammar) plus a per-file `except Exception` net in mine_dir. 6 regression tests added. Suite 339->345 passed, 4 skipped; real-corpus proposals 68->65; read-only + determinism re-proven on the real corpus; 5000-trial property harness on idea #2a zero-drop passed 0 fails.
**Why**: C-01 and O-03 were verified against garbled/partial lines and BOM/CRLF, but not against non-UTF-8 bytes or valid-JSON-but-hostile-shape records, and the precision bar was measured without a "clean 0-failed run" negative case. Schema-drift tolerance has to extend past JSON validity to shape validity, and the file-decode boundary sits outside the json.loads try/except.
