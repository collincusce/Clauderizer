# product-doc-deconflation — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-23

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap and rules of engagement | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Gameplan conflation survey | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Product-doc audit | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Rectify markdown product docs | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Rectify in-code human-facing strings | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Fresh-human-reader verification | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-5-HANDOFF.md |
| 6 | PII scrub and final commit | 🟡 IN PROGRESS | 2026-06-23 | — | handoffs/PHASE-6-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
tool_count: 38 (src/clauderizer/tools_list.py TOOL_NAMES; ops.py REGISTRY mirrors it; a parity test welds them)
package_version: 1.0.4 (pyproject.toml:7 and src/clauderizer/__init__.py:7)
procedure_version: 1.3.0 (src/clauderizer/__init__.py:12)
cli_subcommands: 8: init, status, reindex, doctor, release-check, mcp, ops, uninstall (src/clauderizer/cli.py). Top-level description "Drop-in working memory for AI agents." is already clean prose.
baseline_tests: 617 (measured by cz_preflight via pytest; corrects the stale 602 from the digest — see C-01)
layer2_doc_inventory: README.md, SECURITY.md, docs/TRUST.md, docs/UPGRADING.md, docs/TROUBLESHOOTING.md, docs/gameplans/GAMEPLAN-PROCEDURE.md, the cz_* tool-description strings (src/clauderizer/ops.py REGISTRY + mcp_server.py), and the clauderize --help text (src/clauderizer/cli.py). CLI help + host FLOOR_INSTRUCTION already clean of IDs.
```

### Phase 1 Outputs

```
gameplan_classification: Survey of 23 gameplans: ~13 engine-update, ~7 dogfooding, ~3 mixed (descriptive; full table in the Phase 1 subagent report). Load-bearing finding is the doc debt, not the labels.
conflation_and_doc_debt: 3 structural conflations (harness-truth-and-release-ritual = matrix dogfood vs wiring-shape engine in hosts.py; dogfood-followup-findings = findings frame but ships engine + docs; standing-curator-loop = loop dogfood validating shipped curator engine). The DOC DEBT they left is STYLE bleed, not missing content: layer-1 agent shorthand (internal IDs) written into layer-2 human prose. README/SECURITY/UPGRADING verified clean+accurate (subagent's 'missing tools / unreferenced CROSS-HOST' claims were FALSE per direct README read, L-33).
```

### Phase 2 Outputs

```
jargon_hits_markdown: TRUST.md: O-02(L31), D-031(L43), O-06(L49), H-04(L72), INVARIANT-06(L97), L-03(L104) [all shorthand -> rewrite]. TROUBLESHOOTING.md: H-09(L25), H-08(L28 & L36), H-01..H-09(L82). GAMEPLAN-PROCEDURE.md: INVARIANT-05(L9,L24), L-05(L11,L1163), INVARIANT-13(L12,L168,L178), pre-D-028(L1102) -> rewrite; BUT KEEP the ID-scheme-defining lines (D-001/D-002 L1082, INVARIANT-01/02 L1084) and the illustrative example (introduced_by: D-007 L123).
jargon_hits_src: cz_* tool DESCRIPTION strings live in src/clauderizer/ops.py (REGISTRY/op docstrings) and carry D-015, D-016, D-018, INVARIANT-05, etc. Phase 4 edits ops.py description text ONLY. Module docstrings + code comments in other src/*.py (analyze.py, handlers.py, config.py, ...) are internal developer notes, NOT tool descriptions -> OUT of scope per D2.
drift_and_nochange: README MCP-surface = ACCURATE (38 tools, names match TOOL_NAMES, resources/prompts/host-count all correct; recon's '40' was a miscount). TROUBLESHOOTING.md:82 'H-01..H-09 all resolved' = STALE (HARDENING.md has H-01..H-15) + jargon -> rewrite to plain prose citing docs/HARDENING.md by name. NO-CHANGE files (verified clean+current): README.md, SECURITY.md, docs/UPGRADING.md.
```

### Phase 3 Outputs

```
phase3_edits: 19 jargon cross-refs rewritten to plain prose: TRUST.md (6: O-02/D-031/O-06/H-04/INVARIANT-06/L-03), TROUBLESHOOTING.md (4: H-09, H-08 x2, and the stale "H-01..H-09 all resolved" -> "resolved findings carry dated evidence and a reproduction"), GAMEPLAN-PROCEDURE.md (9: INVARIANT-05 x2, L-05 x2, A-001, INVARIANT-13 x3, pre-D-028). README/SECURITY/UPGRADING untouched (already clean+accurate). Diff 20/20 lines, prose-only; code citations, filename-format templates (A-NNN.md, A-MMM), links, markers, and tables all preserved. No layer-1 artifact modified.
gameplan_procedure_kept_ids: 3 IDs intentionally KEPT in GAMEPLAN-PROCEDURE.md per D1 (defining the ID scheme is allowed; only unresolvable shorthand is banned): L123 "introduced_by: D-007" (illustrative frontmatter example inside a code fence); L1082 "D-001/D-002/D-003" and L1084 "INVARIANT-01/INVARIANT-02" (the "Numbering Conventions" section that DEFINES the ID formats). Phase 5 cold-reader note: these are vocabulary definitions, not misses.
```

### Phase 4 Outputs

```
phase4_edits: Removed internal-ID cross-refs from cz_* tool DESCRIPTION docstrings in src/clauderizer/ops.py (~19 ID points: D-009/D-015/D-016/D-018/D-019/D3, INVARIANT-03/05) across cz_analyze, cz_critique, cz_consolidate_lessons, cz_transition_status, cz_add_open_item, cz_set_exit_criteria, cz_check_exit_criterion, cz_mine_failures, cz_corpus_health, cz_lesson_health, cz_curate, cz_loop_step, cz_discover_skills; also simplified "Phase 1's/Phase 2's" build-phase shorthand. Diff 20/21 lines, ALL inside docstrings — no logic/control-flow touched (verified). Tests green: pytest 617. KEPT (out of scope per D2 / intentional): module docstring (L1/10/14), code comments, 2 illustrative examples (H-03 sample call, L-04 sample arg). CLI help + server FLOOR_INSTRUCTION already clean (Phase 0) — no edits needed.
```

### Phase 5 Outputs

```
cold_read_verdict: Fresh-human-reader cold pass (subagent, no source access): ZERO unexplained internal IDs across all 6 layer-2 docs — the gameplan's goal VERIFIED. GAMEPLAN-PROCEDURE's IDs recognized as defined-locally (Numbering Conventions section), validating the keep-decision. Independent automated sweep agrees: README/SECURITY/UPGRADING=0 hits; TRUST/TROUBLESHOOTING=0; GAMEPLAN-PROCEDURE=3 scheme-definitions only; ops.py tool descriptions clean; clauderize --help clean. Comprehension findings (MCP/hooks/agent-harness/key-merge assumed-known; "[Clauderizer]" breadcrumb introduced late; README "1.0 gates" vague) are a separate concept-definition/onboarding axis, pre-existing and not caused by the ID scrub -> tracked O-04, not resolved here.
```

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: Baseline test count is 602 (carried from the SessionStart digest and cz_status into decision D2 and the Phase 4 exit criterion as the green-tests gate).
**What was actually correct**: The suite is 617 tests — cz_preflight measured it by running pytest (baseline updated 0 -> 617). 617 matches the recorded 1.0.4 "suite 617"; 602 was a stale pre-1.0.4 figure in the digest.
**Why**: The session-start digest's baseline lagged reality and planning trusted it instead of measuring. Phase 0 pins ground truth by measurement, which is exactly where the drift surfaced. The green-tests gate in Phase 4 must compare against 617, not 602.
