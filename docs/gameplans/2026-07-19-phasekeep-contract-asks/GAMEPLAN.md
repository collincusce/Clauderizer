# phasekeep-contract-asks Gameplan

> Created: 2026-07-19
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

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Contract Surface

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] Every ops-registry result and CLI --json output carries schema_version (contract 1.0), and ops --list --json emits the machine-readable op enumeration
- [x] Monotonic revision exists: .clauderizer/revision.json (epoch + counter, atomic temp+rename) bumped by every memory write including cascade-report writes and focus flips, surfaced in status --json; a write-then-read test proves the bump
- [x] New read ops registered in REGISTRY + TOOL_NAMES with parity tests green: cz_list_open_items, cz_list_decisions, cz_list_invariants, cz_list_findings, cz_list_lessons, cz_list_corrections, cz_list_amendments, cz_phase_detail, cz_list_cascade_reports, cz_docs_index, cz_doc, cz_assignments; cz_graph_query emits structured depends_on pins alongside the string form
- [x] Assignment provisional shape lands (revisitable at PhaseKeep m3): gameplan-level Assignee blockquote header, per-phase Assigned line, manager role in config; cz_assign write op + assignment read surfaces
- [x] Init marker-block regression covered: tests assert user content after the managed block survives re-init and half-present markers do not destroy content; any found bug fixed
- [x] Full pytest suite green including the new tests

### Phase 1: Release and Verify

**Goal**: Bump to 1.12.0, pass release-check, cut the GitHub release (Trusted Publishing to PyPI), install from PyPI on this host, and verify the new surface by scripted write-then-read against a scratch repo plus the PhaseKeep O-03 poll benchmark.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] clauderize release-check exits 0 at version 1.12.0 before tagging; GitHub release published; PyPI serves 1.12.0
- [ ] A fresh install outside the dev venv (uvx --from clauderizer or pip) reports clauderize --version 1.12.0 on this host
- [ ] Scripted write-then-read against a scratch repo (released engine) shows the revision bump and schema_version on every output
- [ ] PhaseKeep O-03 poll benchmark recorded against the released revision artifact: 10 projects at 1s intervals, steady-state poller CPU under 2% of one core, p95 read latency under 50ms native
