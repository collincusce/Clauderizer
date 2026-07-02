# engine-1.5.0-onboarding Gameplan

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

### D1 — 1.5.0 release shape: engine 1.5.0 carries procedure 1.6.0; lean five-phase arc

**Context**: Engine at 1.4.1 (main @ 27df365), procedure 1.5.0, suite 755, surface 44. The engine version is about to numerically pass the procedure line it carries — the exact near-collision the 1.4.1 wording patch disambiguated.
**Decision**: Ship as engine MINOR 1.5.0 carrying procedure 1.6.0 (MINOR: a new "Onboarding an existing project" section + changelog; no structural change). Docs and release notes always name both lines explicitly using the 1.4.1 "carries" phrasing. Five phases: plan/commit → detector + cz_onboard → init/modernize surfacing → skill + docs + version bumps → dogfood (a fresh scratch repo with real specs = the unseeded case, plus both live corpora for no-false-fire) and the D-011 ship ritual with 9-cell CI before tag.
**Consequences**: The version pairing flips direction (engine ahead of procedure numerically becomes engine 1.5.0 / procedure 1.6.0) — the carries wording and the CHANGELOG must keep it unambiguous. Suite grows by detector/tool/surfacing/skill tests; surface 44→45 with CLI parity.
**Evidence**: pyproject 1.4.1 @ main 27df365; PROCEDURE_VERSION 1.5.0; suite 755 (1.4.1 CI); tools_list 44
**Status**: active (2026-07-01)

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Plan, baselines & commit

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] D-044 project ADR + D1 gameplan decision recorded; feat.onboarding entity upserted
- [x] Baselines: engine 1.4.1 @ main 27df365, procedure 1.5.0, surface 44, suite 755 confirmed by green preflight
- [x] Plan committed on a feature branch; tree clean

### Phase 1: Detector + cz_onboard assembly tool

**Goal**: New src/clauderizer/onboard.py: spec_candidates(paths) — README.md plus root ARCHITECTURE/DESIGN/SPEC*-style markdown plus docs/**/*.md outside the Clauderizer-owned set (owned = the template doc names, gameplans/, features/, subsystems/, datasources/, capabilities/, entities/, plans/), returning path + size only, capped at 25, skipping files over 2 MB; unseeded_docs(paths) — enabled-module docs whose every non-heading, non-blank body line is a sections.is_placeholder line (structure test, never byte-identity). cz_onboard (read-only, ops + tools_list, surface 44→45): {unseeded, candidates, seeded_count, prompt} where the prompt names the blessed writes and the provenance discipline. Tests: owned-set exclusion, caps, placeholder vs seeded detection across template evolution, tool registry parity, CLI parity via clauderize ops --schema.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] spec_candidates excludes every Clauderizer-owned doc/dir, caps at 25, skips >2MB, returns paths+sizes only (tests)
- [x] unseeded_docs flags placeholder-only docs and clears once a doc has real prose; robust to template text drift (structure test, not byte-identity) (tests)
- [x] cz_onboard read-only with {unseeded, candidates, seeded_count, prompt}; surface 45, registry parity green, clauderize ops --schema shows it (L-05)
- [x] Full suite green

### Phase 2: Surfacing — init advisory + modernize proposal

**Goal**: init: after the doc-scaffold step, when unseeded docs AND spec candidates coexist, the report prints one advisory naming the counts and the next step (cz_onboard / the clauderizer-onboard skill) — no advisory on an empty or already-seeded repo. modernize tier-2: a new "unseeded_docs" proposal with the same predicate so every already-clauderized repo learns about onboarding at its next clauderize upgrade (D-042); no proposal when docs are seeded or no candidates exist. Tests both ways for both surfaces.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] init report prints one onboarding advisory when unseeded docs + candidates coexist; silent otherwise (tests both ways)
- [ ] modernize tier-2 gains unseeded_docs proposal with the same predicate; silent when seeded or no candidates (tests both ways)
- [ ] Full suite green

### Phase 3: Skill + docs + version bumps

**Goal**: Package a clauderizer-onboard skill (assets skills dir, shipped by init like the other six): trigger = onboarding/seeding an existing project's docs; body = run cz_onboard → read each candidate → seed VISION/ARCHITECTURE prose directly → cz_upsert_entity the real subsystems/features → cz_add_decision/cz_add_invariant with provenance naming the source file → re-run cz_onboard to confirm seeded → cz_status. Procedure template: 1.5.0→1.6.0 with changelog + an "Onboarding an existing project" section in human prose. Engine 1.4.1→1.5.0 (pyproject + __init__), CHANGELOG entry naming BOTH version lines with the carries phrasing, README init section gains one onboarding sentence. Jargon sweep clean; venv reinstall; suite green.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] clauderizer-onboard skill ships in the packaged skills and init drops it (test)
- [ ] Procedure template at 1.6.0 with changelog + Onboarding section; engine 1.5.0 in pyproject + __init__; CHANGELOG names both version lines with the carries phrasing
- [ ] Jargon sweep clean; venv reinstalled; full suite green

### Phase 4: Dogfood & ship 1.5.0

**Goal**: Dogfood three ways: (1) a scratch repo with a real README + docs/design.md → clauderize init prints the onboarding advisory and cz_onboard lists both files with the docs unseeded; (2) this repo → no false fire (docs seeded), upgrade stamps procedure 1.6.0 + refreshes the procedure doc; (3) marketing-studio → its STUDIO/CAMPAIGN/EXECUTION-PATTERN docs appear as candidates but no unseeded-docs proposal (their VISION/ARCHITECTURE are real). Then the D-011 ritual: suite green, PII sweep, PR, 9-cell CI green BEFORE tag, squash-merge, release-check 0, tag v1.5.0 full SHA, GitHub Release latest, OIDC publish, PyPI info.version=1.5.0 + uvx --refresh verified; close-out (entities, post-mortem, lessons, focus handback).
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Scratch spec-rich repo: init prints the onboarding advisory and cz_onboard lists README + docs/design.md with unseeded VISION/ARCHITECTURE (live)
- [ ] This repo and marketing-studio: no false onboarding fire; upgrade stamps procedure 1.6.0 (live)
- [ ] D-011 ritual complete: PII sweep, PR, 9-cell CI green pre-tag, squash-merge, release-check 0, tag v1.5.0 full SHA, Release latest, OIDC publish green, PyPI 1.5.0 + uvx --refresh verified
- [ ] Close-out: entities bumped, post-mortem written, focus handed back, gameplan closed
