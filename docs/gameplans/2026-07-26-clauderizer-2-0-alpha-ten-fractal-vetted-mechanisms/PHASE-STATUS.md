# clauderizer 2.0 alpha — ten fractal-vetted mechanisms — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-28

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Honest endings and epistemics | ✅ COMPLETE | 2026-07-26 | 2026-07-26 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Lifecycle detectors | ✅ COMPLETE | 2026-07-27 | 2026-07-27 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Live state and budgets | ✅ COMPLETE | 2026-07-27 | 2026-07-27 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Attention and consolidation | ✅ COMPLETE | 2026-07-27 | 2026-07-27 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Integrity and enforcement | ✅ COMPLETE | 2026-07-28 | 2026-07-28 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Evidence matrix and graduation | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Close-out and ship 2.0.0a1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Fleet pattern: glossary, skill, productization | 🟡 IN PROGRESS | 2026-07-28 | — | handoffs/PHASE-7-HANDOFF.md |
| 8 | jcode-vetted attention mechanisms: gap detection, reinforce verb, negative-space, jcode host | ⬜ NOT STARTED | — | — | handoffs/PHASE-8-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
baseline_tests_after_phase0: 1379 passed, 7 skipped (pre-phase measured baseline was 1330, not the plan-time digest's stale 1253)
phase0_commit: 184c353 (21 files, +1098/−238); procedure bumped 1.9.0 → 1.10.0; deferred display token "⏸️ DEFERRED"; separator baseline 40 → 42; new test files tests/test_honest_closeout.py + tests/test_epistemics_unknown_never_zero.py
```

### Phase 1 Outputs

```
baseline_tests_after_phase1: 1424 passed, 7 skipped (was 1379); commit 586d572
phase1_artifacts: New: src/clauderizer/session_ledger.py (stamp/last_stamp/probe), rituals/stranded.py, rituals/interrupted.py, subsys.session-ledger doc (ratchet-enrolled at 0 omissions); refusal journal at ops REGISTRY seam → .clauderizer/refusals.jsonl (WRITER ONLY — reader integration deliberately left to phase 3's cz_mine_failures work); sessions.jsonl + refusals.jsonl gitignored via init. Design delta vs assessment: interrupted gained a LIVENESS GATE (alive/own-pid claimant = quiet; dead = stranded's voice; fires only when the ledger cannot grade) — required to keep an active session's digest byte-identical while it works.
```

### Phase 2 Outputs

```
baseline_tests_after_phase2: 1457 passed, 7 skipped (was 1424); commits 6215726 (amendment first) + cabbd3e (implementation)
phase2_artifacts: INVARIANT-10 + D-072 (amendment predates stamp code in git: 6215726 < cabbd3e). New: state_stamp.py (FIGURE_KEYS 8-key ratchet, ARM_ENV=CLAUDERIZER_STATE_STAMP, emit() change-trigger), rituals/budgets.py (RESERVE_FRACTION=0.10, declarations/assess/describe, distinct-DATE spend), telemetry.record_stint + PROC_TAG, preflight.record_run_stint (op-called; library run() write-free — C-02), pre_compact wind-down convergence, cz_next_phase_context wind_down attachment, contract 1.1, dormant template comment. STAMP IS ENV-ARMED DORMANT; BUDGETS DECLARED-DORMANT — phase-5 matrix decides both defaults. O-01 (recording coverage) deliberately left open for phase 5: stints only began accruing this phase.
```

### Phase 3 Outputs

```
baseline_tests_after_phase3: 1487 passed, 7 skipped (was 1457); commits d33a882 (decisions first) + 8f29e0f (receipts) + 63fbbb9 (merge-base/ancestry/correction-advisory + procedure 1.11.0) + 2361e0c (refusals reader)
phase3_artifacts: D-073 + D-074 (both predate implementation in git: d33a882 < 8f29e0f/63fbbb9). New: receipts.py (record_seen/load_seen/split_seen; seen.local.jsonl O_APPEND sidecar), ops._receipted REGISTRY-seam wrapper (allowlist exactly cz_get/cz_resolve_finding/cz_resolve_open_item/cz_check_exit_criterion; open items receipt gid-qualified; criteria under synthetic criteria:gid:phase key), digest never-engaged/engaged-but-open split (conditional emission), paths.seen_file + paths.refusals_file, ops._refusal_candidates (miner second source), analyze.near_duplicate_gameplan_lessons, mutations._inline_trailer + survivor ancestry + correction advisory, curate/loop_step/mine id+ledger with suppressed_count + all_proposals + converged_with_suppression, GAMEPLAN-PROCEDURE 1.11.0 (write-corrections-back discipline), close-gameplan/record skills both copies, subsys.receipts (ratchet-enrolled at 0 omissions). Tier-1 gitignore gap closed: sessions.jsonl/refusals.jsonl joined LOCAL_STATE_IGNORES (P1 had init-only). RECEIPTS AND MERGE-BASE ARE ADVISORY-ONLY; capability-not-effect until the phase-5 matrix (dismissal-recurrence + stale-lesson-surfacing signals pre-named in D-074).
```

### Phase 4 Outputs

```
baseline_tests_after_phase4: 1516 passed, 7 skipped (was 1487); commits d33a882..e25d36d span P3+P4; phase-4 commit e25d36d (16 files, +859); D-076 recorded before ENFORCEMENT.md
phase4_artifacts: New: rituals/merge_audit.py (compute/describe; --full-history is LOAD-BEARING — default git history simplification drops merges TREESAME to a parent, which is exactly the lost-update shape; discovered live when the first fixture returned empty), docs/ENFORCEMENT.md (31 rows, four tiers per D-076, D-066+INVARIANT-05 verbatim, fleet rows per A-001, jcode rows deferred to P8 per A-002), tests/test_merge_audit.py (7: lost-update/self-clear/squash-invisible/fenced-exempt/subprocess<=8/surfacing), tests/test_enforcement_ladder.py (row+tier parse only), tests/test_transport_parity.py (15-op matrix, twin repos, direct-fixture preludes; allowlist = clauderizer_status REQUIRED + cz_state stripped + JSON/root normalization; ZERO undocumented divergences found). Disclosure landed on the instructions floor: claude_stanza.md source + CLAUDE.md/AGENTS.md renders byte-identical + README + TRUST.md; NO digest line (pinned). Merge audit surfaces: digest ⚠ line, preflight merge_integrity warn-never-fail, cz_audit merge_integrity list. ADVISORY-SILENT; seeded-fault value claims wait for phase 5.
```

## Corrections Log

### C-01 — Phase 1

**Phase**: 1
**What gameplan said**: The backstop detector's vetted geometry (research-fractal-vetting.json, intent-postmortem assessment): fire whenever the phase is in_progress AND >=1 non-docs commit landed since the tracker anchor AND every closing residue is absent — git evidence only.
**What was actually correct**: Implemented with an additional LIVENESS GATE consulting the session ledger: a provably-alive claimant (or the viewing process itself) means ordinary mid-phase work and stays quiet; a provably-dead claimant is stranded.py's finding; the backstop fires only where the ledger cannot grade (no stamp, or inconclusive probe such as cli transport / other host).
**Why**: The literal geometry fired on ORDINARY LIVE WORK — every active mid-phase repo shows work commits after the anchor with closing writes legitimately not yet run, so the existing INVARIANT-08 golden (test_memory_lag byte-identity) went red the moment the detector landed. Git alone cannot distinguish "died mid-phase" from "being worked right now"; the ledger can. The gate errs SILENT (the binding condition's stated direction) and yields exactly one voice per repo state, pinned by disjointness tests. Phase 5's matrix leg must evaluate the GATED geometry, not the assessment's literal one.

### C-02 — Phase 2

**Phase**: 2
**What gameplan said**: The vetted assessment placed the stint writer inside preflight's run() ("best-effort append one stint via record_stint under write_lock at the write site ... the procedure's own mandated ritual the spend recorder").
**What was actually correct**: The writer is the cz_preflight OP (ops layer, already writes=True for the baseline refresh), calling the new preflight.record_run_stint(); the library run() is pinned WRITE-FREE by test.
**Why**: Implementing the assessment literally made every library caller a telemetry writer: the suite's read-only sample_repo fixture accrued stint records across runs (progressively flipping zero-telemetry tests), and test_write_path's principle — a green pre-flight must not dirty the tree — went red. The ritual-as-recorder intent survives at the op boundary agents actually invoke; embedders, tests, and fixtures calling run() stay byte-free. Same lesson class as C-01: the vetted sketch scopes the mechanism, the goldens find the blast radius.
