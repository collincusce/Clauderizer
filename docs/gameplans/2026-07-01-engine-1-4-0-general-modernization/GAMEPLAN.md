# engine-1.4.0-general-modernization Gameplan

> Created: 2026-07-01
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

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Approval gates are an exit-criterion kind bound to a content hash, checked lazily

**Context**: Marketing-studio's highest-leverage control — "human approves the shot spec before any generation spend" — exists only as prose; nothing records what was approved and an edited spec keeps its stale blessing. Swirls.ai's sharpest idea: permissions derive from the SHA-256 of the canonical definition, so modifying the definition invalidates old tokens. Clauderizer has no runtime to enforce anything, and INVARIANT-05 forbids blocking.
**Decision**: Adapt hash-derived authority to ask-time: an exit criterion may declare kind=approval with an artifact path. A new blessed write cz_approve_gate records approval as the SHA-256 of the artifact's current content plus date and optional note. Every subsequent read that surfaces the criterion (cz_check_exit_criterion, cz_preflight, cz_transition_phase, status detail) recomputes the hash; a mismatch surfaces the criterion as "approval stale — artifact changed since approval" and unchecks it. Advisory only: nothing blocks, no config flag. CLI parity via clauderize ops per L-05.
**Consequences**: Approvals become durable records with automatic expiry-on-edit, at zero runtime cost. One new tool (surface 42→43). Hash computation must handle missing artifacts gracefully (surfaced as "artifact missing", not an exception).
**Evidence**: swirls.ai/security hash-derived authority (verified via llms-full.txt 2026-07-01); marketing-studio D-008 prose gate
**Status**: active (2026-07-01)

### D2 — Deliverables are tracked entities with a kind-defined lifecycle; the matrix renders in detail views only; deliverables are never asset files

**Context**: A campaign's real execution unit is the deliverable (flagship film, pillar short), each progressing independently through concept→spec-approved→produced→assembled→qa→shipped — verified by the flagship output-key churn (five successive keys inside one "Assemble" stage). But a campaign also emits hundreds of rendered files (30 videos, 153 images); tracking those as graph entities would industrialize handoff bloat (D-027, saturation post-mortem).
**Decision**: Kind definitions gain an optional [lifecycle] status vocabulary (campaign ships concept/spec-approved/produced/assembled/qa/shipped; driven/loop omit it). A deliverable is a normal tracked entity (type=deliverable) carrying a `gameplan:` field; its status transitions through the kind's lifecycle via the existing cz_transition_status/cascade machinery. cz_gameplans gains a per-gameplan detail view rendering the deliverables×lifecycle matrix; the injected digest carries at most a one-line rollup for the focused campaign ("deliverables: 3/6 shipped"). Rendered artifact files stay in the repo/studio manifests; a deliverable entity may point at them but they are never entities themselves.
**Consequences**: Campaign semantics become real without a new data model — entities, statuses, and cascade already exist; the feature is a lexicon plus grouping plus rendering. The deliverable≠asset line must be stated in the procedure doc and tool descriptions so deployments don't recreate the bloat we're avoiding. Digest minimalism (INVARIANT-08/D-027) is preserved by construction.
**Evidence**: marketing-studio PHASE-STATUS.md:40-47 flagship_film→kinetic_video_v1 churn (verified 2026-07-01); INVARIANT-12 30-file variant set = ~6 deliverables
**Status**: active (2026-07-01)

### D3 — Standing conditions are declared per gameplan and evaluated lazily inside status/preflight — the engine never schedules, fires, or auto-runs

**Context**: Standing engines (the shorts campaign: weekly cadence, backlog≥3) need their triggers watched, but Clauderizer is a passive layer — no daemon, hooks read-only (INVARIANT-06), everything happens at ask-time. Swirls' trigger/schedule resources assume a runtime we deliberately don't have; host schedulers (cron, scheduled tasks) own cadence.
**Decision**: A loop or campaign gameplan may declare standing conditions in .clauderizer/conditions.<gameplan-id>.toml using the same command-gate primitive as per-kind preflight: each condition is a name plus a shell command whose exit code (0=met) the engine runs ONLY inside cz_status/cz_preflight/cz_loop_step tool calls — never from hooks, never on a timer. A met condition surfaces as "standing condition met — iteration proposed" in the tool result and one digest line for the focused gameplan. The engine proposes; the agent (or the host's scheduler invoking the agent) decides.
**Consequences**: The shorts-style cadence machine gets its threshold watched every time anyone asks for status, with zero daemon and zero INVARIANT-05/06 tension. Command execution reuses the preflight gate runner (timeouts, unwired-gate warnings included). Calendar cadence remains the host's job and the docs say so explicitly.
**Evidence**: GAMEPLAN-PROCEDURE.md v1.3.0 loop-gameplan trigger taxonomy; marketing-studio PLAYBOOK §6 cadence rules enforced by nothing
**Status**: active (2026-07-01)

### D4 — Release shape: engine 1.4.0, procedure 1.4.0→1.5.0, strictly additive, D-011 ritual with 9-cell CI before tag

**Context**: User go (2026-07-01) covers implementing the adopted feature set and shipping it so upgrades deliver it. Engine sits at 1.3.1 (main, clean); PROCEDURE_VERSION is 1.4.0; tool surface 42; mid-flight gameplans exist in at least two corpora (this repo's portfolio, marketing-studio's two campaigns) and must keep working untouched.
**Decision**: Ship everything as engine MINOR 1.4.0. PROCEDURE_VERSION bumps 1.4.0→1.5.0 (MINOR: new optional metadata, new optional TOML files, new tools — no structural change to existing docs). Every feature is additive and defaults to prior behavior when unconfigured: untagged memory, kind files without [lifecycle], absent conditions/preflight TOMLs, unstamped configs all behave exactly as 1.3.1. New tools: cz_approve_gate, cz_modernize (surface 42→44), both reachable via clauderize ops (L-05). Release per D-011: full suite green, release-check exit 0, PR, 9-cell CI green BEFORE tag (L-20), squash-merge, tag on full SHA, GitHub Release, OIDC publish, PyPI + uvx --refresh verification.
**Consequences**: The engine-1.4.0/procedure-1.5.0 pairing must be kept straight in docs and the modernization stamp (they coincidentally near-collide numerically). Back-compat is testable: the existing suite must pass unmodified except where it asserts the tool count.
**Evidence**: pyproject.toml version=1.3.1 @ main (clean tree, verified 2026-07-01); src/clauderizer/__init__.py:12 PROCEDURE_VERSION=1.4.0; ops.py cz_ count=42
**Status**: active (2026-07-01)

## Open Items

**O-01.** cz_analyze keeps resurfacing 10 suggested subsystem edge pairs (mutations↔rituals, rituals↔scaffold, ...) — pre-existing graph hygiene, not this gameplan's scope. Triage once: add real depends_on edges or dismiss via not_related_to.

**O-02.** _(phase 8)_ Invariant near-dup advisory reuses _LESSON_DUP_JACCARD=0.40 for INVARIANT-09 single-sourcing. Recalibrate against marketing-studio's real duplication (INVARIANT-03/04/05 vs 07/08/09 pairs) once Phase 8 measures them — if verbatim pairs score below 0.40, the threshold needs its own reasoned value. _(resolved 2026-07-01: Measured on marketing-studio's real duplication (Phase 8): keep 0.40 — the same-length verbatim pair (INVARIANT-03/08) fires at 0.467 with zero false positives, and lowering the threshold would add noise without catching the misses. The 05/07 and 04/09 pairs are subset-shaped (short restatement ⊂ long rule) and structurally invisible to symmetric Jaccard at any sane threshold; the fix is a containment metric (overlap coefficient), filed as O-04 for a future release.)_

**O-03.** _(phase 8)_ marketing-studio's brief session expects a §6 protocol reply (audit + restatement + questions) and the step-0 usage fixes (wire campaign preflight gates for real, reclassify shorts as kind=loop, curate 13 lessons, record cz_consumes edges). Deliver after 1.4.0 ships; Phase 8's upgrade run covers only the mechanical scaffold half.

**O-04.** Subset-shaped near-duplicates (a terse invariant restating a longer one, e.g. marketing-studio's "logo never AI-generated" vs the full sentence) score below symmetric Jaccard 0.40 by construction. Add an overlap-coefficient (|A∩B|/min(|A|,|B|)) companion signal to the near-dup advisory + modernize detector in a future release — single-sourced beside _LESSON_DUP_JACCARD per INVARIANT-09, with its own measured threshold.

## Phase Breakdown

### Phase 0: Baselines, design decisions & plan commit

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Project ADRs D-042 (two-tier modernization) and D-043 (scoping is filtering) recorded; gameplan decisions D1-D4 recorded
- [x] Five feature entities upserted (feat.scoped-memory, feat.approval-gates, feat.deliverable-matrix, feat.standing-conditions, feat.corpus-modernization) with subsystem depends_on edges
- [x] Baseline captured: engine 1.3.1, PROCEDURE_VERSION 1.4.0, tool surface 42, suite count recorded in outputs registry from a green cz_preflight run
- [x] Plan committed on a feature branch off main; working tree clean afterward

### Phase 1: Scoped memory — write path & near-dup parity

**Goal**: Implement D-043's write half. cz_add_invariant gains optional scope (project|gameplan:<id>) and audience args, written as **Scope**/**Audience** metadata lines in the existing entry grammar (mutations.py add_invariant ~223-237); cz_add_lesson gains optional audience written as a trailing *(audience: X)* marker beside the evidence marker. Extend the write-time near-duplicate advisory from lessons to invariants via a generalized analyze helper reusing analyze._tokens and the single-sourced _LESSON_DUP_JACCARD threshold (INVARIANT-09 — no new tokenizer, no second literal). Abstract index parses and round-trips the new metadata. Ops signatures update automatically; CLI parity via ops --schema. Untagged writes behave byte-identically to 1.3.1.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_add_invariant accepts scope + audience and writes **Scope**/**Audience** metadata lines (test)
- [x] cz_add_lesson accepts audience and writes the *(audience: X)* marker (test)
- [x] Invariant write-time near-dup advisory fires on a verbatim duplicate, computed via analyze._tokens and the single-sourced threshold — canonical-tokenizer guard test still passes (INVARIANT-09)
- [x] Abstract index parses and round-trips Scope/Audience metadata (test)
- [x] clauderize ops --schema shows the new optional args for both tools (CLI parity, L-05)
- [x] Untagged writes produce byte-identical entries to 1.3.1 (test); full suite green

### Phase 2: Scoped memory — read path & curator grouping

**Goal**: Implement D-043's read half as pure filtering. cz_analyze candidate assembly excludes invariants scoped to a non-focus gameplan; cz_next_phase_context and cz_write_handoff gain an optional audience arg — audience-tagged lessons for other audiences drop out of the rollup, untagged entries always pass (rituals/handoff.py collect_lessons/collect_project_lessons ~37-52). Curator paths (cz_consolidate_lessons advisory, cz_corpus_health, cz_curate) group by scope and audience so consolidation is never proposed across them. Digest memory gauge stays unchanged (D-027). No inheritance, no shadowing, no behavior change for untagged corpora.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_analyze excludes invariants scoped to a non-focus gameplan and includes focus-scoped + project ones (test)
- [x] cz_next_phase_context with audience=X drops other-audience lessons and always keeps untagged; the WRITTEN handoff file is never filtered (tests; see correction C-01)
- [x] Curator/consolidation/corpus-health never propose pairing entries across scope or audience (test)
- [x] Existing digest/status golden tests pass unchanged for untagged corpora (INVARIANT-07)
- [x] Full suite green

### Phase 3: Approval gates — hash-bound exit criteria

**Goal**: Implement D1 (gameplan decision). An exit criterion may be an approval criterion: checkbox text of the form "APPROVAL: <artifact-path> — <description>" in the existing - [ ] grammar (status_bundle.py _EC_CHECK_RE ~216). New blessed write cz_approve_gate(phase, criterion, note) computes the artifact's SHA-256, appends an _(approved <date> sha256:<12-hex> ...)_ marker, and checks the box. Staleness is COMPUTED, never auto-written: exit-criteria parsing recomputes the hash and a mismatch makes the criterion report as unsatisfied with an "approval stale — artifact changed" reason, surfaced by cz_check_exit_criterion, cz_transition_phase(complete), cz_preflight, and status detail. Missing artifact surfaces gracefully. Tool surface 42→43 with REGISTRY/TOOL_NAMES parity and clauderize ops reachability (L-05).
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_approve_gate records sha256+date marker and the criterion reports satisfied (test)
- [x] Editing the approved artifact makes the criterion report unsatisfied with 'approval stale' surfaced by cz_check_exit_criterion, cz_transition_phase(complete), and cz_preflight (tests)
- [x] Missing artifact surfaces 'artifact missing' gracefully, no exception (test)
- [x] Tool surface 43 with REGISTRY/TOOL_NAMES parity test green and cz_approve_gate reachable via clauderize ops (L-05)
- [x] Full suite green

### Phase 4: Deliverable-matrix campaigns

**Goal**: Implement D2 (gameplan decision). Kind dataclass gains an optional lifecycle status list loaded from [lifecycle] statuses in kind TOML (kinds/__init__.py ~28-51); campaign.toml ships concept/spec-approved/produced/assembled/qa/shipped; driven/loop omit it. A deliverable is a tracked entity (type=deliverable) carrying a gameplan field; cz_upsert_entity/cz_transition_status advisory-validate its status against the owning gameplan's kind lifecycle (unknown statuses warn, never block). cz_gameplans gains a per-gameplan detail rendering the deliverables×lifecycle matrix; render_digest adds at most ONE rollup line ("deliverables: N/M shipped") for the focused gameplan only when it has deliverables. Single-gameplan repos without deliverables produce a byte-identical digest to 1.3.1 (INVARIANT-07). Deliverables ≠ rendered asset files — stated in tool descriptions.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] campaign kind exposes lifecycle statuses from [lifecycle] in TOML; driven/loop expose none (test)
- [x] A deliverable entity with a gameplan field renders in the cz_gameplans deliverables×lifecycle matrix (test)
- [x] Unknown lifecycle status on a deliverable warns advisory, never blocks (test)
- [x] Digest adds at most one deliverables rollup line, only for a focused campaign that has deliverables; single-gameplan no-deliverable digest byte-identical to 1.3.1 (INVARIANT-07 test)
- [x] Full suite green

### Phase 5: Standing conditions + consumes surfacing

**Goal**: Implement D3 (gameplan decision) plus the GR-8 polish. Loop/campaign gameplans may declare standing conditions in .clauderizer/conditions.<gameplan-id>.toml ([conditions] name→shell command, exit 0 = met), loaded and run by the same gate-runner as per-kind preflight (rituals/preflight.py _load_preflight_gates pattern) ONLY inside cz_status/cz_preflight/cz_loop_step tool calls — never from hooks, never on a timer. A met condition surfaces "standing condition met — iteration proposed" in the tool result plus one digest line for the focused gameplan. Consumes surfacing: cz_next_phase_context/handoff renders the gameplan's declared consumed entities (from the gameplan.<gid> graph node) with their current status/version so cross-gameplan consequences are visible where work starts; portfolio cards already count pending cross-refs — verify and test that path end to end.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] conditions.<gameplan-id>.toml evaluated inside cz_status/cz_preflight/cz_loop_step; met condition surfaces 'iteration proposed' in result + one digest line (test)
- [x] Hook digest path performs no condition evaluation — no subprocess from hook (test)
- [x] cz_next_phase_context/handoff renders consumed entities with current status/version (test)
- [x] Cross-gameplan pending cross-ref visible in portfolio card counts end to end (test)
- [x] Full suite green

### Phase 6: Corpus modernization framework

**Goal**: Implement D-042 — the release's centerpiece. Config gains procedure_version (stamped by init, preserved by merge_missing). A modernization registry keyed by procedure version drives cz_modernize: default is a read-only REPORT (tier-1 mechanical items it would apply + tier-2 advisory proposals); apply=true executes tier-1 only — scaffold missing .clauderizer/preflight.<kind>.toml.example for kinds in use, ensure .clauderizer/kinds/ exists, run config migrations, refresh the engine-owned GAMEPLAN-PROCEDURE.md copy, stamp the new procedure_version — and NEVER touches DECISIONS/INVARIANTS/LESSONS/HARDENING or any gameplan memory. Tier-2 detectors: declared-but-unwired preflight gates, near-duplicate invariant pairs (canonical tokenizer) suggesting scope tags, campaign gameplans with zero deliverable entities, loop gameplans without standing conditions. New CLI subcommand clauderize upgrade = report + apply in one step. cz_status/doctor surface one ⚙ modernization line when the stamp is stale or proposals exist; hooks remain untouched read-only (INVARIANT-06). Tool surface 43→44, writes=True in REGISTRY, read-only default proven by the behavioral gate.
**Depends on**: 2, 3, 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] clauderize init stamps procedure_version into config.toml; merge_missing preserves it (test)
- [x] cz_modernize default returns a read-only report listing tier-1 mechanical items + tier-2 advisory proposals for a stale-corpus fixture (test)
- [x] cz_modernize apply=true scaffolds mechanics only and provably never writes DECISIONS.md/INVARIANTS.md/LESSONS.md/HARDENING.md or gameplan memory (test)
- [x] Tier-2 detectors fire on fixtures: unwired declared gates, near-dup invariant pair, campaign gameplan without deliverables, loop gameplan without conditions (tests)
- [x] clauderize upgrade subcommand wraps report+apply (test); tool surface 44, parity green, read-only behavioral gate passes for default cz_modernize
- [x] Status/doctor surface one modernization line only when stale or proposals exist; hook output unchanged (tests)
- [x] Full suite green

### Phase 7: Docs & procedure 1.5.0 & version bump

**Goal**: Bump PROCEDURE_VERSION 1.4.0→1.5.0 with a GAMEPLAN-PROCEDURE.md changelog entry and sections for scoped memory (filtering, not shadowing), approval criteria, deliverable entities (with the deliverable≠asset line), standing conditions (host owns cadence), and the modernization pass. Engine version 1.3.1→1.4.0 in pyproject.toml + __init__.py. Refresh the human product docs per D-038/D-039 — README (an "Upgrading delivers improvements" section), UPGRADING.md (clauderize upgrade), ARCHITECTURE.md, VISION.md — human-first prose, no agent jargon (regex sweep per the 1.0.5 lesson); new tool descriptions in plain prose.
**Depends on**: 6.

| Task | Description | Effort |
|------|-------------|--------|
| 7.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] PROCEDURE_VERSION = 1.5.0 with GAMEPLAN-PROCEDURE.md changelog entry covering scoped memory, approval criteria, deliverables, standing conditions, modernization
- [x] pyproject.toml and __init__.py at 1.4.0
- [x] README + UPGRADING.md describe 'clauderize upgrade' in human prose; ARCHITECTURE/VISION refreshed (D-038/D-039)
- [x] Agent-jargon regex sweep of product docs clean (1.0.5 lesson)
- [x] Full suite green

### Phase 8: Dogfood & live verification

**Goal**: Prove the upgrade story on real corpora. This repo: run cz_modernize (report, then apply), verify the ⚙ digest line appears then clears, config stamped 1.5.0. marketing-studio (runs the dev venv, so it picks the build up immediately): clauderize upgrade must scaffold preflight.campaign.toml.example, stamp its config, and its report must propose the real gaps found in the 2026-07-01 analysis — unwired campaign QA gates, the INVARIANT-03/04/05 vs 07/08/09 near-duplicate pairs as scope-tag candidates, campaign gameplans without deliverable entities. INVARIANT-07 checks: single-gameplan digest parity, cold-session hook fires, existing mid-flight gameplans untouched. Full suite green.
**Depends on**: 7.

| Task | Description | Effort |
|------|-------------|--------|
| 8.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] This repo: cz_modernize report → apply → digest modernization line appears then clears; config stamped 1.5.0
- [x] marketing-studio live: clauderize upgrade stamps config 1.5.0 + refreshes the procedure doc; the report proposes the real residual gaps — the INVARIANT-03/08 near-dup pair (Jaccard 0.467) and the stale pre-lifecycle kind overlay (new stale_kind_overlay detector, added with test after the dogfood exposed overlay shadowing; see correction C-03). Wired gates correctly produce silence; subset-shaped pairs deferred to O-04
- [x] marketing-studio mid-flight gameplans unchanged (portfolio digest byte-identical before/after upgrade)
- [x] Cold-session digest parity on this repo (INVARIANT-07): post-upgrade status digest carries no modernization line and standard content
- [x] Full suite green

### Phase 9: Ship 1.4.0 — release ritual & close-out

**Goal**: D-011 ritual end to end: full suite green, release-check exit 0 (four-registry sweep), PR with scrub-verified diff (no PII per D-031), 9-cell CI green BEFORE any tag (L-20), squash-merge to main, tag v1.4.0 on the full merged SHA, GitHub Release (latest, non-prerelease), OIDC publish, PyPI info.version=1.4.0 + uvx --refresh verification. Then close-out: subsystem/feature entity version bumps with cascade resolution, post-mortem with friction log, lesson curation, phase summaries, gameplan closed.
**Depends on**: 8.

| Task | Description | Effort |
|------|-------------|--------|
| 9.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] release-check exit 0 (four-registry sweep)
- [ ] PR opened with PII scrub-verify done; 9-cell CI green BEFORE tag (L-20)
- [ ] Squash-merged to main; tag v1.4.0 on the full merged SHA; GitHub Release latest + non-prerelease; OIDC publish green
- [ ] PyPI info.version = 1.4.0 and uvx --refresh resolves 1.4.0
- [ ] Subsystem/feature entities version-bumped with cascade reports resolved; post-mortem written; gameplan closed
