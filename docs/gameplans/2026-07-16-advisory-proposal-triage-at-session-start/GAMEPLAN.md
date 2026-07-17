# advisory-proposal-triage-at-session-start Gameplan

> Created: 2026-07-16
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

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Design the proposal-triage primitive

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Stable proposal-id scheme decided (content hash of type+subject; materially-changed proposal => new id)
- [x] Ledger format + location locked: per-user, gitignored .clauderizer/proposals.local.toml; verdicts dismissed[id] + deferred[id]=until; 'handle' stores nothing (condition resolves)
- [x] Invariant-safety confirmed: hook only surfaces the count (INVARIANT-04/06), agent triages; ledger is per-proposal user verdict not a gate on/off (INVARIANT-05); count rides in the existing digest, no 2nd injection (INVARIANT-08)

### Phase 1: Proposal identity + triage ledger + cz_modernize filtering + tools

**Goal**: Give each modernize proposal a stable content-derived id. Add a per-user gitignored ledger (.clauderizer/proposals.local.toml) with dismissed[id] and deferred[id]=until, plus read/write helpers. cz_modernize filters out dismissed + unexpired-deferred and reports a pending count. Add tools cz_dismiss_proposal(id) / cz_defer_proposal(id, until) (or one cz_triage_proposal) registered in ops/tools_list. init adds proposals.local.toml to .gitignore. Tests: stable ids, dismiss hides / materially-changed id reappears, defer snoozes then returns, filtering both directions (L-25).
**Depends on**: Design the proposal-triage primitive.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Each modernize proposal carries a stable id; a materially-changed proposal yields a new id (test)
- [x] Ledger read/write helpers for .clauderizer/proposals.local.toml (dismissed + deferred); init gitignores it
- [x] cz_modernize hides dismissed + unexpired-deferred proposals and reports a pending count; a dismissed proposal stays hidden and a fresh one still shows (both directions, L-25)
- [x] Triage tools (cz_dismiss_proposal / cz_defer_proposal) registered in ops + tools_list, read/write as appropriate
- [x] Full suite green in a fresh venv

### Phase 2: SessionStart digest surfacing + terse upgrade CLI output

**Goal**: status_bundle/digest surfaces a one-line pending-proposal nudge ('N upgrade proposals awaiting triage — run the clauderizer-modernize skill'), read-only and exit-0, quiet when zero and independent of the version-drift nudge; it must NOT create a second status injection (INVARIANT-08). `clauderize upgrade` CLI prints a terse summary (mechanical count + pending-proposal count + pointer) instead of dumping every proposal. Tests: digest shows the count only when pending>0; upgrade output is terse; hook stays read-only/exit-0.
**Depends on**: Proposal identity + triage ledger + cz_modernize filtering + tools.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] status_bundle/digest surfaces a one-line pending-proposal nudge only when pending>0, independent of the version-drift nudge, read-only and exit-0
- [x] No second status injection introduced (INVARIANT-08 preserved) — a test covers the dedup
- [x] clauderize upgrade prints a terse summary (mechanical count + pending-proposal count + skill pointer), not the full proposal list; a test asserts the terse shape
- [x] Full suite green in a fresh venv

### Phase 3: Ship the clauderizer-modernize triage skill

**Goal**: Add a shipped skill clauderizer-modernize (src/clauderizer/skills/...): ask-first ('triage now or keep working?'), then per cz_modernize proposal walk handle/dismiss/defer — 'handle' executes what an agent can (scaffold .clauderizer/preflight.<kind>.toml gates, invoke clauderizer-onboard for placeholder docs, draft deliverables), 'dismiss'/'defer' record via the triage tools. Wire the digest + terse upgrade nudge to point at it. Test asserts the shipped skill exists and references the triage tools + cz_modernize.
**Depends on**: SessionStart digest surfacing + terse upgrade CLI output.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Shipped skill src/clauderizer/skills/clauderizer-modernize/SKILL.md exists (ask-first; per-proposal handle/dismiss/defer; handle executes gates/onboarding/deliverables)
- [x] The digest + terse upgrade nudges point at the clauderizer-modernize skill
- [x] A test asserts the shipped skill references the triage tools and cz_modernize; skill installs via init (assets)
- [x] Full suite green in a fresh venv

### Phase 4: Docs, dogfood 1.7.0 blind, ship 1.8.0, close

**Goal**: Docs sweep: README/ARCHITECTURE (new tools + the triage flow), CHANGELOG 1.8.0, GAMEPLAN-PROCEDURE upgrade section (procedure version bump if the documented flow changed). Bump pyproject + __version__ to 1.8.0 in lockstep. Bump subsys.rituals/mcp-server/scaffold as touched; cz_cascade + resolve. Verify full suite in a FRESH venv. Then dogfood 1.7.0 BLIND: close this gameplan via the shipped clauderizer-close-gameplan skill and let cz_audit run untouched — report exactly what it flags and how the close flow feels as a first-time user.
**Depends on**: Ship the clauderizer-modernize triage skill.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Docs swept (README/ARCHITECTURE tool surface + triage flow; CHANGELOG 1.8.0; procedure upgrade section)
- [x] pyproject AND __version__ bumped to 1.8.0 in lockstep (cz_audit + guard test green)
- [x] Touched subsystems bumped; cz_cascade run and resolved
- [x] Full suite verified green in a FRESH venv; count recorded
- [x] Gameplan closed via the clauderizer-close-gameplan SKILL with cz_audit run blind; its findings reported and addressed; post-mortem written; focus handed back
