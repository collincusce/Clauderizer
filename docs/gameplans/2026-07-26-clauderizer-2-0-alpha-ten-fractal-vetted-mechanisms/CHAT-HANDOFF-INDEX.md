# Chat Handoff Index — clauderizer 2.0 alpha — ten fractal-vetted mechanisms

> Last updated: 2026-07-27
> Status: Phase 3 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 1424

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
| 0 | Honest endings and epistemics | ✅ COMPLETE | 2026-07-26 | 2026-07-26 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Lifecycle detectors | ✅ COMPLETE | 2026-07-27 | 2026-07-27 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Live state and budgets | ✅ COMPLETE | 2026-07-27 | 2026-07-27 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Attention and consolidation | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Integrity and enforcement | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Evidence matrix and graduation | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |
| 6 | Close-out and ship 2.0.0a1 | ⬜ NOT STARTED | — | — | handoffs/PHASE-6-HANDOFF.md |
| 7 | Fleet pattern: glossary, skill, productization | ⬜ NOT STARTED | — | — | handoffs/PHASE-7-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-26

Both phase-0 mechanisms landed under their binding conditions (research-fractal-vetting.json), tests-first. Honest terminal vocabulary: the status matcher became positional (earliest word-boundary match wins, longest on tie) — killing a LIVE laundering path where dict-order matching read "DEFERRED — call it done" as COMPLETE via the trailing word; `deferred` joined the write vocabulary (⏸️ DEFERRED, reason after the em-dash, engine token leads, empty-safe sanitizer) with exited/abandoned/superseded/wontfix as aliases INTO it and a ratchet test pinning exactly seven statuses; tracker headers now mirror _lifecycle's closed set (COMPLETE+DEFERRED renders "Complete", all-deferred "Deferred"); completing over unchecked criteria names the deferred alternative while the deferred door itself never nags (INVARIANT-05, no flags); deferred is a telemetry terminal outcome carrying reason, making pass_rate an honest goal-met rate. Procedure 1.9.0→1.10.0 (three-way close-out documented), both skill copies + ops docstring in the same commit (MCP schema auto-derives).

Unknowable-never-zero epistemics: the four conflation sites are fixed with the missing-arm tests written first and RED confirmed before implementation — probes that could not run are `unevaluable` (met stays boolean, additive field); preflight warns "cannot trip" on armed-but-unrunnable guards, contains a raising runner as UNKNOWN-not-pass with additive verdict/gates_unrun fields; curator consolidation stops coercing unmeasured utility to 0.0 (evidence text names the unmeasured side); staleness ages carry a hedged "~N active day(s)" only once a stale set exists, with no claim on any git failure. The corpus sweep ratchet ran green over the real trackers (all flips move toward open/deferred). Bonus proof the enforcement stack works: the L-68 separator ratchet fired on two new message-class assertions mid-phase and forced their classification (baseline 40→42). Suite 1330→1379, zero failures; commit 184c353.

### Phase 1 — completed 2026-07-27

Both lifecycle detectors landed under their binding conditions, with one earned design delta. Heal-on-proof stranded-state: session_ledger.py stamps claimant identity (pid, /proc starttime, host, agent, transport) on every in_progress transition inside the existing write lock; the probe grades dead/alive/inconclusive with a hard POSIX gate (a spy test proves win32 can never reach os.kill) and PID-reuse detection via starttime mismatch; stranded.py fires only on provable death — never for its own process, never on parked states — and renders one shared judgment-menu describe() across digest and preflight (adopt via the blessed same-status re-stamp, or close honestly as deferred using phase 0's vocabulary). Reopening a closed phase now surfaces a re-authorization advisory. The read path's zero-bytes contract is pinned by tree-hash test.

Backstop landings: interrupted.py fires when non-docs commits landed after the tracker anchor and no closing write exists — and the phase's one real design change was forced by our own INVARIANT-08 golden: the literal vetted geometry fired on ORDINARY LIVE work, so the detector gained a liveness gate (alive-or-viewer claimant = quiet; provably dead = stranded's finding; the backstop speaks only where the ledger cannot grade — no stamp or inconclusive). That keeps exactly one voice per repo state, pinned by disjointness tests. Its describe() subsumes memory-lag's claim and explains the clean_tree FAIL and do-phase STOP interactions, with a greppable one-phrase-only pin. The refusal journal shipped at the REGISTRY construction seam (both run_op and MCP direct paths journal ok:False writes; reader integration deliberately deferred to phase 3). Mid-phase the enforcement stack again collected its own dues: subsystem doc + ratchet enrollment at 0 omissions, ARCHITECTURE count 40→41, and the memory-lag byte-identity fixture updated to truthfully model a live claimant. Suite 1379→1424, commit 586d572.

### Phase 2 — completed 2026-07-27

Both mechanisms landed under the binding order: the INVARIANT-10 amendment (with D-072) committed BEFORE any stamp code existed — the append-only supersession defines figures-only, change-triggered cz_state notices as a category distinct from status injection, with five bounds all pinned by test. The stamp itself lives at the single ops dispatch seam (now three wrappers deep: contract stamp, refusal journal, state stamp): an 8-key whitelist-ratcheted figure set recomputed from canonical markdown, emitted only when the figures moved this session, byte-bounded (raw checkbox counts — a spy test proves the approval-hashing path is never called), isolated in both directions, and env-armed dormant (CLAUDERIZER_STATE_STAMP=1) until the phase-5 stamped-vs-unstamped matrix decides the default. Contract bumped 1.0→1.1 additively.

Budgets are declared-derived-dormant: `> Budget: N sessions` (+ phase-block tier) read live from markdown, spend counted as DISTINCT RECORDED DATES of preflight stints (proc tags never the unit), reserve = ceil(10%) as a module constant, wind_down/over derived at read time with nothing persisted and no flags, UNTRACKED-never-zero epistemics, and one phase-aware describe() across the digest line, the cz_next_phase_context wind_down attachment, and the pre_compact convergence (L-68 clause 1). The phase's earned correction (C-02): the stint writer moved from preflight.run() to the cz_preflight op after the literal assessment placement mutated the read-only sample_repo fixture across suite runs and broke the green-preflight-never-dirties principle — the library function is now pinned write-free by test. Suite 1424→1457; commits 6215726 + cabbd3e.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_
