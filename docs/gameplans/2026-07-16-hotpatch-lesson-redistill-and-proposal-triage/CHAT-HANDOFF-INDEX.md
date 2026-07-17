# Chat Handoff Index — hotpatch-lesson-redistill-and-proposal-triage

> Last updated: 2026-07-16
> Status: Phase 2 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 821

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
| 0 | Bootstrap | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Re-distill lessons under the 20 threshold | ✅ COMPLETE | 2026-07-16 | 2026-07-16 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Triage the no_standing_conditions proposal | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Ship 1.8.1 release | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-07-16

Bootstrap complete: gameplan planned and committed, source-of-truth captured (v1.8.0, 821-test baseline, 34 lessons, 1 pending proposal), pre-flight green. Ready for Phase 1 (lesson re-distill).

### Phase 1 — completed 2026-07-16

Re-distilled docs/LESSONS.md from 34 → 19 active project lessons (< 20 threshold met). With 0 lexical-duplicate pairs, the honest lever was thematic consolidation, not near-duplicate merging: 7 syntheses (L-50–L-56) each absorbing a cluster of one-principle-across-war-stories lessons, 22 sources obsoleted into them (append-only, marked not deleted), plus L-43 obsoleted as situation-specific. 12 distinct high-value lessons retained (incl. high-utility L-07, L-21). Dogfooding surfaced engine bug H-18: an obsolete-marker reason containing ')' is miscounted as active (fixed the one occurrence in L-43's reason; regex fix + regression test recommended). Correction C-01 records that corpus re-distill is consolidate+obsolete, not cz_promote_lesson. Handoff now ~2.7k tok; the >20 warning that rode every portfolio handoff is cleared.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**8.** Corpus re-distill of docs/LESSONS.md is consolidate+obsolete (add synthesis → promote → obsolete sources), never cz_promote_lesson (that is gameplan→project). cz_lesson_health's 'promotion candidate' means high-utility/keep, not 'move it' when it is already a project lesson.

### Category: Eval methodology

**1.** Treat every claim, borrowed idea, audit finding, or "realize-the-win" as a FALSIFIABLE hypothesis with a pre-named machine-checkable metric, and MEASURE before building or fixing — a discard/null is a successful outcome; the deliverable is the verdicts plus the survivors. Build the adversarial measuring-stick FIRST: (a) an eval concludes only what its fixtures permit — a cleanly-separable corpus saturates at the 1.0 ceiling so no scoring change can show lift (proves "no regression", never "no value"), so target the mechanism with length-bias/term-skew/near-duplicate confounds up front; (b) when you author BOTH fixture and detector, a 100%-detection/0-FP result is suspicious by construction (teaching to the test) — seed adversarial NEAR-MISSES and run a NAIVE strawman beside the real detector, credibility = beating the strawman ON the near-misses, not beating a no-check baseline (anything beats zero); (c) an audit finding names a symptom + a HYPOTHESIZED cause — measure the hypothesis before fixing (a predicted tokenizer under-count was falsified; the real defect was incoherence, fixed by single-sourcing, not by lowering a threshold to manufacture pairs); (d) near-DUPLICATE detection length-normalizes overlap (Jaccard |A∩B|/|A∪B|), never the raw count (the relevance signal) that a long distinct entry trips by sheer size. Corollaries: when a gate's TARGET metric is already SATURATED by an earlier phase, PREDICT the zero and park the feature by analysis WITHOUT building it (cite the saturated metric + absent need + cost); when a "realize-the-win" phase finds the win already banked, deliver a measurement + a regression guard that LOCKS the property + an honest AMENDMENT, never a manufactured change that regresses validated behavior; and when an exit criterion is over-specified vs what is soundly buildable, record the honest amendment rather than faking the checkbox. (Consolidates L-28, L-32, L-38, L-39, L-40, L-44, L-45, L-46.) (promoted 2026-07-16: L-50)

### Category: Release

**2.** Before any irreversible release step (tag → GitHub Release → PyPI publish), gate on three sweeps. (1) A version number is a claim across four registries that never sync — source (pyproject/__version__), remote git tags, GitHub Releases, the PyPI index — plus the ordering invariant that origin/main must hold the staged commit BEFORE any tag/Release (a GitHub-UI release tags the REMOTE head, so locally-authored guards are unpushed by construction); sweep all four with fresh eyes (uvx by-name answers from uv's cache and can hide a failed attempt — v0.7.0/v0.8.0 were double-claimed by exactly this). (2) Run the suite on EVERY host leg the CI matrix covers — a green on one OS is a guess about the others and the publish cannot be undone; a path/separator assertion is itself a platform claim (assert the wrapper FILE hook.sh|hook.cmd, not the slash) — 0.14.0 shipped with 3 Windows cells red on such an assertion. (3) release-check's clean_tree counts UNTRACKED files (foreign tool artifacts, regenerable caches) as a dirty tree and blocks the ritual even though the published artifact builds from origin/main + the tag; the surgical honest fix is .git/info/exclude (local-only, non-committed, deletes nothing) for files that aren't this repo's content — verify `git status --untracked-files=no` is empty first to prove no real source change is uncommitted. (Consolidates L-31 [itself L-08+L-20], L-42.) (promoted 2026-07-16: L-51)

### Category: Design

**3.** Round-trip idempotency (apply-twice == apply-once) through the engine's own parser is the load-bearing test for every mutation — every file the engine writes must round-trip through its parser in tests, and config parse errors must never be swallowed silently. But it is necessary, NOT sufficient: an engine can read its own corruption indefinitely, so also assert render-validity for EXTERNAL readers (contiguous tables, valid markdown). (Consolidates L-04, L-22 [itself L-01+L-06].) (promoted 2026-07-16: L-52)

**4.** A self-improving memory system rests on two pillars. (1) The empirical SIGNAL is the keystone — persist which memory was SURFACED and whether the work then PASSED (an append-only telemetry log), and build it FIRST: per-lesson utility scoring, the curator, and empirical-gated promotion are all unverifiable without it; derive the signal from blessed events already happening (handoff write, phase transition), never from a hook (INVARIANT-06). (2) Reconcile autonomy with the propose-confirm constitution — the loop is autonomous in CADENCE but supervised in MUTATION: it SURFACES proposals read-only (like cz_mine_failures) and the agent applies them via the existing blessed writes, never auto-mutating memory (INVARIANT-05); matches the practitioner rule "start read-only, summarize before you let it change anything". (Consolidates L-36, L-37.) (promoted 2026-07-16: L-53)

**7.** The memory tool surface has two load-bearing contracts. (1) Name tools by their EFFECT — a context fetch must never mutate the tree (a read-named tool stays read-only). (2) Every tracked WRITE needs a CLI-reachable fallback — an MCP-only mutation surface deadlocks any session whose server cannot connect, stranding exactly the sessions that most need to record what broke (also load-bearing for cross-MODEL sessions that bypass MCP entirely). (Consolidates L-03, L-05.) (promoted 2026-07-16: L-56)

### Category: Cross-host

**5.** Don't assume a non-Claude host/model or a "stale"-looking path behaves as you expect — verify the reality first. (1) Cross-model adherence is NOT guaranteed by exposing the MCP tools: Cursor's Composer 2.5 Fast made 0 MCP calls across 142 tool calls, discovering the `uvx … clauderize ops` CLI fallback on its own (validating that a CLI-reachable fallback for every tracked write is load-bearing for cross-MODEL, not just no-MCP sessions) but ALSO hand-editing tracked docs — so trust-but-VERIFY a non-Claude model's self-reported close-out against engine state (a `reindex` showed its plausible summary claimed entities that were never created). (2) When a host's config paths look stale, first confirm whether it is ONE product that moved or TWO products (predecessor/successor) before repointing — Moonshot's Kimi CLI (`~/.kimi/`, pip) and Kimi Code CLI (`.kimi-code/`, npm) are distinct tools; verify the split from upstream docs, and note a successor may drop conventions the predecessor had (Kimi Code CLI does not read `.claude/skills`). (Consolidates L-35, L-49.) (promoted 2026-07-16: L-54)

### Category: Testing

**6.** Independent surfaces that must stay in agreement drift SILENTLY unless a test pins the seam — add the test (or an independent post-implementation review) at exactly the boundary. Three recurring seams: (1) generated/managed content has a SOURCE template — edit the source, not just the render (Clauderizer renders CLAUDE.md's stanza and .claude/skills from src templates at init; editing only the render leaves the source stale and a future init overwrites it) — update both, source first. (2) The phase that ADDS a field/branch/event is NOT the phase that OWNS the shared function it threads through (config merge, markdown writer, graph builder, hook dispatcher, status_bundle) — per-phase TDD misses the cross-cutting integration; independent reviews repeatedly caught merge_missing dropping host_target, a doctor false-failing non-claude repos, unthreaded native event names. (3) A changelog line or in-code hint that claims a shipped ARTIFACT (example file, scaffold, template) needs a test asserting the artifact actually ships — prose and code paths drift independently and the claim reads as true until someone looks (1.3.1 referenced a .example no code scaffolded). (Consolidates L-16, L-34, L-47.) (promoted 2026-07-16: L-55)
