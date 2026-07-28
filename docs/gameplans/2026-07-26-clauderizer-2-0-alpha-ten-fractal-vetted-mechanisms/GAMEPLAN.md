# clauderizer 2.0 alpha — ten fractal-vetted mechanisms Gameplan

> Created: 2026-07-26
> Status: Executing
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

### A-001 — Fleet pattern joins the alpha: glossary, clauderizer-fleet skill, fleet-vs-solo matrix leg

- **Date**: 2026-07-26
- **Affected sections in GAMEPLAN.md**: Phases (new phase "Fleet pattern: glossary, skill, productization" — appended as Phase 7, ordered by dependency to execute after phases 0-2 and alongside/before phase 4's ladder finalization); Phase 5 exit criteria (fleet-vs-solo hypothesis leg added); new canonical doc docs/GLOSSARY.md (seeded now, productized in the new phase); repo-local skill .claude/skills/clauderizer-fleet (created now, shipped-asset productization in the new phase)
- **Affected phases**: 5, 7 (new)
- **Triggered by**: User direction 2026-07-26 after the D-070 plan review: make the multi-agent fan-out pattern part of the glossary, create skills to manage the use case; thesis "the more agents work on a problem, the better the results" — recorded via D-071
- **What changed**: Adds D-071's three artifacts to the alpha scope: (1) docs/GLOSSARY.md canonical vocabulary with the fleet cluster (fleet, hub, worker, worker briefing, assignment, hub-and-spoke law) plus core terms; (2) the clauderizer-fleet skill — repo-local immediately, productized into the shipped asset set (src source + installed render + init/uninstall wiring + dual-copy seam test) by Phase 7; (3) a fleet-vs-solo leg in Phase 5's matrix with D-071's pre-named signal. ENFORCEMENT.md gains fleet rows from whichever of Phase 4 / Phase 7 lands second — both phases carry the criterion so ordering cannot drop it.
- **Why**: The ten adopted mechanisms' primary use case IS the fleet: heal-on-proof handles dead workers, stamps propagate hub state to workers, budgets aggregate fleet spend, merge-audit guards the worktree edge, and the engine's existing locking/assignment/--repo substrate already carries hub-and-spoke fan-out today. Making the pattern canonical vocabulary + a managed skill turns an implicit capability into a supported one, while D-071 keeps the "more agents = better" thesis a measured hypothesis rather than shipped doctrine (L-50, D-064).

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase Live state and budgets)_ Recording coverage gates budget meaning: before reserve-window-wind-down can graduate, measure the fraction of real sessions that produce recorded spend stints (per host kind). If coverage is low, wind-down math is fiction — the phase-5 verdict must cite the measured number and choose dormant/withdraw accordingly. (Vetting condition: "measure recording coverage FIRST since it gates everything.")

**O-02.** _(phase Evidence matrix and graduation)_ Matrix harness legs required by the vetting conditions — kimi-pinned, ops-mode, ≥1 non-Claude host, slow-FS WSL row, an under-adhering host — need confirmed availability/harness before phase 5 begins. A leg that cannot run becomes a named gap in that mechanism's graduation verdict, never a silent skip.

**O-03.** _(phase Attention and consolidation)_ refusals.jsonl has a writer (P1, REGISTRY seam) but no reader yet — D-069's spirit wants the journal consumed. Wire it as a read source in cz_mine_failures (and/or a read-only count in cz_corpus_health) during phase "Attention and consolidation", or explicitly decide it stays a dormant evidence store until the matrix.

## Phase Breakdown

### Phase 0: Honest endings and epistemics

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_transition_phase writes `deferred`; ABANDONED/EXITED arrive as aliases mapping to deferred and no fourth phase status token exists — pinned by a new test file that passes
- [x] mutations._refresh_tracker_headers treats deferred as closed exactly like status_bundle._lifecycle — the runtime-demonstrated divergence (COMPLETE+DEFERRED rendering 'Executing') has a regression test that passes
- [x] The laundering advisory (completing with unchecked exit criteria) is advisory-only with no enable/disable flag, and the deferred path never nags about unchecked criteria — both behaviors pinned by tests (INVARIANT-05)
- [x] The pre-release corpus sweep exists as an executable check: re-parses all tracked gameplan trackers under the positional matcher and asserts every classification flip moves toward open/deferred, never toward complete
- [x] The four epistemics conflation sites are fixed with missing-arm tests written FIRST (conditions.py TimeoutExpired/OSError arms covered); an unknown probe counts in the summary string, lowers the verdict to PASS WITH WARNINGS, and says 'UNKNOWN, not pass'
- [x] exit-criterion `met` stays a boolean with an additive `unevaluable` field — no tri-state flip; a test locks external ops-JSON truthiness compatibility (INVARIANT-07)
- [x] Both skill copies (src/clauderizer/skills asset AND installed .claude/skills), the ops.py cz_transition_phase docstring, and the MCP tools_list schema updated in the same commit; reason sanitization is table-safe with the engine-owned status token leading and no crash on empty/whitespace reason
- [x] Healthy-repo digest byte-identical to pre-phase; full suite green at >=1253 tests plus this phase's additions

### Phase 1: Lifecycle detectors

**Goal**: Implement heal-on-proof-stranded-state and intent-postmortem-with-backstop-landings under their vetting conditions: POSIX-gated evidence-graded liveness probe (non-posix grades inconclusive, never signals), display-only contract (read path writes zero bytes), the judgment menu's honest-close disposition using phase 0's deferred vocabulary, backstop abandoned-work detector with err-silent fire-quiet geometry (in_progress + non-docs commits + zero closing residue), one-voice wording per L-55, refusal journal as a separable ship-or-defer. Advisory-only; no default-behavior claims before the matrix.
**Depends on**: Honest endings and epistemics.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Stranded-state probe is POSIX-gated: on non-posix platforms it grades inconclusive without any os.kill call — a test proves the win32 path can never signal a live process
- [x] Display-only contract pinned: the detect/read path writes zero bytes under both docs/ and .clauderizer/ (sessions.jsonl untouched on read), stated in the module docstring memory_lag-style and proven by test
- [x] The judgment menu's 'close honestly (deferred)' disposition is reachable end-to-end using phase 0's vocabulary, and adopting 'continue' re-stamps evidence via the blessed same-status in_progress transition
- [x] Backstop landing detector fires ONLY when: phase in_progress AND >=1 non-docs commit since the tracker anchor AND every closing residue absent; any post-anchor handoff refresh or phase summary keeps it silent — the full fire/quiet geometry is a test matrix
- [x] One voice (L-55): when the detector fires, its describe() subsumes the memory_lag wording and explains clean_tree's dirty-tree FAIL and do-phase's STOP-and-report step — no fourth phrasing exists (greppable assertion)
- [x] Refusal journal either ships (ok:False wrapper at Op/REGISTRY construction covering BOTH run_op and the MCP server's direct REGISTRY path) or is recorded as explicitly deferred — not silently dropped
- [x] All new surfacing is advisory with no recommended-default claim (that waits for phase 5); healthy-repo digest byte-identical; suite green

### Phase 2: Live state and budgets

**Goal**: Record the INVARIANT-08 append-only amendment FIRST (figures-only change-triggered structured notices on tool results as a category distinct from status injection), then implement per-call-live-state-stamp (change-triggered on figure/revision delta via in-memory last-emission; wrapper isolation pinned both directions; figures key-whitelist ratchet; bounded read cost — no unbounded approval artifact_hash recompute) and reserve-window-wind-down budgets (two tiers only: gameplan-sessions + phase-sessions; spend unit host-stable distinct-DATE stints; WIND_DOWN derived at read time, never persisted, no flags, reserve fraction a module constant; phase-aware advisory wording; pre_compact convergence surfacing per L-68 clause 1). Budgets ship dormant — no filled template default until the matrix.
**Depends on**: Honest endings and epistemics.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] The INVARIANT-08 amendment is recorded as an append-only supersession (figures-only, change-triggered structured notices on tool results defined as a category distinct from status injection) BEFORE any stamp code lands — the amendment's D-NNN/INVARIANT entry predates the first stamp commit in git history
- [ ] cz_state stamp is change-triggered: attached only when the figure set or revision differs from the last emission in this server session (in-memory last-stamp, no persisted flag) — pinned by test
- [ ] Wrapper isolation pinned in both directions: a stamp exception never converts an op success into failure, and an op exception is never masked by stamp attachment; plus the figures key-whitelist ratchet test
- [ ] Stamp read cost bounded: the exit-criteria figure skips or byte-caps approval-row artifact_hash recomputation — no full-file sha256 per call on large artifacts, pinned by test
- [ ] Budgets: exactly two tiers (gameplan-sessions, phase-sessions); spend unit is host-stable distinct-DATE stints with proc tag as tiebreaker only; template guidance says declare phase budgets only when >1
- [ ] WIND_DOWN is derived at read time, never persisted, no enable/disable flag, reserve fraction a module constant; phase-aware advisory wording distinguishes 'IN the final budgeted stint — land the Ending Protocol' from 'recorded spend exceeds budget' — both pinned
- [ ] pre_compact convergence surfacing ships in this phase (L-68 clause 1: session-start surfacing alone does not survive session distance) — test proves the wind-down advisory reaches the pre-compact payload when armed
- [ ] Budgets ship dormant: no filled template default anywhere; O-item on recording coverage carried forward or resolved; healthy-repo digest byte-identical; suite green

### Phase 3: Attention and consolidation

**Goal**: Implement seen-vs-open-receipts (receipts ONLY from genuine engagement — cz_get success, resolve_finding/open_item, check_exit_criterion; lock-free O_APPEND single-line writes to gitignored .clauderizer/seen.local.jsonl; the read-op purity erosion recorded as its own D-NNN before the write lands; digest split = ANY-reader engagement, never-engaged vs engaged-but-open; D-068 drop-nothing golden gates) and two-speed-consolidation-with-merge-base (merge-base convergence implemented as execution of D-059 / dreaming-loop O-02 and recorded as such; suppressed_count in every curate/loop_step summary with the all_proposals include-suppressed read path kept — display never authority per D-013; correction-advisory landing detector + discipline text in the same change across both skill copies per L-16/L-55; contradiction scan reuses analyze._tokens and _LESSON_DUP_JACCARD verbatim per INVARIANT-09).
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Receipts appended ONLY on genuine engagement (cz_get success, cz_resolve_finding, cz_resolve_open_item, cz_check_exit_criterion) — no via='handoff'/'phase_context' auto-receipts — pinned by test
- [ ] Receipt writes are lock-free O_APPEND single-line JSONL to .clauderizer/seen.local.jsonl; the file is gitignored by init AND added to modernize's ensure_gitignore_current tier-1 so existing repos converge (D-067 complete)
- [ ] A new D-NNN recording the read-op purity erosion (cz_get stays writes=False; rebuildable-local-sidecar append is the sole sanctioned exception) is in DECISIONS.md before the write path lands
- [ ] Digest split is ANY-reader engagement (never-engaged vs engaged-but-open); golden gates pass: with no sidecar the bundle and digest are byte-identical to pre-phase, with receipts every open id prints in exactly one bucket and resolved ids in neither (D-068 drop-nothing)
- [ ] Merge-base convergence is implemented and its adoption decision cites D-059 and dreaming-loop O-02 as the executed lineage (not a novel borrow); the dismissal-recurrence signal for phase 5 is named in the decision
- [ ] suppressed_count is reported in every cz_curate and cz_loop_step summary; the all_proposals include-suppressed read path exists — ledger filtering stays display, never authority (D-013) — pinned by test
- [ ] Correction-advisory detector and its discipline text land in the SAME change: GAMEPLAN-PROCEDURE.md + close-gameplan/record skills, both src template and installed .claude render (L-16/L-55)
- [ ] Contradiction scan imports analyze._tokens and analyze._LESSON_DUP_JACCARD — no second tokenizer or threshold constant (INVARIANT-09; test_canonical_tokenizer stays green); suite green; digest byte-identical healthy

### Phase 4: Integrity and enforcement

**Goal**: Implement merge-integrity-audit-for-canonical-docs (git evidence only: merge parents + merge-base + blob comparison; no writer-side ledger, no persisted finding state; O(1) hook-path subprocess cost — single most-recent docs-touching merge, batched blob resolution; squash blind spot stated in docstring AND user-facing wording with no issue-#9-catching claim; quoted-conflict-marker handling pinned; surfaces through existing cz_audit/cz_preflight/cz_status only, no new MCP tool) and enforcement-ladder-with-declared-capabilities (ENFORCEMENT.md maps every discipline — including the nine mechanisms landed in phases 0-3 — to hard-NORMALIZE per D-066 / advisory / instructions-floor; restates D-066 and INVARIANT-05 verbatim; capabilities derived from session host descriptors, never config flags; negative-capability disclosure on the instructions floor, NEVER a digest line; transport parity matrix test comparing CLI ops vs MCP after JSON-normalizing both payloads against an explicit pinned divergence allowlist, with identical staged-state preludes for stateful ops; test parses row name + tier column only).
**Depends on**: Honest endings and epistemics, Lifecycle detectors, Live state and budgets, Attention and consolidation.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Merge audit ground truth is git evidence only (merge parents + merge-base + blob comparison); no writer-side per-file audit ledger and no persisted finding state exist anywhere in the change (revision.py's no-audit-log stance holds)
- [ ] Hook-path subprocess cost is O(1) per compute(): capped at the single most recent docs-touching merge with batched blob resolution (~4 calls) — pinned by a subprocess-count test
- [ ] The squash blind spot is stated in the module docstring AND in user-facing finding/digest wording; no claim anywhere that the audit catches Fractal issue #9's exact squash scenario
- [ ] Conflict-marker scan handles docs that QUOTE markers: fenced code blocks skipped or the quoted-marker behavior pinned by an explicit test
- [ ] Audit surfaces through existing cz_audit/cz_preflight/cz_status only — no new MCP tool; tool-description token cost measured flat; ships advisory-silent with no value claim (that waits for phase 5's seeded-fault protocol)
- [ ] ENFORCEMENT.md exists, maps every discipline (including the nine mechanisms from phases 0-3) to hard-NORMALIZE (D-066) / advisory / instructions-floor, restates D-066 and INVARIANT-05 verbatim, and expresses preflight's real semantics (D-024 blocking default + config.preflight_advisory downgrade)
- [ ] Capabilities in the ladder are derived host facts (session._HOOK_HOSTS/_PROMPT_HOSTS + CROSS-HOST descriptors), never config flags; the negative-capability disclosure lives on the instructions floor (claude_stanza.md/README/TRUST.md) and NO digest line was added (INVARIANT-08)
- [ ] Transport parity matrix test green: CLI ops vs MCP payloads equal after JSON-normalizing BOTH, against an explicit pinned divergence allowlist; stateful ops (resolve_cascade, dismiss/defer, …) get identical staged-state preludes via direct fixture setup; test_enforcement_ladder parses row name + tier column only; suite green

### Phase 5: Evidence matrix and graduation

**Goal**: Run the D-064 multi-agent matrix with each mechanism's pre-named signals (L-50: metric named before measuring; a discard is a successful outcome). Legs per the vetting conditions: Claude Code + at least one non-Claude host, kimi-pinned and ops-mode legs for budgets, slow-FS WSL row for the stamp, an under-adhering host for the backstop detector, A-alive and cross-host controls for stranded-state (zero false positives required), seeded-fault protocol for the merge audit (detection rate, clean-merge false-positive rate, healthy-repo digest byte-identity). Measure recording coverage FIRST — it gates whether budget wind-down means anything. Write a per-mechanism verdict: graduate as shipped default, keep documented-dormant, or withdraw — each with its figures recorded as decisions/amendments.
**Depends on**: Honest endings and epistemics, Lifecycle detectors, Live state and budgets, Attention and consolidation, Integrity and enforcement.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Recording coverage measured FIRST and recorded with figures — the budgets verdict cites it explicitly (low coverage ⇒ wind-down math is fiction ⇒ dormant or withdraw)
- [ ] Matrix legs executed and logged per condition: Claude Code + >=1 non-Claude host; kimi-pinned + ops-mode legs for budgets; slow-FS WSL row for the stamp (stamped vs unstamped arms); an under-adhering host for the backstop detector; any leg that cannot run is a named gap in the verdict, never a silent skip
- [ ] Stranded-state: zero false positives across same-host-MCP-stranding vs A-alive and cross-host controls, or the mechanism stays advisory-dormant — verdict recorded with counts
- [ ] Backstop detector fires on seeded abandoned work and stays quiet on healthy closes across the matrix; never-engaged advisory fires on a genuinely ignored finding and stays quiet on engaged ones — both with counts
- [ ] Merge audit seeded-fault protocol run: detection rate on true merges, clean-merge false-positive rate, and healthy-repo digest byte-identity all recorded
- [ ] Fleet-vs-solo leg run per D-071's pre-named signal: the same seeded task solo vs an N-worker fleet (hub-and-spoke, cz_assign partitioning) — exit-criteria pass quality, wall-clock, LockHeld/collision counts, and independent-verifier-found defects recorded; the 'more agents = better' hypothesis confirmed, refuted, or bounded, and the clauderizer-fleet skill's guidance updated to match the figures
- [ ] Per-mechanism verdict written for ALL TEN (graduate as default / documented-dormant / withdraw), each with its pre-named signal's measured figure (L-50) — recorded as decisions/amendments; discards documented as successful outcomes

### Phase 6: Close-out and ship 2.0.0a1

**Goal**: Ship the alpha: CHANGELOG documents every mechanism with its conditions and matrix verdict, the pass_rate semantic shift (goal-met rate once deferred outcomes log), and the receipts sidecar classification. Version 2.0.0a1 (PEP 440 pre-release — pip installs only with --pre). Release ritual passes the L-51 three sweeps and the H-28 does-the-CODE-pass check; publish to PyPI; verify fresh-venv install + doctor green. Then post-mortem, cz_audit per D-051, and close the gameplan.
**Depends on**: Evidence matrix and graduation.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] CHANGELOG documents all ten mechanisms with their binding conditions and matrix verdicts, the pass_rate semantic shift (goal-met rate once deferred outcomes log), and the receipts sidecar classification
- [ ] pyproject version = 2.0.0a1; release notes state PEP 440 pre-release semantics (pip installs only with --pre)
- [ ] L-51 three sweeps + H-28 does-the-CODE-pass check green before tagging; no Fractal outcome numbers cited anywhere in release materials (D-070)
- [ ] Published to PyPI; fresh-venv `pip install --pre clauderizer==2.0.0a1` succeeds and `clauderize doctor` is green
- [ ] Post-mortem written; cz_audit (D-051) run with findings triaged; gameplan closed via the close-gameplan procedure

### Phase 7: Fleet pattern: glossary, skill, productization

**Goal**: Productize the D-071 fleet pattern (A-001). Harden docs/GLOSSARY.md into the canonical vocabulary surface (fleet cluster + core terms, each entry pointing at its owning doc) and sweep the non-single-sourced doc listings that should reference it (L-65). Move clauderizer-fleet from repo-local to shipped asset: src/clauderizer/skills source + installed render identical under the dual-copy seam test, assets.py ships it on init, uninstall removes only clauderizer-owned skills. Audit the skill capability-honest: every 2.0-mechanism reference names its landing phase and degrades gracefully where absent. Add the fleet discipline rows to ENFORCEMENT.md (hub-and-spoke law = instructions-floor; assignment ownership = advisory) if phase 4 already landed, else leave them to phase 4's exhaustive sweep. Dogfood one real fleet run in this repo (N>=2 workers, hub-and-spoke, cz_assign partitioning) and record its figures.
**Depends on**: Honest endings and epistemics, Lifecycle detectors, Live state and budgets.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] docs/GLOSSARY.md carries the fleet cluster (fleet, hub, worker, worker briefing, assignment, hub-and-spoke law) + core vocabulary, every entry pointing at its owning doc; the L-65 sweep ran over non-single-sourced doc listings (README, ARCHITECTURE) so the new canonical doc is referenced, with an executable pin where one fits
- [ ] clauderizer-fleet exists in BOTH copies (src/clauderizer/skills source + installed .claude/skills render) byte-identical, covered by the dual-copy seam test alongside the existing nine skills
- [ ] assets.py ships clauderizer-fleet on init; golden init test updated; uninstall removes only clauderizer-owned skills — all pinned by tests
- [ ] Capability-honesty audit green: every reference in the skill to a 2.0 mechanism names the phase that lands it and specifies the degraded behavior when absent — no unbuilt feature described as present (L-65 claim-needs-artifact)
- [ ] ENFORCEMENT.md carries the fleet rows (hub-and-spoke law = instructions-floor; assignment ownership = advisory) regardless of whether this phase landed before or after phase 4
- [ ] Dogfood fleet run recorded via cz_add_output: N>=2 host-spawned workers over independent work in THIS repo, cz_assign partitioning, all tracked writes through the hub — figures captured: memory collision count (must be 0), LockHeld retry count, honest-close outcomes per worker
- [ ] Full suite green; healthy-repo digest byte-identical
