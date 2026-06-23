# product-doc-deconflation Gameplan

> Created: 2026-06-23
> Status: Complete
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

### D1 — Operational jargon rule for the layer-2 product-doc audit

**Context**: D-039 mandates two doc layers and bans internal cross-reference IDs from layer-2 human product prose, but gives no mechanical test for what counts. A recon pass on 2026-06-23 disagreed on whether INVARIANT-NN is jargon (one reader treated it as allowed public vocabulary). The audit needs one crisp, reproducible rule so the sweep is mechanical, not a matter of taste.
**Decision**: In layer-2 VISIBLE RENDERED PROSE, ban these ID patterns: D-<n>, H-<n>, INVARIANT-<n>, L-<n>, O-<n>, C-<n>, and gate IDs (e.g. G6) / phase-internal D-k. INVARIANT-NN IS banned here (resolving the ambiguity) — state the rule in plain words instead of citing its number. ALLOW public product vocabulary: gameplan, handoff, cascade, phase, exit criteria, preflight, baseline, plus every cz_* tool name and clauderize CLI verb. EXEMPT machine affordances per D-038: IDs inside HTML comments, YAML frontmatter, and markdown anchors/link targets stay untouched. Referencing a tracker FILE by path (e.g. docs/HARDENING.md) is allowed; citing its internal IDs is not.
**Consequences**: The sweep becomes a regex over visible prose for the banned patterns, excluding comment/frontmatter/anchor regions. Each hit is rewritten to the plain rule or fact it encodes. The rule is reusable; promote to a project decision at close-out if it proves enduring.
**Evidence**: Recon 2026-06-23: docs/TRUST.md (O-02, D-031, O-06, INVARIANT-06), UPGRADING.md (H-09, H-08), TROUBLESHOOTING.md (H-08 x2, H-01..H-09), GAMEPLAN-PROCEDURE.md (L-05, INVARIANT-05/06/13) carry IDs in visible prose.
**Status**: active (2026-06-23)

### D2 — Scope boundary — rectify layer-2 surfaces incl. cz_* tool descriptions; leave layer-1 artifacts verbatim

**Context**: This gameplan is meta-dogfooding: Clauderizer manages an audit of Clauderizer's own docs. Two symmetric risks: (a) over-reach — an execution session 'cleaning up' the dense shorthand in gameplans/handoffs/tracked logs, which is CORRECT per D-039 layer-1 and must NOT be touched; (b) under-reach — skipping the cz_* tool-description strings, which live in source code but are human-facing product docs the user explicitly named in the goal.
**Decision**: IN SCOPE (layer-2, rectify to plain prose + fix drift): README.md, SECURITY.md, docs/TRUST.md, docs/UPGRADING.md, docs/TROUBLESHOOTING.md, docs/gameplans/GAMEPLAN-PROCEDURE.md, the cz_* tool DESCRIPTION strings in src/, and the clauderize --help text. Tool descriptions are edited as DOCS not logic: only description/docstring strings change, no control flow; the full suite must stay green at baseline (602) as the gate. OUT OF SCOPE (layer-1, leave byte-for-byte apart from this gameplan's own normal cz_* tracking writes): every gameplan GAMEPLAN.md / handoff / phase-status / cascade-report, and the append-only tracked logs DECISIONS.md, INVARIANTS.md, LESSONS.md, HARDENING.md (their IDs are the schema, not prose to prettify).
**Consequences**: Rectification never edits a gameplan or handoff. Editing tool descriptions requires a green-test preflight (Phase 4). The final work commit contains only layer-2 files plus this gameplan's own tracking writes.
**Evidence**: User goal 2026-06-23 enumerates the layer-2 surfaces incl. 'the cz_* tool descriptions'. Recon: the cz_analyze description string in src cites D-016/D-018/INVARIANT-05.
**Status**: active (2026-06-23)

## Open Items

**O-01.** _(phase 2)_ README MCP-surface tool list (the enumeration + the "38 tools" summary line, ~README.md:382) is not single-sourced from tools_list.py (lesson L-21). This gameplan reconciles the count/enumeration by hand against ground truth (38 tools). A durable fix — a parity test asserting the README list against TOOL_NAMES, or generating the section — is a separate engine task, out of scope here.

**O-02.** Prior gameplan 2026-06-23-dogfood-followup-findings is COMPLETE (8/8 phases) but not formally closed out (no post-mortem / final cascade). Creating this gameplan made it inactive; decide whether to write its post-mortem before or after this gameplan closes, so it is not silently dropped. _(resolved 2026-06-23: Closed out in a parallel session 2026-06-23 (commit 5ddb32e: post-mortem on disk, active_gameplan cleared). No longer pending.)_

**O-03.** _(phase 5)_ Final sweep found user-facing CLI RUNTIME OUTPUT messages leak internal IDs — concretely, `clauderize release-check`'s RED branch prints "...until every X is resolved (L-08)." (src/clauderizer/cli.py cmd_release_check, ~L363). This is a related but SEPARATE surface from the scoped "clauderize --help text" (D2): runtime output messages (release-check, and likely doctor verdicts + release_check.py check labels/details) were not in the layer-2 list. NOT fixed here, to respect the gameplan's scope boundary and avoid a half-done expansion. Recommend a focused follow-up sweep of all CLI output paths. _(resolved 2026-06-23: Addressed in the 1.1.0 harden/fix pass (2026-06-23): scrubbed internal-ID leaks from user-facing CLI output — release_check.py check details (H-07 x2 + G7) and cli.py's release-check RED message (L-08). Doctor verdicts checked, already clean. Tests updated (test_release_check.py asserts ID-free substrings "drifted"/"skewed"); suite green at 619.)_

**O-04.** _(phase 5)_ Cold fresh-human-reader pass (Phase 5) flagged comprehension gaps that are OUT OF SCOPE for this gameplan (concept-definition completeness, not internal-ID jargon or dogfood/engine conflation): SECURITY.md & TRUST.md assume the reader knows "MCP server" / "hooks" / "agent harness" / "key-merge" without defining them (reader gave both a "no" newcomer-verdict on that basis); TROUBLESHOOTING.md introduces the "[Clauderizer]" stdout breadcrumb late; README's "1.0 readiness gates" is vague without RELEASING.md. Recommend a future "novice onboarding / concept glossary" doc-polish pass. The gameplan's actual goal (zero unexplained internal IDs) was VERIFIED ACHIEVED by the same pass; these are a different quality axis.

## Phase Breakdown

### Phase 0: Bootstrap and rules of engagement

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Ground-truth facts confirmed against source and recorded via cz_add_output: tool count = 38 (tools_list.py), package version = 1.0.4 (pyproject), 8 CLI subcommands, PROCEDURE_VERSION = 1.3.0.
- [x] Layer-2 product-doc inventory recorded as an output: the 6 markdown docs + the cz_* tool-description strings in src + the clauderize --help text.
- [x] Governing decisions in place and reviewed: the operational jargon rule (D1) and the scope boundary (D2).
- [x] Working tree clean (plan scaffold committed) and baseline tests green — ready to begin the audit.

### Phase 1: Gameplan conflation survey

**Goal**: Classify all 23 existing gameplans by primary intent (dogfooding | engine-update | mixed) and enumerate every instance where the two were conflated — especially engine or product-doc changes that shipped under a dogfooding frame and left human docs stale. Produce the authoritative classification table and the doc-debt list that feeds rectification. This phase only reads and analyzes layer-1 artifacts; it never edits them.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] All 23 gameplans classified as dogfooding | engine-update | mixed in a recorded table (kept in this gameplan's own layer-1 notes, not a human-facing doc).
- [x] Every conflation instance enumerated: each case where a gameplan's framing blurred dogfooding vs engine-update, or where engine/product-doc changes shipped under a dogfooding frame.
- [x] For each conflation instance, the specific layer-2 human-doc debt it left is named (which product doc went stale/unrefreshed) — or explicitly marked 'no doc debt' — yielding the input list for Phases 3-4.

### Phase 2: Product-doc audit

**Goal**: Exhaustively sweep every layer-2 surface for banned-ID jargon in visible prose (per the operational jargon rule) and for factual drift, producing a precise file:line remediation list partitioned into markdown-doc fixes and in-code-string fixes. A regex sweep, not a sampled read — recon already showed sampled reads miss hits and disagree on the rule.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Every layer-2 surface swept with an exhaustive regex for the banned ID patterns: README.md, SECURITY.md, docs/TRUST.md, docs/UPGRADING.md, docs/TROUBLESHOOTING.md, docs/gameplans/GAMEPLAN-PROCEDURE.md, the cz_* tool-description strings in src/, and the clauderize --help text.
- [x] Each jargon hit recorded with file:line, the offending token, and a proposed plain-prose rewrite.
- [x] Drift candidates verified against Phase-0 ground truth (README tool enumeration vs 38; the 'all hardening findings resolved' claim vs HARDENING.md; version/command claims) and each marked confirmed-drift with corrected value, or false-alarm.
- [x] Remediation list complete and partitioned into markdown-doc fixes (Phase 3) and in-code-string fixes (Phase 4).

### Phase 3: Rectify markdown product docs

**Goal**: Apply the remediation to the six markdown layer-2 docs (README, SECURITY, TRUST, UPGRADING, TROUBLESHOOTING, GAMEPLAN-PROCEDURE): rewrite jargon to plain prose, fix confirmed drift, and refresh any doc left stale by the conflations found in Phase 1 — preserving every machine affordance (anchors, frontmatter, HTML comments) per D-038. Markdown only; no source code in this phase.
**Depends on**: 1, 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] All banned-ID jargon in README/SECURITY/TRUST/UPGRADING/TROUBLESHOOTING/GAMEPLAN-PROCEDURE rewritten to plain prose — re-running the sweep on these files yields zero hits in visible prose.
- [x] All confirmed drift in these files fixed to ground-truth values, including the README MCP-surface enumeration reconciled to 38 tools.
- [x] Every Phase-1 doc-debt item assigned to a markdown doc is addressed (stale doc refreshed) or explicitly deferred with a recorded reason.
- [x] Machine affordances preserved: HTML comments, YAML frontmatter, anchors and link targets unchanged — verified by reviewing that the diff touches only visible prose.
- [x] No layer-1 artifact (gameplan/handoff/tracked log) modified.

### Phase 4: Rectify in-code human-facing strings

**Goal**: Scrub banned-ID jargon from the cz_* tool-description strings (and any CLI help/epilog/server-instruction strings) in src/, rewriting to plain prose. Edit description text only — no logic, no control flow — and prove the full test suite stays green at the baseline (602). This is the engine-adjacent phase: source files change, so it is gated on tests.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] All banned-ID jargon removed from cz_* tool descriptions and any CLI help/epilog/server-instruction strings — re-running the sweep on src/ yields zero hits in description strings.
- [x] git diff shows only description/docstring/help-text string changes; no logic or control-flow lines changed (verified by diff review).
- [x] Full test suite green at the baseline count (617) via cz_preflight or the host test command, before and after the edits.

### Phase 5: Fresh-human-reader verification

**Goal**: Verify the rectified docs read cleanly to a stranger: a subagent with NO source/code access reads the layer-2 docs cold and reports any remaining jargon, unexplained term, or comprehension blocker. Back it with a final automated sweep proving zero banned-ID patterns in visible prose, and confirm every Phase-1 doc-debt item was addressed.
**Depends on**: 3, 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] A subagent with no source/code access reads the rectified layer-2 docs cold and reports zero unexplained internal IDs and zero comprehension blockers — or every issue it raises is resolved and re-checked.
- [x] Final automated sweep across all layer-2 surfaces proves zero banned-ID patterns in visible prose.
- [x] Every Phase-1 doc-debt item confirmed addressed, or explicitly deferred with a recorded reason.

### Phase 6: PII scrub and final commit

**Goal**: Ship the rectified docs safely: scrub PII (home paths, usernames, unrelated sibling-project names) from the staged diff to placeholders, stage exactly the rectified layer-2 files plus this gameplan's own tracked artifacts, and make the single work commit as the LAST step — after a grep scrub-verify, per the no-PII-in-committed-files rule.
**Depends on**: 5.

| Task | Description | Effort |
|------|-------------|--------|
| 6.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] PII sweep on the staged diff (home paths, usernames, unrelated sibling-project names) returns clean — any occurrences scrubbed to ~ / placeholder.
- [x] Working tree staged with exactly the rectified product docs plus this gameplan's own tracked artifacts; no stray files.
- [x] Single work commit created as the final step; layer-1 working-memory artifacts unchanged in substance (only this gameplan's normal tracking writes).
