# concurrent multi-axis gameplans Gameplan

> Created: 2026-06-27
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

### D1 — Two orthogonal data-driven axes: host profile (language) stays, kind (type+skin) is new

**Context**: The word 'profile' already means the LANGUAGE profile (profiles/*.toml -> test/build/lint commands). The user's 'kind/profile' is a DIFFERENT axis (vocabulary + preflight semantics + template). Conflating them would overload a loaded term.
**Decision**: Keep 'host profile' as language-only. Introduce 'kind' (driven|loop|campaign|user-defined) as a second axis with its own data files kinds/*.toml (lexicon + default template + preflight check list), packaged like profiles with a .clauderizer/kinds/ overlay. The two compose: a campaign kind on a python host resolves preflight from the kind (QA gates), not pytest.
**Consequences**: No collision; both axes are pure data (add a kind = a new toml, never an engine change), mirroring the profiles pattern reviewers already know.
**Status**: active (2026-06-27)

### D2 — Focus replaces active via read-fallback migration + alias; open-set is derived, never stored

**Context**: Every write op already resolves its target with 'gid = gameplan_id or config.active_gameplan' — the single pointer is only a default-target, not a storage limit. Storage is already multi-gameplan.
**Decision**: Add Config.focus; on load read [focus].id falling back to legacy [active_gameplan].id (the migration); on write emit [focus]; keep a config.active_gameplan property alias so no call site changes. The 'open set' is DERIVED by scanning each gameplan's GAMEPLAN.md '> Status:' (Planning|Executing = open), not stored. config.extra preservation already prevents dropping fields on rewrite.
**Consequences**: Zero new persistent state for the open-set; old repos migrate transparently; single-gameplan behavior is unchanged because focus == the old active default.
**Status**: active (2026-06-27)

### D3 — Lexicon relabel is DISPLAY-ONLY — on-disk section headings stay canonical

**Context**: status_bundle and sections parse on-disk headings literally (## Phase Breakdown, ### Phase N). Renaming headings in the file would break every parser and test.
**Decision**: Apply kind lexicon (phase->stage, output->asset, ...) ONLY to transient surfaces: render_digest, handoff prose headers, and op-result summary strings. On-disk section headings and op names stay canonical. A campaign's digest says 'Stage 2/5' while the file still says 'Phase'.
**Consequences**: Thin, safe skin; parsers/tests untouched. Truer templated-headings + alias-aware parsers are possible later but were judged not worth the parser destabilization now (user chose display-only).
**Status**: active (2026-06-27)

### D4 — Per-kind preflight = generalized command-gate primitive; engine ships mechanism, user wires policy

**Context**: preflight.run hardcodes tests/build pulling commands from the language Profile. A campaign needs QA gates (virality/brand-lint/duration), not pytest.
**Decision**: Generalize tests/build into one named command-gate: a check whose shell command resolves from .clauderizer/preflight.<kind>.toml (user-wired) else the host profile. The check LIST comes from the focus gameplan's kind definition; config.preflight_checks remains the per-repo override. Unwired gates skip-with-hint (reusing _generic_profile_hint). Pass/fail by exit code, advisory-downgrade preserved.
**Consequences**: Clauderizer ships the run-named-gates mechanism, never the QA logic. driven kind's gate list == today's so behavior is identical; campaign gates are just more entries.
**Status**: active (2026-06-27)

### D5 — Cross-gameplan deps ride the already-project-wide graph; gameplan-node convention, no new cascade op

**Context**: index.build ingests ALL docs/ frontmatter and cz_cascade walks the full graph — cross-gameplan cascade over tracked entities already works; only the report destination is gameplan-scoped. The gap is that gameplan-internal outputs/decisions aren't graph nodes.
**Decision**: Blessed pattern: cross-consumed artifacts become tracked entities (cz_upsert_entity, exists). Represent each gameplan by a lightweight gameplan.<gid> node carrying a consumes list (rendered as depends_on edges) so transitioning a shared entity flags the OTHER gameplan's node — the generic cross-gameplan edge with NO new op. Add cascade fan-out: drop a pending cross-ref into a non-focus affected gameplan's _cascade-reports so its cascade_hygiene catches it.
**Consequences**: Reuses existing graph + cascade; minimal new surface. The exact fan-out form (central report + per-axis pointer vs duplicate) is an open item for Phase 4.
**Status**: active (2026-06-27)

### D6 — Back-compat is proven by a Phase-0 golden snapshot gate, not asserted

**Context**: Zero breakage for single-gameplan repos is the headline constraint. It must be machine-checked, not hoped for.
**Decision**: Phase 0 writes a golden snapshot test asserting a single-gameplan repo's cz_status dict + rendered digest are byte-identical before/after, plus a migration round-trip test ([active_gameplan]-only loads, rewrites to [focus]). This gate must stay green through every later phase. Baseline = 663 tests.
**Consequences**: Any accidental behavior drift fails CI immediately; the back-compat promise is enforced rather than documented.
**Status**: active (2026-06-27)

## Open Items

**O-01.** _(phase 4)_ Cross-gameplan cascade fan-out form: central report in focus gameplan + a per-axis pending pointer, vs a duplicated report per affected gameplan. Decide in Phase 4 (lean: central + pointer to avoid double-resolve).

**O-02.** _(phase 3)_ Preflight check-list precedence when BOTH config.preflight_checks is set AND the kind defines checks: recommend kind-default unless config explicitly overrides — confirm and document in Phase 3.

**O-03.** _(phase 0)_ Implementation branch strategy: branch off main for this initiative rather than continuing on feat/abstract-index-fast-retrieval (which has its own in-flight gameplan). Confirm with user at Phase 1 greenlight.

**O-04.** _(phase 1)_ Should cz_create_gameplan gain a focus=True flag so a new gameplan can be created WITHOUT stealing focus? Minor ergonomic; decide during Phase 1.

## Phase Breakdown

### Phase 0: Bootstrap and back-compat harness

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Baseline test count (663) captured as a Source-of-Truth value
- [x] Golden snapshot test: single-gameplan cz_status dict + rendered digest byte-identical (written and passing)
- [x] Migration round-trip test stub in place ([active_gameplan]-only config loads)
- [x] D1-D6 design decisions recorded in this gameplan
- [x] Implementation branch created off main (not the abstract-index feature branch)

### Phase 1: Focus model (concurrent gameplans + portfolio)

**Goal**: Replace the single active pointer with a focus + derived open-set: Config.focus with [active_gameplan] read-fallback migration and an active_gameplan alias property; cz_focus and cz_gameplans ops; clauderize focus/gameplans CLI verbs; a portfolio block in status_bundle, render_digest, and the SessionStart hook that expands only when >1 gameplan is open.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Config.focus loads via [focus] with [active_gameplan] read-fallback; rewrite emits [focus] and round-trips; config.active_gameplan alias still works
- [ ] cz_focus and cz_gameplans present in BOTH ops.REGISTRY and tools_list.TOOL_NAMES (parity test green)
- [ ] clauderize focus <id> and clauderize gameplans CLI verbs work
- [ ] Portfolio block in status_bundle; render_digest + SessionStart expand it ONLY when >1 gameplan open
- [ ] Golden single-gameplan digest gate still byte-identical
- [ ] Full suite green vs 663 baseline

### Phase 2: Kinds as real profiles (parse + lexicon)

**Goal**: Make kind behavioral: a gameplan_kind() parser reading the > Kind: header (default driven); packaged kinds/*.toml (driven=current behavior, loop, campaign) with a .clauderizer/kinds/ overlay loader mirroring profiles; cz_create_gameplan validates kind and templates first_phase from it; display-only lexicon relabel applied at render_digest, handoff prose, and op summaries ONLY (on-disk section headings stay canonical so parsers/tests are untouched).
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] gameplan_kind() parses > Kind: header, defaults to driven when absent
- [ ] kinds/{driven,loop,campaign}.toml ship; .clauderizer/kinds/ overlay loads (mirrors profiles load_for_repo)
- [ ] cz_create_gameplan validates kind and templates first_phase from it
- [ ] Campaign focus: digest/handoff/summaries show lexicon (Stage/asset) while on-disk headings unchanged AND phase parser still finds phases
- [ ] driven kind reproduces current lexicon exactly (golden gate green)
- [ ] Full suite green vs baseline

### Phase 3: Per-kind / per-gameplan preflight

**Goal**: Generalize the hardcoded tests/build checks into a named command-gate primitive whose command resolves from .clauderizer/preflight.&lt;kind&gt;.toml (user-wired) else the host profile; the check LIST comes from the focus gameplan's kind definition with config.preflight_checks remaining the per-repo override; unwired gates skip-with-hint reusing the existing pattern; cz_preflight resolves the kind from focus. Clauderizer ships the mechanism, never the QA logic.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] Named command-gate primitive runs a wired gate via injected stub runner (pass/fail by exit code)
- [ ] Check list resolves from focus gameplan's kind definition with config.preflight_checks as override
- [ ] Unwired gate skips with an actionable hint; advisory-downgrade still works
- [ ] driven preflight output identical to today (tests/build from host profile)
- [ ] cz_preflight resolves kind from focus
- [ ] Full suite green vs baseline

### Phase 4: Cross-gameplan dependencies and explicit scoping

**Goal**: Make cross-gameplan edges first-class over the already-project-wide graph: a gameplan.&lt;gid&gt; node convention carrying a consumes list (rendered as depends_on edges, reusing cz_upsert_entity, no new op); cascade fan-out that drops a pending cross-ref into a non-focus affected gameplan's _cascade-reports so its cascade_hygiene catches it; a handoff "Consumes (cross-gameplan)" section; document project vs gameplan memory scoping explicitly.
**Depends on**: 1.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] A gameplan.<gid> node with a consumes list produces cross-gameplan cascade dependents on transition of a shared entity
- [ ] A non-focus affected gameplan receives a pending cross-ref its cascade_hygiene preflight catches
- [ ] Handoff renders a Consumes (cross-gameplan) section
- [ ] Project vs gameplan memory scoping documented and surfaced
- [ ] Full suite green vs baseline

### Phase 5: Docs, dogfood, release

**Goal**: Update GAMEPLAN-PROCEDURE, the relevant docs/subsystems pages, and README for focus/kinds/cross-gameplan; dogfood a SECOND concurrent gameplan (a campaign kind) on an ISOLATED repo copy (L-29) proving two axes advance independently with correct per-kind preflight + portfolio; run the full D-011 release ritual and cut a minor version. Spaces (Feature 4) is explicitly out of scope.
**Depends on**: 3, 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] GAMEPLAN-PROCEDURE, relevant docs/subsystems pages, and README updated for focus/kinds/cross-gameplan
- [ ] Dogfood on an ISOLATED repo copy (L-29): two concurrent gameplans (one campaign kind) advance independently with correct per-kind preflight and portfolio
- [ ] Full D-011 release ritual green (release-check 0, CI matrix green, tag, GitHub Release, publish)
- [ ] Minor version bumped and verified on PyPI
- [ ] Spaces (Feature 4) confirmed out of scope / noted as future
