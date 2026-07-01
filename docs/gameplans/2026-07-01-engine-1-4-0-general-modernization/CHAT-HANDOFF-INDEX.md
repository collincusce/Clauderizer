# Chat Handoff Index — engine-1.4.0-general-modernization

> Last updated: 2026-07-01
> Status: Phase 4 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 716

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
| 0 | Baselines, design decisions & plan commit | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Scoped memory — write path & near-dup parity | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Scoped memory — read path & curator grouping | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Approval gates — hash-bound exit criteria | ✅ COMPLETE | 2026-07-01 | 2026-07-01 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Deliverable-matrix campaigns | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Standing conditions + consumes surfacing | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Corpus modernization framework | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Docs & procedure 1.5.0 & version bump | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |
| 8 | Dogfood & live verification | ⬜ NOT STARTED | — | — | handoffs/PHASE-8-HANDOFF.md |
| 9 | Ship 1.4.0 — release ritual & close-out | ⬜ NOT STARTED | — | — | handoffs/PHASE-9-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-01

Planned the 1.4.0 release from the confirmed feature-brief verdict. Recorded the two architectural ADRs (D-042 two-tier corpus modernization; D-043 scoping-is-filtering) and four gameplan decisions (hash-bound approval criteria with computed staleness; deliverable entities with kind lifecycles, matrix in detail views, deliverable≠asset; lazily-evaluated standing conditions; engine 1.4.0/procedure 1.5.0 additive release shape). Laid out phases 1–9 with exit criteria, upserted five planned feature entities with subsystem edges, filed O-01..O-03 (edge triage, near-dup threshold recalibration, marketing-studio reply + usage fixes). Baselines: engine 1.3.1, procedure 1.4.0, surface 42, suite 716 green via preflight. Plan committed at d0b3068 on feat/engine-1.4.0-general-modernization; PII scrub clean. Code recon (subagent) mapped all six touch areas with line anchors — recorded in the Phase 1 handoff notes.

### Phase 1 — completed 2026-07-01

Scoped-memory write path shipped. cz_add_invariant gained scope (project | gameplan:<id>, malformed shapes rejected, unknown gameplan ids warn advisory) and audience; cz_add_lesson gained audience — both written in the existing entry grammar (**Scope**/**Audience** metadata lines; *(audience: X)* lesson marker) so untagged writes are byte-identical to 1.3.1 (tested). The write-time near-duplicate advisory now covers invariants via a shared analyze._near_duplicates engine — one tokenizer, one threshold (INVARIANT-09 guard green), self-excluding since invariants share one file. Abstract index records gained scope/audience fields (SCHEMA_VERSION 2, cache auto-refreshes) plus parse_audience() single-sourced beside the lesson-line grammar. CLI parity verified live via clauderize ops --schema. Suite 725 passed (+9). Bonus O-02 evidence: the verbatim marketing-studio-shaped duplicate pair trips the 0.40 threshold in the live test.

### Phase 2 — completed 2026-07-01

Scoped-memory read path shipped as pure filtering. analyze.scope_filter (single-sourced through abstract_index.parse_scope) drops other-gameplan invariants from cz_analyze (ops passes the focus id; no focus → no filtering, surfacing bias), from the handoff's governing-invariant pointer, and from surfaced_ids telemetry. Audience threading: cz_next_phase_context(audience=...) filters gameplan + project lesson rollups, pointers, and focused sets — untagged always passes; the WRITTEN handoff file is never filtered (correction C-01: the propagation rule wins over the plan's original wording, pinned by test). Curator paths (corpus_health + curate_proposals) pair only same-audience lessons. Digest memory gauge untouched. Suite 730 passed (+5).

### Phase 3 — completed 2026-07-01

Hash-bound approval gates shipped (D1). New criterion grammar "APPROVAL: <artifact> — <desc>" inside the existing checkbox model; cz_approve_gate (surface 42→43, writes=True, CLI parity live-verified) stamps _(approved <date> sha256:<12-hex> — note)_ and checks the box; parentheses in notes sanitized to brackets (own test caught the half-done sanitizer). Satisfaction is computed at read time in status_bundle.exit_criteria — unapproved/stale/missing all report unchecked with a reason, so cz_check_exit_criterion, cz_transition_phase(complete) advisories, and status detail get reopening for free; a hand-flipped checkbox never counts and advises cz_approve_gate. Preflight gains an approval_gates check appended ONLY when the current phase declares approvals (byte-identical check list otherwise, INVARIANT-07): stale/missing warn — PASS WITH WARNINGS, never fail (INVARIANT-05). Suite 737 (+7).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
