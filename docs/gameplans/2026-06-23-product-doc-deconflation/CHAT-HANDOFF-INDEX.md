# Chat Handoff Index — product-doc-deconflation

> Last updated: 2026-06-23
> Status: All 7 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 617

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Bootstrap and rules of engagement | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Gameplan conflation survey | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Product-doc audit | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Rectify markdown product docs | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Rectify in-code human-facing strings | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Fresh-human-reader verification | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-5-HANDOFF.md |
| 6 | PII scrub and final commit | ✅ COMPLETE | 2026-06-23 | 2026-06-23 | handoffs/PHASE-6-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-23

Phase 0 pinned the audit's ground truth by measuring it rather than trusting the digest. Confirmed directly from source: 38 cz_* tools (tools_list.py), version 1.0.4 (pyproject + __init__), PROCEDURE_VERSION 1.3.0, and 8 CLI subcommands. cz_preflight measured the suite at 617 tests — correcting the stale 602 the SessionStart digest carried (correction C-01; Phase 4's green-tests gate retargeted 602→617). All six values plus the layer-2 doc inventory are in the Outputs Registry so later phases read them instead of re-deriving.

The two governing decisions are in place and reviewed: D1 (the operational jargon rule — banned ID patterns vs allowed public product vocabulary vs exempt machine affordances, with INVARIANT-NN explicitly banned in visible prose) and D2 (scope boundary — layer-2 surfaces incl. the cz_* tool descriptions are rectified; layer-1 artifacts are left verbatim). Plan scaffold committed (719f278); preflight green (8 checks, 1 skip). The leak surface is now scoped: the markdown docs (TRUST / UPGRADING / TROUBLESHOOTING / GAMEPLAN-PROCEDURE carry IDs in prose) plus the cz_* tool-description strings in src; the CLI help and host floor text are already clean. Ready for Phase 1 (gameplan conflation survey).

### Phase 1 — completed 2026-06-23

Surveyed all 23 gameplans (~13 engine-update, 7 dogfooding, 3 mixed) and named 3 structural conflations (harness-truth-and-release-ritual, dogfood-followup-findings, standing-curator-loop) where a dogfood frame blended with engine/artifact shipping. Key finding: the conflation's residue in the human docs is STYLE bleed, not missing content — gameplan-driven doc edits carried layer-1 agent shorthand (internal IDs) into layer-2 prose. A background subagent produced the classification and a doc-debt draft; per L-33 its doc-debt claims were verified against the docs directly, and the major ones (cz_loop_step / cz_curate / the skill tools "missing" from the README; CROSS-HOST.md "unreferenced") proved FALSE — the README is complete, accurate, and links CROSS-HOST.md. Verified doc debt is the jargon in TRUST/TROUBLESHOOTING/GAMEPLAN-PROCEDURE; README/SECURITY/UPGRADING are clean.

### Phase 2 — completed 2026-06-23

Swept every layer-2 surface with an exhaustive regex (six markdown docs + the cz_* tool-description strings, located in src/clauderizer/ops.py). Jargon: TRUST.md (6 — O-02/D-031/O-06/H-04/INVARIANT-06/L-03), TROUBLESHOOTING.md (4 — H-09, H-08 x2, the stale "H-01..H-09" range), GAMEPLAN-PROCEDURE.md (several, mixed with legitimate ID-scheme-defining text to KEEP), and ops.py descriptions (D-015/D-016/D-018/INVARIANT-05). Drift: README MCP-surface is ACCURATE (38, names match — recon's "40" was a miscount/false alarm); TROUBLESHOOTING's "H-01..H-09 all resolved" is stale (HARDENING.md has H-01..H-15) → rewrite to plain prose citing the tracker by name; UPGRADING + SECURITY clean and current. Remediation partitioned: Phase 3 = the three markdown docs; Phase 4 = ops.py tool descriptions; no-change = README/SECURITY/UPGRADING. The exhaustive sweep caught what sampled reads missed (TRUST's H-04/L-03) and three recon false alarms — validating D1's "regex, not judgment" and L-33.

### Phase 3 — completed 2026-06-23

Rectified the three markdown docs that carried agent shorthand: TRUST.md (6 IDs), TROUBLESHOOTING.md (4 — including rewriting the stale "H-01..H-09 all resolved" to "resolved findings carry dated evidence and a reproduction"; a naive bump to H-15 would have become a falsehood, since HARDENING.md currently has open findings), and GAMEPLAN-PROCEDURE.md (9). README/SECURITY/UPGRADING needed no changes (verified clean and accurate; the README's 38-tool surface was already correct — the recon's "40" was a miscount). The diff is 20/20 lines, prose-only — every code citation, filename-format template (A-NNN.md / A-MMM), link, marker, and table preserved; no layer-1 artifact touched. Three IDs remain in GAMEPLAN-PROCEDURE.md by design: the frontmatter example (D-007) and the Numbering-Conventions definitions (D-001.../INVARIANT-01...), which DEFINE the ID scheme rather than cite it as shorthand. Re-sweep confirms TRUST/TROUBLESHOOTING clean and GAMEPLAN-PROCEDURE down to only those intentional keeps.

### Phase 4 — completed 2026-06-23

Scrubbed internal-ID cross-references from the cz_* tool-description docstrings in src/clauderizer/ops.py — the surface an agent or user actually sees in the tool list. ~19 ID points (D-009/D-015/D-016/D-018/D-019/D3, INVARIANT-03/05) removed across 13 tool descriptions, plus a couple of "Phase N's" build-phase shorthand simplifications. The diff is 20/21 lines, every one inside a docstring — no logic or control flow touched (verified by diff review). The full suite stayed green at 617 (cz_preflight tests: pytest ok). Deliberately kept (out of scope per D2, or intentional): the module docstring and code comments (internal dev notes, not tool descriptions) and two illustrative example values (the H-03 sample call in cz_resolve_finding, the L-04 sample arg in cz_obsolete_lesson). The CLI help text and host FLOOR_INSTRUCTION were already clean (confirmed in Phase 0), so no source there needed editing.

### Phase 5 — completed 2026-06-23

Verified the rectification two independent ways. (1) A cold fresh-human-reader subagent (no source/tracking access) read all six layer-2 docs as a stranger and found ZERO unexplained internal IDs — the gameplan's objective. It recognized GAMEPLAN-PROCEDURE's remaining IDs as defined-locally in the Numbering Conventions section, validating the keep-decision. (2) An independent automated regex sweep confirmed: README/SECURITY/UPGRADING zero hits, TRUST/TROUBLESHOOTING zero, GAMEPLAN-PROCEDURE only the 3 scheme-definitions, ops.py tool descriptions clean, clauderize --help clean. The cold reader also surfaced concept-definition/onboarding gaps (MCP/hooks/agent-harness/key-merge assumed known; minor prose) — a separate quality axis, pre-existing and not caused by the scrub — tracked as O-04 for a future polish pass. Two out-of-scope leaks found during verification (O-03 CLI runtime-output IDs; O-04 onboarding gaps) are deliberately deferred and tracked, not dropped.

### Phase 6 — completed 2026-06-23

Shipped the rectification safely. PII scrub-verify on both the deliverable diff and the entire gameplan dir came back clean — no home paths, usernames, or sibling-project names were introduced, so nothing needed scrubbing. Committed at the very end, after verification, in two reviewable commits: e375f09 (the deliverable — the 4 rectified files, 40/41 lines) and 0319fdc (the gameplan execution record + the six phase handoffs), plus the earlier scaffold 719f278. The work commit is genuinely the last step; the tree is clean. Layer-1 working-memory artifacts were touched only by this gameplan's own normal cz_* tracking writes — no other gameplan or tracked log changed.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** On a docs/finding audit, VERIFY before three reflexes fire. (1) Don't "modernize" a stale count/claim — a stale "H-01..H-09 all resolved" would have become FALSE when bumped to H-15, since HARDENING.md had open findings; describe the discipline ("resolved findings carry dated evidence") instead of restating a snapshot that drifts. (2) Make "jargon" a mechanical regex + allow-list BEFORE editing — two careful readers disagreed on whether INVARIANT-NN counts; a written rule (gameplan D1) settled it, where taste would have thrashed. (3) A confident subagent doc-debt claim is a lead to verify, not a fact — a survey agent reported README tools "missing" that were present; reading the README first stopped a bloating "fix". Same lesson re-applied to FINDINGS: a CRITICAL marked "open" (H-14) was actually fixed-in-code with stale status — verify the code, not the status label. *(evidence: gameplan 2026-06-23-product-doc-deconflation; commits e375f09 (docs scrub) + the H-14/H-15 status verification; cf. project lessons L-21 (doc drift), L-33 (verify subagent claims))*
