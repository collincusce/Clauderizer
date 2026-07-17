# advisory-proposal-triage-at-session-start — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-16

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Design the proposal-triage primitive | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Proposal identity + triage ledger + cz_modernize filtering + tools | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | SessionStart digest surfacing + terse upgrade CLI output | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Ship the clauderizer-modernize triage skill | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Docs, dogfood 1.7.0 blind, ship 1.8.0, close | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |

## Outputs Registry

### Phase 0 Outputs

```
triage-design: Stable ids: proposals.proposal_id(kind, *parts) = '<kind>:<12-hex>' over the identifying structural parts (gameplan + gate names / doc list / invariant pair) — materially-changed proposal => new id. Ledger: per-user gitignored .clauderizer/proposals.local.toml, [dismissed] id=date + [deferred] id=until-date; 'handle' stores nothing (condition resolves). filter_pending(proposals, ledger, today) drops dismissed + unexpired-deferred. cheap=True on modernize.report skips only the near-dup-invariant scan (the abstract-index build) so the digest count stays cheap. Invariant-safety: ledger writes are blessed cz_* tools (agent decides, INVARIANT-05); it's per-proposal user verdict not a gate on/off; hook will only surface the count (INVARIANT-04/06); count rides the existing digest (INVARIANT-08).
```

### Phase 1 Outputs

```
triage-impl: src/clauderizer/proposals.py (id + ledger + dismiss/defer/is_suppressed/filter_pending). modernize.report() attaches a stable id to all 6 proposal kinds and gained cheap=True (skips near_dup). ops.cz_modernize filters via the ledger and reports pending_count/suppressed_count; new tools cz_dismiss_proposal / cz_defer_proposal (writes=True) registered in ops REGISTRY + tools_list. init gitignores .clauderizer/proposals.local.toml. tests/test_proposals.py (8): stable+content-sensitive ids, dismiss-hides / fresh-shows / materially-changed-reappears (L-25), defer snoozes-until-date-then-returns, dismiss<->defer move, all report proposals carry ids, cheap omits near_dup, tools registered as writers, init gitignores ledger. Suite 807->815, green fresh venv. E2E smoke: dismiss hides via cz_modernize; ledger file written.
```

### Phase 2 Outputs

```
digest-and-terse-cli: status_bundle.compute() computes a cheap pending-proposal count (modernize.report(cheap=True) + ledger filter, best-effort/try-except so the hook never breaks) into bundle['pending_proposals'], set BEFORE the no-active-gameplan early return; render_digest appends one line ('N upgrade proposal(s) awaiting triage — invoke the clauderizer-modernize skill') only when pending>0, independent of the version-drift modernization line. cli.cmd_upgrade is now terse: mechanical shown in full, proposals summarized as a count + skill pointer (not the wall); --json still lists them. Live smoke confirmed both. INVARIANT-08 preserved (line rides the single digest — test asserts <=1 [Clauderizer] header). golden digest (test_back_compat_focus) unaffected (sample_repo has no proposals). Suite 815->819, fresh venv green.
```

### Phase 3 Outputs

```
modernize-skill: Shipped src/clauderizer/skills/clauderizer-modernize/SKILL.md (+ synced .claude/skills copy). Flow: ask-first ('triage now or keep working?') -> cz_modernize for the pending list -> per proposal handle/dismiss/defer. Per-kind handle playbook: unwired_gates (scaffold .clauderizer/preflight.<kind>.toml [gates], infer from repo scripts else TODO-stub, never guess a real command), no_deliverables (propose deliverables from the specs, confirm, cz_upsert_entity), unseeded_docs (invoke clauderizer-onboard), no_standing_conditions/stale_kind_overlay/near_dup_invariants guidance. dismiss=cz_dismiss_proposal, defer=cz_defer_proposal. Propose-confirm constitution stated (INVARIANT-05). Auto-discovered (appeared in the skills list) + installed by init. 2 tests. Suite 819->821, fresh venv.
```

## Corrections Log

_(Every divergence from the gameplan, captured in real time, as C-NN entries.)_
