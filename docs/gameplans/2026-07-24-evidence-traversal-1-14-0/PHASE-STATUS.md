# evidence traversal 1.14.0 — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Single-source the status parser and expose defaulted status | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | One atomic symlink-refusing write path for tracked markdown | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Well-formedness at the write boundary | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Implement D-063 so the curator stops proposing from absent evidence | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Resolve H-20 with capability-not-presence engine identity | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Preserve foreign config and converge existing installs | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Restore full lesson propagation, close H-19, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
FINDINGS_REGISTER_BEFORE_AFTER: before: cz_list_findings returned 21 findings, ALL status "active", ALL date null. after: 17 resolved / 4 open (H-16, H-19, H-20, H-21), every date populated, 21/21 status_source="parsed", 0 defaulted. NOTE the plan said "20 findings, 3 open" — it is 21 and 4 because H-21 was recorded after the plan was written.
PARSE_RECONCILIATION_BASELINE: HARDENING 21 entries / 21 parsed / 0 defaulted (strict — the error oracle). DECISIONS 68 / 41 parsed / 27 defaulted (exactly D-001..D-027, the founding entries predicted by O-04). INVARIANTS 9 / 0 parsed / 9 defaulted (by design). ok=true, zero false positives on the non-strict registers — this is INVARIANT-10's ratification gate for Phase 6.
RED_BEFORE_GREEN_HARNESS: git worktree --detach at tag pre-1.14.0-writepath, run with PYTHONPATH=&lt;wt&gt;/src. Results: test_canonical_parsers 5/5 RED pre-fix, 5/5 green. test_render_roundtrip 7/9 RED pre-fix (the decisive failure is substantive, "assert 'active' == 'open'", not a missing key); the 2 that pass pre-fix are lesson and correction, which never depended on the status parser. Reuse this harness for every remaining phase's standing oracle.
SUITE: 1002 -> 1016 passed, 5 skipped (+14: 5 canonical-parser, 9 round-trip)
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
