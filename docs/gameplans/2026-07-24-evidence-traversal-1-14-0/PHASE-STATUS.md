# evidence traversal 1.14.0 — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Single-source the status parser and expose defaulted status | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | One atomic symlink-refusing write path for tracked markdown | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Well-formedness at the write boundary | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Implement D-063 so the curator stops proposing from absent evidence | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-3-HANDOFF.md |
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

### Phase 1 Outputs

```
WRITE_PATH: writer.write_atomic is the single byte-write: refuse_if_symlink -> sibling temp (never mkstemp, whose 0600 would re-permission every tracked doc) -> mode preserved -> os.replace with a bounded Windows retry -> unlink in finally. 4 bypassing sites rerouted: handoff.py:566, cascade.py:171, cascade.py:225, index.py:68. NO revision bump inside write_atomic — the callers already bump (corrects all three planning drafts).
TRUNCATION_PROOF: RLIMIT_FSIZE probe: a failed write on a populated DECISIONS.md leaves it sha256-identical. Pre-fix the same probe destroyed 92,027 -> 38,334 bytes. Planted-symlink probes: cz_write_handoff and the cascade report path both refuse instead of writing outside the repo. 7 of 10 tests red pre-fix.
EARLY_WARNING_CHECK: git diff pre-1.14.0-writepath -- docs/ after Phase 1: 9 files, 750 insertions, ALL intended gameplan artifacts. No unintended mutation of canonical memory. No *.tmp-* residue.
WINDOWS_HELD_HANDLE_TEST: test_replace_survives_a_second_open_handle_on_windows: opens a second read handle on the target, then write_atomic must still land via the bounded retry and leave no tmp residue. Skipped on POSIX by design — O-01's resolution is the windows-latest matrix cells, which is the one Phase 1 behavior no Linux cell can observe.
```

### Phase 3 Outputs

```
CORPUS_WIPE_CLOSED: live repo 6 obsolete proposals -> 0. Fresh clone 25 of 25 -> 0, 25 active lessons still standing. Standing loop no longer drives the corpus to zero. loop_step now says CONVERGED (no telemetry — nothing measured, not nothing to do) instead of a false all-clear.
TESTS_RETARGETED: test_curator.py::test_obsolete_never_surfaced_and_low_utility pinned the pre-decision behavior; retargeted to assert the DECIDED contract (never-surfaced alone does not propose; the evidence-backed low-utility arm still does) and renamed. test_rituals memory-gauge assertion accepts either wording since the instruction half is telemetry-gated. The two the plan named as must-pass-unmodified both did.
FRESH_CLONE_CI_LEG: test.yml gains a fresh-clone job: asserts telemetry.jsonl is NOT tracked, then that cz_curate proposes zero obsoletions, cz_loop_step reports has_telemetry false with the honest summary, and the corpus is intact. This is the only place that shape is exercised — the in-process suite always has the author's repo.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
