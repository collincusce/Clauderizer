# integrity-patch Gameplan

> Created: 2026-06-28
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

### A-001 — Phase-1 "fork hid pairs" expectation falsified by Phase-0 data; threshold recalibration redirected to 0.40 alignment

- **Date**: 2026-06-28
- **Affected sections in GAMEPLAN.md**: Phase 1 goal + exit criteria; Open Item O-01
- **Affected phases**: 1
- **Triggered by**: Phase-0 measurement (output redundancy_measurement / divergence_finding)
- **What changed**: The Phase-1 goal sentence "cz_corpus_health ... should surface real near-duplicate pairs in the 30-lesson bloat that the fork hid" does NOT hold: the canonical analyze._tokens yields 0 redundant pairs over the real 30-lesson corpus at EVERY threshold from 0.3 to 0.7 (max pairwise Jaccard 0.19). The tokenizer-unification still proceeds (D-041, the real fix), but its effect is coherence — one tokenizer basis shared with analyze.near_duplicate_lessons + the abstract index — NOT a jump in the reported pair count (which stays 0, correctly). O-01 recalibration resolves to: import analyze._LESSON_DUP_JACCARD (0.40) into telemetry so corpus_health/curate use ONE near-duplicate definition with the write-time advisory; 0 false positives on the real corpus at 0.40.
- **Why**: Fixture-first discipline (L-39/L-40): the audit's predicted under-counting symptom was an assumption; measurement proved the defect is incoherence (two tokenizer+threshold definitions of near-duplicate), not under-reporting. Recording this so Phase 1's exit criterion "post-fix redundancy count surfaces real pairs" is read as "shares the canonical tokenizer+threshold basis (count stays an honest 0)", not as a target to manufacture.

## Decisions

### D1 — Tests must assert runtime behavior, not module-load constants

**Context**: The integrity check found ~5 tautological tests that assert immutable module-load constants and pass regardless of what the function does at runtime: `assert ops.REGISTRY[x].writes is False` + `fn.__name__ == ...` in test_lesson_health.py:86, test_loop_gameplan.py:101, test_curator.py:75, test_skill_discovery.py:105, test_analyze.py:273. They inflate the count and give false confidence; the real read-only/parity guarantees live in test_ops.py (REGISTRY==TOOL_NAMES + the AST signature-drift guard). Plus test_mcp_tools.py:38 guards only a stale 16-of-42 tool subset.
**Decision**: A test that claims a property must EXERCISE it. "Read-only" is proven by snapshotting the repo and asserting no tracked file changed across a real call (the test_hook_dispatch read-only-snapshot pattern), not by asserting a registry flag. Replace each tautological writes-is-False/__name__ assertion with a behavioral one, or delete it where the real gate already covers it (keep test_ops.py's parity + signature-drift guard as the single source). Upgrade test_mcp_tools to the full 42-tool surface (or fold into the test_ops parity gate). No test added in this gameplan may assert only a module-load constant.
**Consequences**: The suite's green stops over-counting trivially-true assertions and starts reflecting real behavior. Slightly fewer tests, each load-bearing. Two genuine coverage gaps get filled (the SessionStart digest tool-list advertisement; the per-kind preflight command-gate subprocess path).
**Evidence**: tests/test_lesson_health.py:86, test_loop_gameplan.py:101, test_curator.py:75, test_skill_discovery.py:105, test_analyze.py:273, test_mcp_tools.py:38; the real gate test_ops.py:55/117; v1.3.0 integrity audit
**Status**: active (2026-06-28)

### D2 — Patch, not minor — no user-facing behavior regression; targets 1.3.1

**Context**: This gameplan fixes coherence/test/docs findings from the v1.3.0 integrity audit. It adds no features and no new tools (surface stays 42). The only behavioral shift is internal + advisory: unifying the tokenizer changes what cz_corpus_health's redundancy metric reports (D-041) — but that is an advisory health tool (INVARIANT-05), and the shift is measured + intended.
**Decision**: Version bump is a PATCH: 1.3.0 -> 1.3.1. No user-facing behavior may regress; the suite stays green; the tool surface stays 42 (no TOOL_NAMES/REGISTRY change). Release via the D-011 ritual (release-check exit 0, push-then-release, 9-cell CI green on the release commit, tag v1.3.1, GitHub Release, PyPI via Trusted Publishing, verify uvx --refresh + PyPI). The merge to main follows the abstract-index precedent (PR, CI-green, merge-ready, release handed to the user — INVARIANT-07).
**Consequences**: Scope discipline: anything that would change a user-facing contract or add a tool is out of scope (defer to a minor). The corpus-health output change is documented in the CHANGELOG as a fix, not a feature.
**Evidence**: D-011 release ritual (docs/RELEASING.md); the 1.3.0 release precedent (PR #16); INVARIANT-07; tool surface 42 (tools_list.TOOL_NAMES)
**Status**: active (2026-06-28)

## Open Items

**O-01.** Threshold recalibration (Phase 1): does corpus_health._REDUNDANCY_THRESHOLD (currently 0.6, tuned for the stopword-keeping fork) need a new value once routed through the canonical analyze._tokens? Decide from the Phase-0 before/after Jaccard distribution — keep 0.6 only if the data supports it; otherwise recalibrate and record why. Resolves into a Phase-1 decision/output.

**O-02.** Campaign preflight false-green (Phase 2, finding #6a): pick the fix for kinds/campaign.toml declaring virality/brand_lint/duration gates with no shipped wiring — (a) loud-warn in preflight/doctor that declared gates are unwired, (b) ship an example .clauderizer/preflight.campaign.toml, or both. Constraint: a campaign gameplan must not read green on gates that never ran. Resolves into the Phase-2 implementation + test.

**O-03.** Digest tool-advertisement testability (Phase 3, finding #3a): confirm where the SessionStart digest renders its advertised tool list (status_bundle.render_digest / the digest assembler) and that it reflects the passed-in tool names, so the new test can assert advertised-list == TOOL_NAMES rather than a hardcoded copy. If the digest derives the list indirectly, decide the right seam to assert. Resolves into the Phase-3 test.

**O-04.** Promote D-041 to an INVARIANT? (Phase 5): once one-canonical-tokenizer is enforced by the Phase-1 guard test, decide whether \"all lexical-overlap/similarity computations use the single analyze._tokens tokenizer\" graduates from a project decision (D-041) to a numbered INVARIANT (INVARIANT-09). Lean yes if the guard test makes it a hard, machine-checked rule; record the rationale either way.

## Phase Breakdown

### Phase 0: Branch, baseline, and measure the tokenizer divergence

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Branch fix/integrity-patch exists off main and the working tree is clean after the plan commit
- [x] Baseline suite count is captured and recorded as a gameplan output (expected 711 passed / 4 skipped)
- [x] A reproducible measurement records cz_corpus_health's redundancy-pair count BEFORE the fix (fork tokenizer) AND the count the canonical analyze._tokens would yield over the same 30-lesson corpus — both numbers recorded as outputs (fixture-first, L-39/L-40)
- [x] The divergence is demonstrated, not assumed: the measurement shows whether the fork under-reports (the predicted symptom) and by how much

### Phase 1: Unify the canonical tokenizer

**Goal**: Resolve the keystone finding (D-041). Replace the divergent telemetry._tokens (src/clauderizer/telemetry.py:108) with an import of the canonical analyze._tokens, and route corpus_health._jaccard (the redundancy metric behind cz_corpus_health / cz_lesson_health / cz_curate / cz_loop_step) through it. Using the Phase-0 before/after measurement, RECALIBRATE _REDUNDANCY_THRESHOLD against the canonical tokenizer (it was tuned for the stopword-keeping fork) — pick the value from the data, not taste (resolves the threshold open item). Add a guard test that there is exactly ONE token-splitter in src/ (corpus_health/telemetry use analyze._tokens), so a second fork cannot reappear. Re-run cz_corpus_health and confirm its redundancy count now shares the dedup-advisory basis (it should surface real near-duplicate pairs in the 30-lesson bloat that the fork hid). No user-facing behavior change beyond the advisory redundancy output (D2). Watch INVARIANT-06: corpus_health is reached by cz_* read ops, not a hook, so analyze._tokens is fine here.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] telemetry.py no longer defines its own token splitter; corpus_health._jaccard tokenizes via the canonical analyze._tokens
- [ ] A guard test asserts there is exactly ONE token-splitter definition in src/ (corpus_health/telemetry route through analyze._tokens) — a second fork makes the test fail
- [ ] _REDUNDANCY_THRESHOLD is set from the Phase-0 data (kept or recalibrated), with the chosen value justified by the measured distribution and recorded as a decision/output
- [ ] cz_corpus_health's post-fix redundancy count is recorded and shares the same tokenizer basis as analyze.near_duplicate_lessons (Phase-5 advisory) and the abstract index token_set
- [ ] Full suite green; no user-facing behavior change beyond the advisory redundancy output (D2)

### Phase 2: Code coherence and small traps

**Goal**: Fix the remaining src/ coherence + robustness findings, each with a test. (a, #5) Single-source the L-NN lesson-line grammar: handoff.py:155 (_PROJECT_LESSON_NUM_RE + its parse) reuses abstract_index.parse_lesson_line / one shared regex instead of a copy; add a test that the index path and the handoff path agree on the same line. (b, #6a) campaign.toml preflight gates (virality/brand_lint/duration) silently skip when unwired = false-green; resolve the open item — loud-warn in preflight/doctor that declared gates are unwired, and/or ship an example .clauderizer/preflight.campaign.toml — so a campaign gameplan can't read green on gates that never ran. (c, #6b) analyze.suggest_edges is O(n^2) over all entities and runs on every cz_analyze incl. the hot UserPromptSubmit hook path — add a size guard (skip/cap before the pair loop) so a large entity graph doesn't tax the hook (INVARIANT-06 hot path). (d, #6c) cz_get is writes=False but get_entry -> abstract_index.load_or_rebuild may write the disposable cache (consistent with cz_graph_query, INVARIANT-01) — add a one-line clarifying comment AND a test asserting cz_get mutates no tracked markdown (only the gitignored cache may change). No tool-surface change.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] handoff.py parses L-NN lesson lines via the single shared abstract_index regex/parse_lesson_line (no duplicate _PROJECT_LESSON_NUM_RE); a test asserts the index path and handoff path agree on the same input
- [ ] A campaign gameplan can no longer read green on unwired preflight gates: preflight/doctor loud-warns on declared-but-unwired gates and/or an example .clauderizer/preflight.campaign.toml ships — covered by a test
- [ ] analyze.suggest_edges has a size guard (skip/cap before the O(n^2) pair loop) so the UserPromptSubmit hot path is bounded on a large entity graph — covered by a test
- [ ] cz_get carries a one-line comment explaining the writes=False vs disposable-cache-write distinction, AND a test asserts cz_get mutates no tracked markdown (only the gitignored cache may change)
- [ ] Full suite green; tool surface unchanged at 42

### Phase 3: Test integrity

**Goal**: Make the suite reflect behavior, not module-load constants (D1, #3). Replace the ~5 tautological writes-is-False/__name__ tests (test_lesson_health.py:86, test_loop_gameplan.py:101, test_curator.py:75, test_skill_discovery.py:105, test_analyze.py:273) with BEHAVIORAL read-only assertions (snapshot the repo, call the op, assert no tracked file changed — the test_hook_dispatch read-only-snapshot pattern), or delete the redundant ones where test_ops.py's parity + AST signature-drift guard already covers them. Fix test_mcp_tools.py:38 (stale hardcoded 16-of-42 subset) to assert the full surface or fold it into the test_ops parity gate. Fix the stale '24/24' comment at test_ops.py:56 (it's 42). ADD the two genuinely-missing tests: (a) the SessionStart digest's advertised tool list == TOOL_NAMES (resolve the open item — confirm status_bundle.render_digest's tool section reflects the passed list, then assert it); (b) the per-kind preflight command-gate via a REAL subprocess (not the fake runner) — exit-code->status mapping, output handling, and wired/unwired/advisory ordering in one check list. Scrub the PII path (#4): test_diverse_robustness.py:262 — remove the hardcoded /mnt/c/Users/<username>/... home path (the literal username is PII, and it skips on any other machine); make the skip portable + username-free.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] The ~5 tautological writes-is-False/__name__ tests (test_lesson_health.py:86, test_loop_gameplan.py:101, test_curator.py:75, test_skill_discovery.py:105, test_analyze.py:273) are replaced with behavioral read-only assertions or removed where test_ops.py's parity+signature-drift gate already covers them
- [ ] test_mcp_tools.py:38 asserts the full 42-tool surface (or is folded into the test_ops parity gate); the stale '24/24' comment at test_ops.py:56 reads 42
- [ ] New test: the SessionStart digest's advertised tool list equals TOOL_NAMES
- [ ] New test: per-kind preflight command-gate exercised via a REAL subprocess (not the fake runner) — exit-code→status mapping, output, and wired/unwired/advisory ordering
- [ ] test_diverse_robustness.py:262 no longer contains any home-dir/username literal; the skip is portable (passes/skips correctly on a machine without that path) and a grep for the username across tests/ returns nothing
- [ ] Full suite green

### Phase 4: Docs refresh to 1.3.0

**Goal**: Close the documentation drift (#2, the L-21 non-single-sourced-doc sweep). Update docs/ARCHITECTURE.md (frozen ~0.15.0) and docs/VISION.md (pre-1.2.0) to reflect what shipped: 1.2.0 (concurrent / multi-axis gameplans, kinds = driven/loop/campaign, cz_focus / cz_gameplans / cz_consumes, cross-gameplan dependencies, focus+portfolio) and 1.3.0 (the abstract index, cz_get addressable fetch, abstracts on cz_analyze, the write-time near-duplicate-lesson advisory). Bump the stale frontmatter version in docs/subsystems/mcp-server.md (currently 0.5.0; body already lists 42 tools). Add cz_resolve_finding to the README mutations listing (its pair cz_add_finding is listed; the 42 count is already correct). Human-first prose, no agent-shorthand in visible text (D-038/D-039); leave the single-sourced CLAUDE.md/AGENTS.md stanza (L-16) untouched. Docs-only — no src/ or test change, so the suite count is unchanged.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] docs/ARCHITECTURE.md and docs/VISION.md both describe the 1.2.0 feature set (concurrent/multi-axis gameplans, kinds driven/loop/campaign, cz_focus/cz_gameplans/cz_consumes, cross-gameplan deps) and the 1.3.0 feature set (abstract index, cz_get, abstracts on cz_analyze, write-time dedup advisory)
- [ ] docs/subsystems/mcp-server.md frontmatter version no longer reads 0.5.0 (reflects the current release)
- [ ] README mutations listing includes cz_resolve_finding alongside cz_add_finding; the 42-tool count stays correct
- [ ] Change is docs-only: no diff under src/ or tests/, and the suite count is unchanged from Phase 3
- [ ] Visible doc prose stays human-first (D-038/D-039); the single-sourced CLAUDE.md/AGENTS.md stanza (L-16) is untouched

### Phase 5: Close and 1.3.1 patch release

**Goal**: Land the hardening as a patch (D2, D-011 ritual). cz_preflight green; run the suite on the 9-cell CI matrix (D-012/L-31 — every host leg before the irreversible publish). Then stage 1.3.1: bump pyproject.toml + src/clauderizer/__init__.py __version__, write the CHANGELOG entry framing the tokenizer-unify as a FIX (corpus-health redundancy now uses the canonical tokenizer) plus the docs/test hardening, refresh the editable install (L-19). Push-then-release (origin/main holds the commit BEFORE the tag — L-20 ordering), release-check exit 0 (four-registry sweep), tag v1.3.1 against the pushed commit (not a short SHA — that 422'd last time, L-46 candidate), GitHub Release (latest, non-prerelease), Publish-to-PyPI via Trusted Publishing/OIDC, verify uvx --refresh -> 1.3.1 and PyPI info.version=1.3.1. Merge via a CI-green PR (abstract-index PR #16 precedent). The release itself is HANDED TO THE USER (INVARIANT-07) unless they say go. Post-mortem; promote any enduring lesson; DECIDE whether to promote D-041 (one canonical tokenizer) to an INVARIANT now that it's enforced by a guard test. Close the gameplan and clear the focus pointer. Flag the unblock: with the tokenizer unified + cz_corpus_health trustworthy, the standing-curator-loop gameplan can now do the 30-lesson bloat consolidation on a sound redundancy basis.
**Depends on**: 1, 2, 3, 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_preflight green and the 9-cell CI matrix green on the release commit (D-012/L-31)
- [ ] Version is 1.3.1 in both pyproject.toml and src/clauderizer/__init__.py; CHANGELOG.md has a 1.3.1 entry framing the tokenizer-unify as a fix plus the docs/test hardening
- [ ] release-check exits 0 (four-registry sweep); tag v1.3.1 is on the pushed commit; GitHub Release is latest + non-prerelease
- [ ] PyPI info.version=1.3.1 and uvx --refresh resolves to 1.3.1 (release performed only on the user's go — INVARIANT-07)
- [ ] A decision records whether D-041 (one canonical tokenizer) is promoted to an INVARIANT now that a guard test enforces it
- [ ] Post-mortem written; the gameplan is closed and the focus pointer cleared; the standing-curator-loop unblock (trustworthy cz_corpus_health) is flagged
