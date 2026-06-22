# Chat Handoff Index — Empirical self-improvement loop - telemetry-gated curator and loop-gameplan primitive

> Last updated: 2026-06-21
> Status: Phase 5 of 6 in progress

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 548

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
| 0 | Telemetry substrate & baseline | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Utility & failure-risk scoring (advisory) | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-1-HANDOFF.md |
| 2 | The Curator - propose-confirm maintenance pass | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Empirical-gated promotion & typed-edge risk surfacing | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-3-HANDOFF.md |
| 4 | The loop-gameplan primitive | ✅ COMPLETE | 2026-06-21 | 2026-06-21 | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, dogfood & ship | 🟡 IN PROGRESS | 2026-06-21 | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-21

Phase 0 shipped the telemetry keystone: a deterministic, append-only memory-telemetry log (.clauderizer/telemetry.jsonl) plus the read-only cz_corpus_health surface, wired into the two blessed writes that already exist - cz_write_handoff logs which lessons/invariants a handoff surfaced; cz_transition_phase logs each phase's outcome + exit-criteria checked/total. This closes the one verified gap (no persisted empirical signal) that made Phase 1 scoring and the Phase 2 curator impossible. Constitution-clean: stdlib-only/no-ML (D-018), append-only (INVARIANT-03), advisory read-only surface (INVARIANT-05), never written from a hook (INVARIANT-06). Baseline captured pre-loop: 20 active lessons, 0 redundant, 20 never-surfaced, 0 events. Suite 548 -> 554 green (+6 tests, exit 0). Next: Phase 1 turns this signal into per-lesson utility/failure-risk scoring.

### Phase 1 — completed 2026-06-21

Phase 1 turned raw telemetry into per-lesson empirical health via the read-only cz_lesson_health op (tool surface 32->33). utility = fraction of a lesson's RESOLVED surfacings that preceded a passing phase (join key (gameplan,phase) across surfaced+outcome events); plus failure_risk, surfaced/resolved counts, last_surfaced recency, and an advisory signal (never-surfaced | low-utility-review | promotion-candidate) - INVARIANT-05: it surfaces candidates, the agent (and Phase 2's curator) decides. Validated by a deterministic labeled-sample held-out-judgment eval: good lesson 1.0+promote, bad 0.0+review, unused never-surfaced; window-recency confirmed. Deterministic, stdlib-only (D-018), no writes. Suite 554 -> 559 passing (+5 tests), green.

### Phase 2 — completed 2026-06-21

Phase 2 shipped the Curator: cz_curate (read-only, tool surface 33->34) PROPOSES a corpus-maintenance batch from telemetry-derived health, exactly like cz_mine_failures - it never writes. Four action kinds, each with evidence and the blessed cz_* op to apply it: consolidate (lexically redundant project-lesson pair -> obsolete the dup into the higher-utility kept lesson), obsolete (never-surfaced, or utility<=0.2 over >=2 resolved surfacings), flag (0.2<utility<=0.5, review-only), promote (high-utility gameplan lesson -> L-NN). This is SkillOps-style library-time maintenance realized the Clauderizer way: propose-confirm, the agent decides (INVARIANT-05). Validated by an A/B - applying the proposals via cz_obsolete_lesson drops redundant_pairs 1->0 and shrinks the active set while the kept lesson still surfaces for its topic (recall@k preserved). Resolves O-02 (nothing auto-applies). Deterministic, no ML (D-018). Suite 559->565 passing green.

### Phase 3 — completed 2026-06-21

Phase 3 added empirical-gated promotion + typed-edge risk surfacing. (1) Promotion is gated Darwin-Godel-style: the curator proposes promote only on recurrence (>=2 resolved surfacings) AND correlation with passing (utility>=0.8); a single surfacing or a mixed record is gated out (tested). (2) cz_analyze's edge-suggester labels each suggestion with a kind - redundant (lexical near-duplicate) or related; alternative stays agent-assignable since semantic detection would need ML (D-018, recorded as amendment A-001). (3) cz_cascade flags dependents of a shaky upstream (superseded/deprecated/blocked) in a new Preemptive risk section - the risk-propagation analogue of SkillOps, deterministic + advisory (INVARIANT-05). All no-write, no-ML. Suite 565->569 passing green.

### Phase 4 — completed 2026-06-21

Phase 4 delivered the loop-gameplan primitive - the capstone. (1) cz_loop_step (read-only, tool 34->35) runs one iteration: the corpus_health convergence metric + cz_curate proposals + a converged flag (true when no actionable consolidate/obsolete/promote remains) + a spawn_gameplan escape hatch (>=3 review-flags suggests escalating to a driven gameplan - never auto-creates). The agent applies actionable proposals via blessed writes and re-calls until converged. (2) cz_create_gameplan gained kind=driven|loop, rendered as '> Kind:' in GAMEPLAN.md. (3) A K-iteration test proves convergence: proposals -> 0 and the health metric monotone-improves (redundant_pairs/never_surfaced non-increasing) to redundant_pairs=0. (4) GAMEPLAN-PROCEDURE.md bumped 1.2.1->1.3.0 (MINOR) in both the bundled template and the repo copy, documenting the loop-gameplan type. Addresses O-03 (cadence = Routines/SessionStart-nudge/manual, a deployment choice). All read-only, no ML (D-018), advisory (INVARIANT-05). Suite 569->573 passing green.

### Phase 5 — completed 2026-06-21

Phase 5 local close-out done; ship paused for authorization. Promoted 3 enduring lessons (L-36/37/38) and wrote POST-MORTEM.md (EC1). Bumped 0.16.0->0.17.0 + procedure 1.3.0 + CHANGELOG; suite 573 green; doctor engine-checks green (wiring ✗ is gitignored machine-specific, init-repairable); release-check has all 4 registries clean + publish gate green, RED only on clean-tree (commit Phase 5) and push (gated). Created the standing loop gameplan (kind=loop) and ran cz_loop_step on Clauderizer's own 23-lesson corpus (redundant=0, 14 never-surfaced obsolete proposals) - the agent correctly DECLINED all 14 on fresh telemetry, demonstrating the propose-confirm boundary (EC3). EC2's literal 'release-check exit 0' + the actual ship (merge->push->tag->PyPI) are the one remaining gated step, paused for the CEO's go.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**3.** When an exit criterion is over-specified relative to what is soundly buildable under a constraint (e.g. a no-ML lexical engine cannot decide a SEMANTIC 'alternative' edge, D-018), record an honest AMENDMENT with the reason rather than faking the checkbox - the gameplan's own discipline (D-026 empirical gain-gate, INVARIANT-05) is better served by a truthful scope adjustment than a green box. (promoted 2026-06-21: L-38)

### Category: Design

**1.** The empirical signal is the keystone of a self-improving memory system: persist which memory was SURFACED and whether the work then PASSED (an append-only telemetry log), and build it FIRST - per-lesson utility scoring, the curator, and empirical-gated promotion are all unverifiable without it. Derive the signal from blessed events already happening (handoff write, phase transition), never from a hook (INVARIANT-06). (promoted 2026-06-21: L-36)

**2.** Reconcile autonomy with a propose-confirm constitution: a self-improvement loop is autonomous in CADENCE but supervised in MUTATION - it SURFACES proposals read-only (like cz_mine_failures) and the agent applies them via the existing blessed writes; it never auto-mutates memory (INVARIANT-05). This both honors the constitution and matches the practitioner best-practice ('start read-only; summarize before you let it change anything'). (promoted 2026-06-21: L-37)
