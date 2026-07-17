# Chat Handoff Index — advisory-proposal-triage-at-session-start

> Last updated: 2026-07-16
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 807

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
| 0 | Design the proposal-triage primitive | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Proposal identity + triage ledger + cz_modernize filtering + tools | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | SessionStart digest surfacing + terse upgrade CLI output | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Ship the clauderizer-modernize triage skill | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs, dogfood 1.7.0 blind, ship 1.8.0, close | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-16

Locked the triage primitive: content-derived stable proposal ids (kind:hash over identifying parts, so materially-changed proposals re-surface), a per-user gitignored ledger (.clauderizer/proposals.local.toml: dismissed[id]=date, deferred[id]=until; handle stores nothing), filter_pending semantics, and a cheap report mode that skips only the expensive near-dup scan so the digest stays fast. Invariant-safety mapped: hook surfaces the count only (04/06), agent records verdicts via blessed tools (05), count rides the existing digest (08). Design captured in D-052.

### Phase 1 — completed 2026-07-16

Built the triage core: proposals.py (ids + ledger + dismiss/defer/is_suppressed/filter_pending), modernize.report() now stamps every proposal with a stable id and supports cheap=True, ops.cz_modernize filters the ledger and reports pending/suppressed counts, and cz_dismiss_proposal/cz_defer_proposal (writes) are registered in ops + tools_list. init gitignores the ledger. 8 tests prove stable+content-sensitive ids, dismiss-hides while fresh/materially-changed still show (L-25 both directions), defer snoozes-until-date-then-returns, and registration. Suite 807->815, green in a fresh venv; E2E smoke confirmed cz_modernize hides a dismissed proposal.

### Phase 2 — completed 2026-07-16

Surfaced the pending count without noise. The session digest now carries a single 'N upgrade proposals awaiting triage' line (cheap report + ledger filter, best-effort so the hook never breaks), shown only when pending>0 and independent of the version-drift nudge — riding the existing digest, so no second injection (INVARIANT-08). clauderize upgrade went terse: mechanical work in full, proposals as a count + clauderizer-modernize pointer, with --json/cz_modernize for the full list. Live smoke confirmed both surfaces; 4 tests (both directions + single-injection + terse CLI). Suite 819 passed, fresh venv.

### Phase 3 — completed 2026-07-16

Shipped the clauderizer-modernize skill — the agent-driven flow the digest and terse upgrade now point at. It asks first, pulls the pending list from cz_modernize, and walks each proposal handle/dismiss/defer, with a per-kind handle playbook (scaffold gates without guessing real commands, propose deliverables from the specs then cz_upsert_entity on confirm, invoke clauderizer-onboard for unseeded docs) and dismiss/defer via the new tools. It states the propose-confirm constitution (INVARIANT-05). Auto-discovered and init-installed; 2 tests. Suite 821 passed, fresh venv.

### Phase 4 — completed 2026-07-16

Shipped 1.8.0 and closed via the shipped 1.7.0 flow (blind dogfood). CHANGELOG 1.8.0, pyproject+__version__ lockstep, README/ARCHITECTURE swept; subsys.mcp-server 0.12/scaffold 0.13/rituals 0.11 bumped and all cascades resolved (additive; feat.corpus-modernization the extended consumer). Ran cz_audit via the shipped engine: 0 mechanical findings (release single-sourced, tree clean, no pending cascades), then affirmed the 4 judgment checks (fresh-venv verified, consumers re-audited incl. CLI/uninstall, claims test-backed). Dogfood note: the running MCP server predated cz_audit (added this session), so it ran via clauderize ops — inherent MCP-load behavior, worth a docs note. Fresh-venv suite 821 passed.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
