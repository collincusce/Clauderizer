# Chat Handoff Index — alpha-to-beta-evidence

> Last updated: 2026-06-10
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 255

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
| 0 | Beta gates on the record; ship 0.9.0 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | CI proves the OS matrix; win32 leg executed for real | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | G6: native-leg cold-start evidence | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Foreign-repo live loop: node profile end-to-end | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Beta-evidence consolidation; scope gameplans B and C | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Shipped 0.9.0 — the harness-truth backlog (shape-C wiring, D-010 consumer-leg probes, release-check, RELEASING.md, [memory] config) is now public — and put the beta gates on the record: D-012's B1–B6 written into docs/RELEASING.md beside the 1.0 gates, with the evidence table Phase 4 will complete. The ritual ran exactly as written and boring on purpose: push the backlog first, stage (three version surfaces + editable reinstall + CHANGELOG retitle), doctor exit 0 with the executor-leg probe already claiming identity clauderizer 0.9.0, release-check exit 0 before any tag existed (all four registries swept fresh and unclaimed), tag the pushed commit, cut the Release, watch the tag==source gate pass — its first green passage on a legitimate release — and verify fresh resolution via uvx --refresh. Zero incidents, against two prior releases (0.7.0, 0.8.0) that each had same-day incidents; the machinery built to prevent those shapes was load-bearing, not decorative.

B1 is satisfied with dated artifacts (staged commit bdac36b, publish run 27311516131, the Release URL, the fresh-resolve output). One forward-looking catch for Phase 1: the publish run's annotations warn that checkout@v4 / upload-artifact@v4 / setup-uv@v5 run on deprecated Node 20 (forced to Node 24 from 2026-06-16) — the test.yml rework should bump action versions while it is in there.

### Phase 2 — completed 2026-06-10

Closed G6, the last open 1.0 gate, with both host shapes evidenced and the legs named per D-010. The native half ran live on a fresh scratch repo: plain init (whose spawn-test now IS the hostile-cwd digest probe), doctor 14/14 exit 0, and the registered SessionStart string traversed exactly as a native harness would execute it — /bin/sh -c and /bin/bash -c from a hostile cwd — delivering the in-band digest and the 0.9.0 identity through the same leg (L-10 pairing). The windows-wsl half was already carried by the harness-truth restart evidence (transcript e4573a6d). RELEASING.md's G6 entry now records the satisfaction with a named residual rather than a silent pass: the native evidence is leg-faithful but not a literal Claude Code cold start on a native-OS machine, since this host's harness is Windows. B3 row filled in the beta evidence table.

### Phase 1 — completed 2026-06-10

Expanded CI from ubuntu-only to the full 9-cell OS matrix (ubuntu/macos/windows × py3.11–3.13) and made the windows cells truthful: the native cmd wrapper is now EXECUTED on real Windows (4 new live tests — digest passthrough, dead-engine breadcrumb, unreachable-repo breadcrumb, hostile-cwd cd /d anchor), not simulated via monkeypatched platform. The decisive move was previewing the windows-latest cell locally (a native Windows venv installed from the UNC repo) before spending CI cycles: that run surfaced three real product bugs invisible from Linux — missed .exe console-script resolution, text-mode newline corruption of the cmd wrapper (which also silently broke init idempotency on win32), and doctor freshness never matching a healthy win32 wrapper after CRLF normalization — plus a doctor gap for distro-spelled wrapper paths and cp1252-blind test reads. Two CI cycles total: round 1 failed only windows/3.11 (shutil.which doesn't PATHEXT-resolve explicit paths before 3.12 — the direct-wiring test now registers the real .exe), round 2 went 9/9 green (run 27312987722).

D3's leg-honesty held: the win32 twins cannot skip on windows runners, the 4 WSL-interop live tests skip cleanly everywhere, and the windows-wsl executor matrix remains local dated evidence since GitHub runners have no WSL. Both workflows also got Node-24 action bumps (the deprecation warning caught in Phase 0's publish run). B2 row filled in the RELEASING.md evidence table.

### Phase 3 — completed 2026-06-10

Ran the first-ever live loop on a repo that is neither Clauderizer nor python: a node scratch repo, adopter-realistic (scaffold committed). Auto-detect chose the node profile; preflight ran real `npm test` and `npm run build` (baseline 2 captured by the mocha regex); every tracked write — gameplan creation, two phase transitions, decision, lesson, output, summary, handoff — went through `clauderize ops`, exercising L-05's CLI parity for real; the digest arrived both directly and through the registered command from a hostile cwd; and the guard fired in both directions (broken test → preflight FAIL with the tests check naming the failure; restored → 7/7 PASS). Zero hand-edits of tracked docs; doctor exit 0 throughout.

The loop earned its keep by surfacing a stranger-facing diagnosis bug invisible on the home repo: a fresh `git init` with zero commits — exactly the state a brand-new adopter runs preflight in — was misdiagnosed as "not a git repo" because rev-parse fails identically on an unborn branch. Fixed by discriminating via rev-parse --is-inside-work-tree into an honest "no commits yet (unborn branch)" skip, with two regression tests (suite 259 → 261) and a live re-verification in the loop's round 2. B4 row filled in the RELEASING.md evidence table.

### Phase 4 — completed 2026-06-10

Consolidated the evidence: B1–B4 verified holding simultaneously on one commit (89c94e3) — 0.9.0 fresh-resolving from PyPI, the 9-cell CI matrix green twice consecutively, G6 closed with named legs, the node loop proven with guard-fires — with a fresh doctor exit 0 and the suite at 261. The RELEASING.md evidence table now cites a dated artifact for every gate this gameplan owned. The fresh release-check run was deliberately included and reads exit 2: all four registries correctly report 0.9.0 as claimed by today's release — the L-08 guard refusing version reuse — recorded explicitly so the post-release red is never mistaken for drift.

Scoped the rest of the arc from what the evidence revealed. Gameplan B (stranger-readiness, B5): clean-environment quickstart walk, upgrade/uninstall stories, the trust-model doc for what init writes into .claude/settings.json, a troubleshooting runbook distilled from HARDENING and the friction logs, and the README positioning pass. Gameplan C (beta-flip, B6): burn-down, the classifier flip shipped via the ritual at a version chosen by fresh sweep (0.10.0 expected), plus the deferred MCP-server staleness nudge if it fits. The one named residual carried forward: a literal Claude Code cold start on a native-OS machine (G6 note).

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Preview a foreign CI cell locally before iterating through the pipeline: a native-Windows venv installed from the repo and running the suite found every win32 defect (3 product bugs + a test-encoding class) in one local cycle, where CI feedback costs minutes per round and truncates logs. The matrix run then needed only two cycles, and the one CI-only failure was a runner-version quirk (py3.11 which/PATHEXT) no local 3.13 could have shown — i.e., local preview shrinks CI iteration to exactly the failures only CI can produce.
