# Standing curator loop - memory maintenance — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-28

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Iterate | ✅ COMPLETE | 2026-07-28 | 2026-07-28 | handoffs/PHASE-0-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
tokens_before: 6884 (project_lesson_tokens, cz_status 2026-07-28 pre-iteration)
tokens_after: 6913 (+29: synthesis body 1142 chars vs union 1206, but evidence+provenance tails outweighed the margin; handoff_est_tokens fell 6035->5988)
entries_before: 21 active project lessons (never_surfaced 3: L-11, L-24, L-52)
entries_after: 20 active (clears the digest's >20 breach; never_surfaced 2: L-11 kept with cause, L-69 trivially new)
actions_taken: Consolidated L-24+L-52 -> L-69 under L-67 coverage gate (pre 2/2 rank-1 simulated, post 2/2 rank-1 live, k=5, rarest-token queries; add-time Jaccard 0.505 vs L-24); obsoleted L-24, L-52. Kept L-11 (its zero is the H-25 wiring gap per ops.py cz_create_gameplan comment, not lesson evidence). Kept L-63 out of the cluster: gate ran 2/3 (empty top-5 on L-63's query) and telemetry shows it young+active. Declined 3 cz_curate promote proposals (alpha gameplan lessons 1-3): promotion adds project entries/tokens against this loop's directive and writes files of a gameplan other fleet workers hold. Dropped candidate merges L-07+L-25 (co-surfaced only 4/24 events) and L-53+L-56 (0 co-surfacings, no tool signal). Corpus judged at consolidation floor; further reduction needs an engine lever (rendered evidence/provenance tails, handoff rendering policy).
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
