# the ending protocol needs a detector — memory lag, nested repos, the unbuilt write guard — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-25

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Memory-lag detection so a session cannot silently drift from the repo | ✅ COMPLETE | 2026-07-25 | 2026-07-25 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Nested clauderized repos stop contradicting each other | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Build the write guard 1.14.0 specified and did not ship | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Close the graph drop gap and the init spawn-test carried from 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Close out and ship 1.14.1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
DETECTOR: src/clauderizer/rituals/memory_lag.py — public API: tracker_anchor(paths, gid) -> (short_sha, iso_date) | None; work_commits_since(paths, anchor) -> int (-1 = git could not answer); detect(paths, gid, target, status) -> lag dict | None; describe(lag) -> the single shared sentence. Wired at status_bundle.compute (bundle["memory_lag"]), status_bundle.render_digest ("⚠ Memory lag: " line), preflight.run (check_memory_lag, appended only when lag exists).
SUITE: 1074 -> 1085 passed, 7 skipped (+11, all in tests/test_memory_lag.py)
RED_BEFORE_GREEN_HARNESS: git clone --local --no-checkout <repo> <tmp> then checkout --detach efdf210 (an isolated CLONE, not a worktree — nothing writes the real .git, so the isolation is structural per L-29), run with PYTHONPATH=<tmp>/src. Reuse for every remaining 1.14.1 phase. Measured RED on efdf210 for Phase 0: bundle["memory_lag"]=None, "Memory lag" in digest=False, preflight memory_lag check=None, verdict "preflight PASS" — against a fixture whose tracker read NOT STARTED with a src/ commit past it. Post-fix on the same fixture: lag={'phase':'1','commits':1,'anchor':'b324de5'}, line present, check ('memory_lag','warn'), verdict "PASS WITH WARNINGS".
HISTORICAL_CHECK: The 1.14.0 drift window, measured: anchor 54290e2 "close(P4)" 2026-07-25 04:01:34 was the last tracker write, leaving phases 5 and 6 NOT STARTED; the tracker was not touched again until ef196aa 15:25:31 — 11h24m later. Non-docs commits in that window: 1 at eac1c9a (the criterion-7 commit; touches src/hosttargets.py, modernize.py, ops.py, scaffold/init.py, tests/), rising to 4 by f42f73d, and 8 total between the anchor and efdf210. tests/test_memory_lag.py::test_historical_1_14_0_drift_would_have_fired parses the phase state FROM the tracker as it stood at eac1c9a (nothing hand-fed) and asserts the detector fires.
LIVE_DOGFOOD: In-band evidence (L-07): after committing 61317f5 with this gameplan's phase 0 still reading READY, `clauderize status` on this repo emitted — ⚠ Memory lag: phase 0 "Memory-lag detection so a session cannot silently drift from the repo" still reads ready, but 1 non-docs commit landed since the tracker was last written (efdf210, 2026-07-25). The detector caught its own author.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
