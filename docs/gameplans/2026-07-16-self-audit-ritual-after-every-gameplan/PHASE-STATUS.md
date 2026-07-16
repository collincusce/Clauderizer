# self-audit-ritual-after-every-gameplan — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-16

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Design the cz_audit work/release self-audit gate | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Implement rituals/audit.py + register cz_audit | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Wire cz_audit into the shipped close skill + procedure | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Dogfood, ship 1.8.0, close | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-3-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
audit-design: cz_audit = new advisory work/release gate distinct from cz_critique (memory). Mechanical signals (skip-graceful): version single-sourcing (pyproject vs pkg __version__ vs top CHANGELOG heading), dirty git tree, pending cascades + unresolved open items. Judgment checklist (irreducible): clean-environment verification, consumer re-audit, claim honesty, shipped-artifact reality. Return shape mirrors cz_critique: {ok, scope, release, git, graph, checklist, finding_count, summary, prompt}. Read-only, stdlib-only, never blocks (INVARIANT-05).
```

### Phase 1 Outputs

```
cz-audit-impl: src/clauderizer/rituals/audit.py implements audit(paths, config). Registered via ops.cz_audit() + REGISTRY['cz_audit']=Op(writes=False) + tools_list TOOL_NAMES (auto-picked-up by mcp_server + cli). tests/test_audit.py (6 tests): version-drift fires on pyproject-vs-__version__ (the exact 1.7.0/1.6.0 bug) AND on changelog drift, stays QUIET when consistent and when sides missing (L-25 both-directions), shape+checklist+advisory-prompt, and cz_audit registered read-only. Suite 799->805 passed, 5 skipped, green in a FRESH venv. Live smoke: no false version finding on the consistent repo; flags uncommitted work.
```

### Phase 2 Outputs

```
audit-wired-into-close: Shipped close-gameplan skill (src/clauderizer/skills/... + synced .claude/skills copy) gained a step 5 self-audit (cz_audit) before the post-mortem. GAMEPLAN-PROCEDURE.md: Ending Protocol step 5 now says verify in a clean environment; Close procedure gained step 6 self-audit (renumbered 7-9); header + changelog bumped to procedure v1.7.0; PROCEDURE_VERSION bumped 1.6.0->1.7.0 in __init__.py (lockstep enforced by test_modernize). Docs: README discipline list + ARCHITECTURE gained cz_audit. Tests: test_shipped_close_skill_invokes_cz_audit + test_procedure_template_documents_self_audit_at_current_version. Suite 805->807, green in fresh venv. Note: this repo's installed docs/gameplans/GAMEPLAN-PROCEDURE.md copy + config stamp intentionally left at 1.6.0 (they refresh via clauderize upgrade — hand-bumping installed copies is modernize's job).
```

### Phase 3 Outputs

```
dogfood-evidence: Ran cz_audit on this gameplan (dogfood). Before committing: finding_count=1 — release [] (version single-sourced at 1.8.0 across pyproject/__version__/CHANGELOG — the exact check that would have caught the 1.7.0 bug), git flagged the 3 uncommitted version-bump files. Addressed: committed them + resolved the two subsystem cascades. After: cz_audit finding_count=0 (release [], git [], graph []). Consumer re-audit affirmed: cz_audit works via the clauderize ops CLI (full result under results[0].result) and is in the 46-tool MCP surface. Clean-env: verified in a fresh venv (807 passed). Claim-honesty + artifact-reality: every claim (skill/procedure/docs ship cz_audit) is backed by a test. Version 1.8.0; subsys.rituals 0.10.0 + subsys.scaffold 0.12.0, cascades resolved.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
