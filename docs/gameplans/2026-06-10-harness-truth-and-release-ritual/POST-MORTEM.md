# Post-Mortem — 2026-06-10-harness-truth-and-release-ritual

> Closed: 2026-06-10, all five phases complete in one day. **H-08 and H-09
> resolved with dated evidence — the findings tracker is all-resolved
> (H-01..H-09).** Suite 215 → 255 green. Ships next release: shape-C wiring +
> anchored wrapper, the D-010 consumer-leg doctor probe, `clauderize
> release-check`, `docs/RELEASING.md` + 1.0 gates, `[memory]` config
> thresholds. Lessons distilled to L-10 (paired probes) and L-11
> (restart-gated phases).

## What worked

1. **Matrix before wiring (D1 → D2).** Phase 0 refused to let reasoning pick
   the command shape: all candidates ran under all three executors against the
   real wrapper, with the broken shape in the same matrix as the control
   proving the harness detects the failure. D2 then chose shape C on evidence
   (zero quote surface, byte-minimal, no +x dependency) with shape A recorded
   as fallback. The matrix script survives as the re-runnable evidence
   artifact (`scripts/wiring_matrix.ps1`).
2. **The restart-gated phase split worked exactly as designed (C-01 → L-11).**
   The session that shipped shape C could not observe its own next cold start,
   so it recorded an explicit `REMAINING EXIT CRITERION` line in the outputs
   registry and stopped. The next session's own startup digest WAS the
   evidence; it closed Phase 1 cold in minutes, quoting its own transcript's
   `hook_success` attachment (shape C verbatim, exit 0, 388ms) into H-08's
   resolution.
3. **The pre-code live smoke caught a blind probe at design time (→ L-10).**
   The planned `--version` executor probe answers before repo discovery and
   passed anchored and un-anchored wrappers alike — discovered in a throwaway
   shell script BEFORE any code existed. The shipped design pairs probes
   (identity + no-arg digest) so each guard's claim is witnessed by a spawn
   that traverses its layer.
4. **Guard-fires discipline produced the gameplan's best artifact.** One live
   test (`test_live_old_shape_guard_fires_where_direct_probe_stays_green`)
   shows the pre-fix shape failing through the executor leg WHILE the old
   direct probe stays green on it — the retired false green is itself pinned
   as a regression test.
5. **Harness transcripts again proved first-class diagnostics.** H-08 was
   diagnosed from `hook_non_blocking_error` attachments and resolved with a
   `hook_success` attachment — both quoted byte-for-byte into HARDENING.
6. **Blessed-writes discipline held end-to-end.** Every transition, output,
   summary, correction, lesson, consolidation, and promotion went through
   `cz_*` tools; one commit per phase; clean tree at every preflight.

## What didn't (root causes)

1. **Declared phase dependencies were narrative, not technical (C-01).** The
   gameplan said 2←1, 3←2, 4←3; actual safe order was 0, 1-code, 3, 4,
   1-validation, 2. Root cause: dependencies written before the restart gate's
   session-splitting consequence was understood — phases 3 and 4 never
   technically needed Phase 2's probe work. Distilled to L-11: declare
   dependencies by technical need; expect restart-gated criteria to split
   their phase.
2. **The ending protocol is undefined at the last phase.** "cz_write_handoff
   for the next phase" has no referent when every phase is complete; the
   closing session improvised (regenerate the final phase's handoff, point its
   agent-owned notes at close-out). Improvement #1 below.
3. **GAMEPLAN.md task tables stayed scaffold placeholders all gameplan**
   (`_(describe)_ / _(est)_`). Phases executed from goal text + handoff notes
   instead. Placeholders that never fill read as missing work; either fill
   them at planning time or make the per-phase task table optional.

## Friction log (host/tooling, with workarounds)

1. **Transcript identification by mtime lies.** Glob's newest-first ordering
   pointed at the wrong session `.jsonl`; the current session's file was found
   by content (the user's opening message + its two `hook_success` records).
   Runbook: match transcripts by content, never by mtime.
2. **The PowerShell→wsl.exe→distro-shell quote chain** mangled pipelines and
   `$?` repeatedly during verification. Reliable patterns: write a script to
   `/tmp` via UNC and run `wsl.exe -d <distro> /bin/sh /tmp/x.sh`, or capture
   full output in PowerShell and filter PowerShell-side. (Already in session
   memory; re-confirmed.)
3. **`pytest -q` on this host prints no final summary line** (progress lines
   + exit code only). Exit verification counted progress characters and
   trusted the exit code. Rituals that "report the final count" should not
   assume the summary line exists.
4. **Marker-block regeneration vs agent notes (D-008) held** — regenerating a
   handoff while its Phase Notes carry agent edits preserved everything — but
   the sane sequence is: `cz_write_handoff` first, then edit notes.

## Procedure improvements (concrete)

1. **Define the last-phase ending protocol**: when no next phase exists,
   regenerate the final phase's handoff with a "gameplan ready for close-out"
   note and stop — consider saying so in the do-phase skill text.
2. **Restart-gated exit criteria get a registry line at ship time** (L-11):
   an explicit `REMAINING EXIT CRITERION:` sentence in the phase's outputs
   entry is what lets the next session close the phase cold.
3. **Probe design starts from the layer map** (L-10): enumerate which layer
   each guard exists for, then pair probes so each claim is witnessed by a
   spawn that traverses that layer; prove fire/green at the granularity the
   check reports.
4. **HARDENING residual pointers resolve in the post-mortem, not by rewrite.**
   H-08's and H-09's dated resolutions each carried "Residual: Phase 2 …" —
   Phase 2 shipped exactly that (consumer-leg probes from a non-repo cwd), so
   those residuals are now SATISFIED; this paragraph is the authoritative
   statement, and the dated entries stay append-only.

## Carried forward (next initiative candidates)

- **Ship the Unreleased work** via the `docs/RELEASING.md` ritual
  (release-check exit 0 → tag the pushed commit → Release → gate → uvx
  verify → restart-validate). 1.0 gates as of this close: G1 ✓ (restart
  evidence), G2 ✓ (this gameplan), G3 ✓ (release-check mechanical, gate
  pinned), G4 ✓ (tracker all-resolved with dated evidence), G5 ✓ (suite 255;
  structural invariants pinned), **G6 open** (cold-start UX proven live on
  windows-wsl; the native-host live cold start remains), G7 ✓ as of this
  close-out (CHANGELOG + docs updated).
- **MCP server module staleness**: the long-running server holds the modules
  it imported at session start, so in-session `cz_*` writes run pre-edit code
  after engine edits. Known and documented in memory; candidate for a doctor
  or digest nudge ("engine source newer than server start").

## Final state

All five phases complete; 255 tests green; doctor 16/16 exit 0 with the hook
verdict earned through the harness's real leg (git-bash → wsl.exe → sh, from
a non-repo cwd, identity + digest in-band); wiring shape C live and anchored;
release ritual mechanical behind `clauderize release-check`; memory
guardrails in config; H-01..H-09 all resolved with dated evidence. The system
now refuses to claim what nothing traversed — and the probe that would have
lied about it is a pinned regression test.
