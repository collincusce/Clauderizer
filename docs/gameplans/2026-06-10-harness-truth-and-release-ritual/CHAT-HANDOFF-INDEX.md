# Chat Handoff Index — harness-truth-and-release-ritual

> Last updated: 2026-06-10
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 234

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
| 0 | Executor matrix: prove the wiring shape | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | hosts.py emits the immune shape; restart-validate H-08 | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Doctor traverses the consumer leg (D-010) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Release preflight ritual (O3) and 1.0 readiness gates (O4) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | Memory guardrails as config: O1 ACTIVE_LESSONS_WARN, O2 consolidation trigger | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Built scripts/wiring_matrix.ps1 and ran every candidate SessionStart command shape under the three Windows executors (Git Bash bash -c, cmd /c, PowerShell direct) with an in-band pass criterion (digest on stdout — exit codes untrusted, L-09) and, after round 1, a hostile cwd (C:\) by default. Verdict per D1/D2: shape C (//bin/sh //<repo>/.clauderizer/hook.sh) passes all three executors with zero quote surface and is chosen for Phase 1; shape A (sh -c 'exec …') also passes and is the recorded fallback; B (env-prefix) is bash-only; the CURRENT shape fails exactly and only under Git Bash, proving the harness detects H-08's failure (the control fires).

The bigger catch was incidental: round 1's entire cmd column failed not on argv shape but on working directory — cmd cannot hold the UNC project cwd, and clauderizer-hook discovers its repo FROM cwd, so the hook went silently empty (exit 0, both streams 0 bytes). Recorded as H-09 with an anchored-wrapper control proving the fix (cd <repo> in the generated wrapper → 758-byte digest from C:\ under all three executors). Phase 1 therefore ships two changes: the C shape in hosts.py AND the self-anchoring wrapper template; Phase 2 must make init/doctor probes spawn from a non-repo cwd. Gameplan lesson #1: debug every surprising matrix cell before reading the verdict (cwd and a fixture missing +x each confounded a full row/column).

### Phase 3 — completed 2026-06-10

Shipped `clauderize release-check` (O3/D-011): the push-then-release ordering invariant and the four-registry sweep (source, remote tags, GitHub Releases, PyPI-queried-directly) as a doctor-style three-state check — exit 0/2/3, unverifiable registries reported honestly instead of green. Twelve new tests prove every individual skew fires against real git repos with a local bare origin (including the remote-only-tag shape that burned v0.7.0 and v0.8.0) and pin the publish-gate marker to the real publish.yml. Live-fire on this repo returned RED with all four registries correctly showing 0.8.0 claimed and the dirty Phase-3 tree caught — the H-07 incident shape detected on real data. Suite 220 → 232.

docs/RELEASING.md (O4) makes the ritual mechanical (eight steps, release-check exit 0 as the hard precondition, the GCM/workflow-scope credential caveat) and defines seven 1.0 readiness gates G1–G7, each phrased as a verifiable check — G1 (H-08 restart evidence) and G2 (consumer-leg probes, Phase 2) are the open ones this gameplan owes.

### Phase 4 — completed 2026-06-10

Moved the memory-bloat guardrails from prose to config (O1, O2): a new [memory] table with active_lessons_warn (default 12, the former hardcoded constant) and project_lessons_warn (default 20), read by the status gauge with the module constants retained only as the no-config fallback. The gauge gains the O2 nudge — when docs/LESSONS.md L-entries exceed the line, the digest names the cross-gameplan cost and prescribes the re-distill moves (cz_obsolete_lesson L-NN, promote a tighter synthesis) — and both nudges coexist on the single ⚠ Memory line. Malformed thresholds raise at load instead of silently defaulting (L-04); merge_missing passes ints through so a deliberate 0 (warn-always) survives re-init. Suite 232 → 234; this repo's config regenerated by init and verified idempotent, with the live digest correctly silent at 9/20 project lessons.

### Phase 1 — completed 2026-06-10

Wired the matrix-winning shape C into hosts.py — the windows-wsl SessionStart command became wsl.exe -d ubuntu //bin/sh //<repo>/.clauderizer/hook.sh (//-led paths: MSYS2 skips conversion, Linux collapses // to /) — and made the generated wrapper self-anchoring (cd '<repo>' with an unreachable-repo stdout breadcrumb, always exit 0), closing H-09. Regenerated this repo's wiring via plain clauderize init (2 files changed, then byte-idempotent); doctor 16/16 through the new wiring, with wrapper freshness upgraded to full-content compare plus a distinct template-outdated nudge (exit 3). Suite 215 → 220 (anchor render sh+cmd, foreign-cwd execution, unreachable-repo breadcrumb, doctor nudge); production wiring re-verified by the executor matrix from hostile cwd C:\ — shape C PASS/PASS/PASS, shape A fallback confirmed, CUR control failing only under Git Bash.

The load-bearing criterion deliberately spanned a session boundary: the shipping session cannot observe its own next cold start. The following real cold start (2026-06-10, transcript e4573a6d) recorded a SessionStart:startup hook_success attachment running registered shape C verbatim — exit 0, 388ms, full [Clauderizer] digest on stdout, injected into session context — the only in-band proof of the whole chain (L-07/L-09). H-08 resolved with that evidence quoted. Residual handed to Phase 2 (D-010): doctor/init probes still spawn wsl.exe directly from the repo cwd; they must traverse the Git-Bash consumer leg from a non-repo cwd so regressions are caught by checks, not only by the matrix script.

### Phase 2 — completed 2026-06-10

Made doctor's SessionStart-hook verdict traverse the leg sessions actually use (D-010). hosts.verify_hook_wiring now runs the direct wsl.exe round-trip first (deepest diagnosis on failure), then — when Git Bash is reachable (interop path from WSL, canonical path on win32) — spawns the registered command STRING through bash.exe -c from a non-repo cwd twice: --version for engine identity, no-args for the in-band digest. The split matters and was discovered by the pre-code live smoke: --version answers before repo discovery, so an identity probe is anchor-blind; only the no-arg digest path proves the H-09 anchor. Executor unreachable → honest unverifiable naming Git Bash (exit 3), with no end-to-end claim surviving for an untraversed leg. init's registered-hook spawn-test switched to the same hostile-cwd digest probe, so an un-anchored wrapper can no longer register.

Exit criteria all proven live on this box: the old wiring shape FAILS through the executor leg while the direct argv probe stays green on it (the false green retired, demonstrated in test_live_old_shape_guard_fires_where_direct_probe_stays_green); shape C passes end-to-end; real-repo doctor 16/16 exit 0 with the verdict naming the traversed leg (git-bash → wsl.exe → sh); init idempotent with the new probe live. Suite 234 → 255 (17 hermetic + 4 live skip-guarded tests). Lesson #3 recorded: a probe's argument changes which layers it traverses — judge each claim with the probe that actually reaches its layer.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

**1.** Debug every surprising matrix cell before reading the verdict: a cell can fail for a reason orthogonal to what the matrix measures, and a column can be 100% confounded. Round 1's entire cmd.exe column failed on working-directory fallback (H-09), not argv shape; shape A's row failed on a fixture missing +x. Both initially read as "shape ineligible" — the truthful matrix needed the confound removed (anchored wrapper, executable fixture) and the criterion hardened (hostile cwd by default). Lesson #4's "prove the probe" applies cell-by-cell, not just to the harness as a whole.

**2.** Declare phase dependencies by technical need, not narrative order: a restart-gated exit criterion guarantees the shipping session cannot close its own phase, so genuinely independent later phases will (and should) run while it waits. What made the split safe was the outputs registry carrying an explicit REMAINING EXIT CRITERION line — the next session resumed and closed the phase cold from that line alone.

### Category: Observability

**3.** A probe's argument changes which layers it traverses: --version short-circuits before repo discovery, so it certifies launch identity but is blind to the H-09 anchor; the no-arg digest path proves anchoring but carries no version claim. One spawn cannot witness both — pair the probes and judge each guard's claim with the spawn that actually reaches its layer. Found by the pre-code live smoke (lesson #4's "prove the probe" applied at design time): the planned --version-only executor probe passed anchored AND un-anchored wrappers alike.
