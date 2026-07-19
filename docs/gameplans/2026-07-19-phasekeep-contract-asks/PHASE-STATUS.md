# phasekeep-contract-asks — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-19

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Contract Surface | ✅ COMPLETE | 2026-07-19 | 2026-07-19 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Release and Verify | ✅ COMPLETE | 2026-07-19 | 2026-07-19 | handoffs/PHASE-1-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
SUITE: 943 passed, 5 skipped (36 new: test_contract_surface.py, test_listing_ops.py, test_marker_recovery.py)
CONTRACT_COMMIT: 39a0693 (13 new registry ops; contract schema 1.0; revision.json; assignment shape; marker losslessness)
```

### Phase 1 Outputs

```
RELEASE: v1.12.0: release-check exit 0 pre-tag; tag pushed; GitHub Release cut; Publish to PyPI run 29682146599 success (Trusted Publishing); uvx --from clauderizer==1.12.0 reports 1.12.0
WRITE_THEN_READ: scratch repo via released engine: revision 2 -> 3 (add_open_item) -> 4 (assign); schema_version 1.0 on status/ops results; 62 ops in --list --json
POLL_BENCHMARK: 10 projects @1s for 60s (Node poller reading revision.json, PhaseKeep scripts/bench-revision-poll.js): CPU 0.24% of one core (target <2%), p50 0.81ms, p95 1.23ms, p99 1.82ms, max 3.65ms (target p95 <50ms native). wsl.exe-interop leg deferred to the first Windows-side consumer with reason: the artifact read is a UNC file read, no per-poll process spawn, and cannot be measured from inside WSL
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
