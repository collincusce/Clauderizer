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
| 7 | Fleet pattern: glossary, skill, productization | ✅ COMPLETE | 2026-07-28 | 2026-07-28 | handoffs/PHASE-7-HANDOFF.md |
| 8 | jcode-vetted attention mechanisms: gap detection, reinforce verb, negative-space, jcode host | ✅ COMPLETE | 2026-07-28 | 2026-07-28 | handoffs/PHASE-8-HANDOFF.md |

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

### Phase 8 Outputs

```
baseline_tests_after_phase8: 1550 passed, 7 skipped (worktree venv .venv/bin/pytest; baseline was 1516+7; +34 new tests: tests/test_memory_gap.py 12, tests/test_reinforce_lesson.py 17, tests/test_negative_space_procedure.py 4, +1 transport-parity matrix row)
phase8_artifacts: Branch worktree-agent-af68c07562fb35d36 @ e5b9335 (worktree /home/ccusce/Clauderizer/.claude/worktrees/agent-af68c07562fb35d36; ff-merged to main@9c5e0d6 first — worktree had been created at the v1 bootstrap commit). Code: analyze-op gap advisory + telemetry.record_gap (ops.py cz_analyze only, hook path byte-free), corpus_health gap_events, telemetry.record_reinforced + lesson_health reinforced_count/reinforcement evidence + curator reinforcement evidence, mutations.reinforce_lesson via _inline_trailer, lesson_state.REINFORCED_RE/parse_reinforcement beside _STATE_RE, new op cz_reinforce_lesson (REGISTRY+tools_list+README 68 tools), GAMEPLAN-PROCEDURE v1.12.0 negative-space text (source template + blessed render, byte-identical), ENFORCEMENT.md four rows, subsystem docs (markdown-core/mutations/ops/telemetry) pay the doc-seam ratchet. All guards armed by injection then reverted (L-68 step 4). Digest: zero advisory bytes pinned; the only digest delta a live host sees is the Tools listing line growing by the one new tool name (sanctioned surface change, INVARIANT-07 additive).
jcode_host_row: UNVERIFIABLE (honest, per the vetted or-branch). Blocking reasons, all probed 2026-07-28: no jcode binary on PATH (which=1); no Rust toolchain at all (cargo/rustc/rustup absent, ~/.cargo does not exist — jcode is a Rust workspace, uninstallable without a global toolchain mutation outside a worktree-isolated worker's writ); no ~/.jcode state dir; not in npm -g (only claude-code/higgsfield/corepack/npm), uv tools (kimi-cli only), pipx, /usr/local/bin, /opt; no local clone in ~ or /tmp. Even with a build, the vetted bar is a LIVE session (MCP initialize + cz_status reachable + AGENTS.md stanza demonstrably in context), which needs a jcode-supported model credential this environment does not hold. Consequently: NO env markers captured (none fabricated), NO detect_session_agent arm added, NO native emitter added — src/ contains zero jcode detection/emitter code (the only src occurrence of the word is the procedure changelog prose citing D-075). What a verification session needs: host with rustup+cargo, git clone github.com/1jehuang/jcode @ >= a92b270, cargo build --release, a supported model API key, cwd = a clauderized repo, then (a) confirm initialize handshake against repo-root .mcp.json clauderizer entry asserting serverInfo.name, (b) drive one prompt that calls cz_status and returns the digest, (c) confirm the AGENTS.md stanza reached context, (d) capture real session env markers BEFORE any detect arm, (e) confirm .claude/skills discovery via skill.rs loader paths. Phase-5 matrix: this row enters as a named gap, not a silent skip (O-02 rule).
```

### Phase 7 Outputs

```
dogfood_fleet_run: N=2 host-spawned workers + hub (manager=fable-hub), cz_assign partitioning: worker-jcode → alpha phase 8 (worktree isolation, code via branch e5b9335 merged 784ccd9, memory via hub MCP), worker-curator → curator-loop iteration (memory-only). Figures: memory collisions 0 (duplicate-id scan DECISIONS/LESSONS/HARDENING clean), LockHeld 0 across 27 hub writes (16 jcode + 11 curator) under real concurrency (revision 1012→1030 mid-run), honest-close outcomes: both workers complete with negative-space sections, both verified against engine state (fleet step 5). Wall-clock: curator ~16min, jcode ~33min. Worktree bootstrap surprise recorded as gameplan lesson #4 (worker had to fast-forward a v1-bootstrap-pinned worktree)
baseline_tests_after_phase7: 1554 passed, 7 skipped post-merge of P7+P8 (was 1516; +4 seam tests from P7, +34 from P8); P7-only hub tree measured 1520 passed pre-merge
phase7_artifacts: Commits 61c35d2 (feat: skill productized src+render byte-identical, tests/test_skill_asset_seam.py 4 pins armed-once-red, test_init fleet assertion, README+ARCHITECTURE glossary refs, GLOSSARY status refresh) + 71f8805 (curator writes) + 703727d (P8 close writes) + 784ccd9 (P8 merge). Briefing contract gained the D-075 negative-space clause (send-back = hub judgment). H-30 filed: serving-engine backward-stamp (published 1.14.3 MCP vs 2.0-alpha tree) — recovered via .venv/bin/clauderize upgrade, stamp now 1.12.0
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
