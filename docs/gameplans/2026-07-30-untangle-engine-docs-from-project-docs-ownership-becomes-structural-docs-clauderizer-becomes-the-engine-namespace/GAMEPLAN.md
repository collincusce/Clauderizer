# Untangle engine docs from project docs — ownership becomes structural, docs/clauderizer/ becomes the engine namespace Gameplan

> Created: 2026-07-30
> Status: Planning
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

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase 0)_ BACKWARD COMPAT is the real hazard, not forward. An older engine (2.0.0, procedure 1.13.0) opening a migrated repo resolves docs/DECISIONS.md via paths.doc(), finds nothing, and reports an EMPTY corpus rather than an error — silent total memory loss from its perspective, in exactly the mixed-version situation a team or a stale uvx cache produces. Proposed mitigation is to bump PROCEDURE_VERSION 1.x -> 2.0.0 so the existing doctor MAJOR-mismatch check fires loudly ("upgrade this install") instead. MUST be verified by actually running a 2.0.0 engine against a migrated fixture and observing what the digest and doctor say — not assumed. If the old engine stays silent, the migration needs a stronger gate (e.g. a legacy stub file at each old path pointing at the new location).

**O-02.** _(phase 0)_ D-039 places GAMEPLAN-PROCEDURE.md in the PRODUCT layer (a human reads it to evaluate the methodology), but in a CONSUMER repo it is engine-shipped reference the human rarely opens, and it already lives under docs/gameplans/. Decide per-context rather than globally: in the Clauderizer repo it is a product doc; in a consumer repo it is engine state. Resolve before P3 moves anything, since it determines whether docs/gameplans/ as a whole relocates under docs/clauderizer/ or stays put.

## Phase Breakdown

### Phase 0: Record the law — ownership taxonomy, the D-039 realization, and the compat gate

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] D-080 recorded as the filesystem realization of D-039 (extends, does not supersede — the two-layer taxonomy stands)
- [ ] O-01 backward-compat hazard resolved with a MEASURED answer: a real 2.0.0 engine run against a migrated fixture, with the observed digest and doctor output recorded verbatim
- [ ] O-02 resolved: docs/gameplans/ either relocates under docs/clauderizer/ or stays, decided per-context with the reason written down
- [ ] The owner taxonomy is written down as an explicit table (engine-owned / engine-schema-user-content / project-owned) naming every one of the 17 templated doc names
- [ ] A decision recorded on release shape: whether the breaking path change ships as 2.1.0 with auto-migration or as 3.0.0
- [ ] The five-repo collision survey is committed as the evidence artifact behind D-080, not left in a chat transcript

### Phase 1: Ownership becomes structural — the identity default

**Goal**: Give every doc a structural OWNER (engine | project) that the engine reasons about, and route paths.doc() through an owner lookup — with the identity default being the LEGACY location, so the whole generalization lands with zero behavior change and no file moves (L-41). Split SIZE_MANIFESTS into engine docs vs optional project seeds without changing what any existing repo gets yet.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Every doc has a structural owner the engine can query; no caller infers ownership from a filename
- [ ] paths.doc() routes through the owner lookup, and the identity default resolves to the LEGACY location
- [ ] A byte-identical golden of the status digest, a written handoff, and cz_status stays green across the whole phase — the L-41 proof that the generalization changed nothing yet
- [ ] Zero files moved in this phase, asserted by a test
- [ ] SIZE_MANIFESTS split into engine docs vs opt-in project seeds, with every existing repo still resolving exactly the set it resolves today
- [ ] Suite green with the new ownership tests armed red first

### Phase 2: Two glossaries, and the engine stops claiming names

**Goal**: Author the engine GLOSSARY as Clauderizer vocabulary (gameplan, phase, cascade, invariant, handoff, hub-and-spoke, deferred, negative-space) distinct from any project glossary; demote the generic-name templates (ARCHITECTURE, SECURITY, VISION, TESTING, SCHEMA, DEPLOYMENT, REQUIREMENTS, INCIDENTS, DATASOURCES, ENGINEERING-PRINCIPLES) from default scaffolds to opt-in project seeds; and scope 2.0.0's ensure_modules_current to ENGINE docs only, so the upgrade action stops reaching for names in the project's namespace.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 3: The untangle — classify, git mv, conserve every entry

**Goal**: Build the migration itself: classify each engine-named doc (still-an-untouched-template => engine's, move it; seeded with real content => project's, leave it exactly where it is and write a fresh engine doc alongside), move with git mv so history survives, never split or merge a file, and assert entry-count conservation across the move (INVARIANT-03). Idempotent and resumable; a --dry-run report that names every file and its verdict before anything is written.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Classifier proven both ways on real files: an untouched template is moved, a user-seeded doc with the same name is left byte-identical in place
- [ ] Entry-count conservation asserted across every migration (decisions, invariants, lessons, findings counted before and after — INVARIANT-03)
- [ ] History survives: git log --follow on a moved doc reaches its pre-migration commits
- [ ] No file is ever split, merged, or rewritten by the migration — only moved or newly created
- [ ] Idempotent: a second run reports 0 actions; resumable: an interrupted run leaves a state the next run completes rather than corrupts
- [ ] --dry-run names every file and its verdict before anything is written, and its plan matches what a real run then does
- [ ] Armed red first against a fixture repo built from a real pre-migration corpus

### Phase 4: Wire it to upgrade, and make an old engine say "upgrade" instead of "empty"

**Goal**: Run the untangle automatically from clauderize upgrade (the chosen posture) as a reported, reversible tier-1 action, and close the backward-compat hazard O-01 names: bump PROCEDURE_VERSION to 2.0.0 so an older engine's MAJOR-mismatch check fires loudly rather than silently reporting an empty corpus — VERIFIED by running a real 2.0.0 engine against a migrated fixture, not assumed. Add the doctor check that the layout matches the declared ownership.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 5: The 72 prose references — every surface that tells an agent where memory lives

**Goal**: Sweep the agent-facing and human-facing prose that hardcodes docs/ paths: the shipped stanza, all clauderizer-* skills, templates, README, UPGRADING, TRUST, TROUBLESHOOTING, and the tool descriptions. Pin the seam executably per L-65 — a test diffing referenced paths against the owner map — rather than sweep discipline. Append-only gameplan handoffs are explicitly NOT rewritten.
**Depends on**: 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_

### Phase 6: Prove it on the real corpus, then ship

**Goal**: Acceptance on the six real repos that motivated this (Clauderizer, viderizer, phasekeep, clauderizer-site, marketing-studio, arena-security-audit): migrate each, confirm every digest still renders and every entry survives, confirm each project's own docs were left untouched, and confirm viderizer ends with a film glossary AND an engine glossary rather than one confused file. Then release, with the CHANGELOG stating the breaking path change and the compat gate plainly.
**Depends on**: 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] _(verifiable)_
