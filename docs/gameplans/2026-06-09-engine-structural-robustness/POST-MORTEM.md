# Engine Structural Robustness — Post-Mortem

> Author: Claude Code session (Windows-host cold-start, Fable 5)
> Date: 2026-06-09
> Scope: Full retrospective on phases 0–3, executed 2026-06-09 in a single session,
> immediately following the cold-start recovery that produced H-01..H-03.

## Executive Summary

v0.6.0 closed the entire engine-robustness cluster from the two prior
post-mortems plus the same morning's cold-start findings: anchored ID
numbering (C-01 class), structural table writes with write-through healing
(H-02), collision-proof cascade report names, blessed writes for the last
three hand-edit surfaces (Outputs Registry, Per-Phase Completion Summaries,
tracker headers), the lesson-state grammar (D8), doctor engine-identity
checks (D9), and the gauge's close-out note (H-03). Tests grew 109 → 139;
MCP tools 22 → 24; doctor checks 11 → 13. Every defect fixed was first
*reproduced on this repo's own tracked docs*, and every fix was demonstrated
on them too — the gameplan's decisions numbered D3..D9 with a phantom D6 gap
under the very bug Phase 0 fixed, and `subsys.rituals` ended the day with
four same-day cascade reports coexisting where the old code would have kept
exactly one.

A structural note for the record: this session ran on the Windows host where
the MCP server cannot connect, so every `cz_*` operation was executed through
a JSON-ops shim calling the same `mutations.*`/`rituals.*` functions the
tools wrap (D-001/D-007 make this equivalence safe). That constraint is
itself the strongest argument for the CLI-parity open thread below.

## What the Gameplan Got Right

### 1. Live evidence as exit criteria
Every phase's exit criteria demanded demonstration on the repo's own files,
not just the suite: the six fractured trackers healed by same-status blessed
touches, the collision fix proven by Phase 2/3 close-outs re-cascading the
same entities, the close-out itself recorded through the Phase 2 tools.
The discipline carried from discipline-seams ("demonstrate on the live
repo") and again caught what unit tests alone would have missed.

### 2. The amendment flow absorbed a planning miss without derailing
Phase 0's preflight failed immediately (`pytest: not found`) — a gap the
plan hadn't predicted. A-001 + C-01 + task 0.6 recorded and fixed it inside
the procedure: first real use of `cz_add_amendment` in this repo, and the
fix (engine-interpreter-environment resolution) generalizes beyond the
incident.

### 3. Reversing a prior decision explicitly (D5 vs context-economics D6)
Per-phase cascade was deliberately resumed *because* the collision fix
needed same-day repeats to prove itself. Recording the reversal as a
decision kept the contradiction legible instead of silent.

## What the Gameplan Got Wrong

### 1. Assumed preflight ran anywhere the engine runs
**Cost**: one blocked preflight, one amendment, ~30 minutes.
**Root cause**: profile commands resolved via inherited PATH; the venv that
owns pytest is never activated when the engine is launched by absolute path.
**Lesson**: an engine that owns a toolchain must resolve bare commands
against its own interpreter's bin dir (now lesson #1, encoded in
`preflight._command_env`).

### 2. D8's strict grammar invalidated one legacy fixture form
**Cost**: trivial (one test updated).
**Root cause**: a fixture hand-wrote `**4.** (obsolete) old advice.` — a
*leading* marker the engine never produces. The grammar is strictly
trailing; the fixture moved to the documented form. Flagged here because
any in-the-wild hand-edited leading markers would now count as active —
acceptable, since hand-edits were always forbidden.

## Procedure Improvements

- The Ending Protocol texts (index template, do-phase skill, generated
  handoffs) now name the blessed writes (`cz_transition_phase`,
  `cz_add_output`, `cz_add_phase_summary`) instead of "update
  PHASE-STATUS.md" — the protocol is executable as written.
- `cz_add_amendment` renders a `Cascade report:` line pointing at a file
  that is never created when amendment cascade is disabled
  (`rituals.amendments = false`); make that line conditional, or create the
  report.
- close-gameplan skill could add: "when a new write-back lands, backfill
  closed gameplans once" (lesson #3 — self-healing only fires on mutation).

## Session Friction Log (the dogfooding deliverable)

Collected in real time across the cold-start recovery and all four phases:

1. **MCP-or-nothing was the whole session's tax.** With the server
   unconnectable mid-session, *every* tracked write needed the shim. The
   CLI has `status/doctor/reindex/init/mcp` but zero write parity — strictly
   followed, "only use cz_* tools" would have meant not recording the very
   findings about the breakage. Promoted as L-05. The JSON-ops-file pattern
   (`czshim.py /tmp/ops.json`) worked well and is a candidate CLI feature
   (`clauderize ops <file>` or per-mutation subcommands).
2. **Silent hook death is indistinguishable from "not clauderized".** Fixed
   in part (stanza now names the CLI fallback), but a hook that *cannot
   spawn* still leaves nothing in-session. H-01 remains open for an
   engine-side breadcrumb.
3. **Windows-host sessions against a WSL repo are second-class**: wsl.exe
   argument mangling corrupted quoting and exit codes (one phantom "doctor
   exit 0" scare), UNC git needed safe.directory, and the MCP command is a
   Linux path Windows can't exec. Practical guidance: run sessions inside
   WSL; or register a user-scope Windows MCP entry wrapping
   `wsl.exe -d Ubuntu <venv>/bin/clauderizer-mcp`.
4. **`transition_phase` same-status returns ok:False "(or already X)"** —
   ambiguous between "row missing" and "legitimate no-op", and it made the
   heal-by-touch dogfood step non-obvious (healing only happens when the
   normalized table differs). A distinct "no-op" result shape would read
   better.
5. **Recording decisions before Phase 0 landed froze the broken numbering
   into this gameplan forever** (D3..D9, no D1/D2/D6). Embraced as evidence,
   but it shows ordering pressure: defects in the recording machinery
   contaminate the records of the gameplan that fixes them.
6. **The "never hand-edit" rule reads broader than its actual boundary.**
   The procedure expects the planning session to author GAMEPLAN.md body
   content (task tables, captures) directly; the forbidden zone is
   frontmatter + tool-owned logs. The stanza/rules could state that boundary
   crisply — this session hesitated before every body edit.
7. **add_finding's security-tinted schema** (severity/preconditions/
   reproduction) fits engine defects awkwardly, though it worked.
8. **Backfill asymmetry**: new write-backs (headers) don't reach artifacts
   that stopped mutating; this close-out backfilled the two closed gameplans
   by calling the new helper directly — there was no cz-level way to do it.
9. **What felt *good***: the ops-file batching, preflight's baseline
   write-back correcting the fresh template's "0" unprompted, healing
   two-gameplan-old corruption with a no-op transition, and the close-out
   recording itself entirely through tools built three hours earlier.

## Open Threads

- **CLI write parity** (friction #1): expose the mutation surface without an
  MCP client — the highest-leverage robustness item this round surfaced.
- **Publish 0.6.0 to PyPI**: `uvx --from clauderizer` by name still resolves
  the published version; until 0.6.0 ships, any uvx-wired repo dogfoods old
  code (doctor's D9 check now detects it, but only for the engine repo
  itself).
- H-01 engine-side residue: a cold-start breadcrumb when the hook cannot
  spawn at all.
- Carried from before, still deferred: `ACTIVE_LESSONS_WARN` as config;
  project-scope lesson consolidation past ~20 entries.
- `cz_add_amendment`'s unconditional cascade-report pointer (Procedure
  Improvements above).

## Addendum — second live test, same day (Windows-host cold start of the repaired wiring)

> Author: Claude Code session (Windows host, Fable 5), 2026-06-09, post-release.
> Scope: first cold-start of the repaired wiring; 0.6.0 surface exercised over the
> real MCP protocol; findings recorded as H-04 and gameplan lesson #4.

**The live test failed exactly as H-01 warned, one layer up (H-04).** The repaired
wiring (WSL venv console scripts) turned out to be host-scoped: a Windows-host
session over \\wsl.localhost spawned neither hook nor MCP server — no digest, no
cz_* tools, no breadcrumb — while `clauderize doctor` inside WSL reported 13/13
green, identity checks included. Repaired this session: both wiring files
hand-rewritten to wsl.exe-shimmed console scripts and verified from the Windows
side (hook emits the digest; the server answers initialize/tools_list/tools_call
with all 24 tools over stdio). `clauderize init` could not write that wiring
itself: `--run-cmd 'wsl.exe -d ubuntu <venv>/bin/clauderize'` composes
`clauderize clauderizer-mcp` — an invalid subcommand, exit 2. Recorded as H-04
(mitigated; residuals: init composition, doctor host-blindness, no native
mid-session attach).

**0.6.0 surface, exercised over the real MCP protocol** (stdio JSON-RPC probe;
the harness cannot attach a repaired server mid-session, so the probe drives the
same tool layer it would — a fidelity step up from the first session's
`mutations.*` shim):

- Memory gauge: digest and status render `(handoff n/a: gameplan complete)`
  (H-03 fix) and the counts reconcile with the docs — 2 active → 3 after lesson
  #4, 1 promoted, 6 project.
- Doctor identity checks: both green, certifying 0.6.0.
- `cz_add_finding` / `cz_add_lesson` allocated H-04 and lesson **4.** correctly
  through prose dense with H-01/L-06 mentions — Phase 0's anchored numbering
  proving itself on hostile live documents.
- `cz_add_output` / `cz_add_phase_summary` byte-identical upserts:
  content-idempotent (no git diff) but the results still say `action: updated` /
  `replaced: true` with `files_changed` — idempotency holds yet is not observable
  from the result shape; a `changed: false` field would close that.
- `cz_transition_phase` same-status: `ok:false "phase 3 not found (or already
  complete)"` — friction #4's ambiguity reproduced verbatim over MCP. The header
  write-backs were deliberately not re-exercised (it would mean falsifying a
  complete gameplan's status); their on-disk results from close-out stand as the
  evidence.

**Second friction log:**

1. The harness enumerates MCP servers once, at session start: even with
   .mcp.json repaired mid-session, native cz_* tools never attach (ToolSearch
   re-check negative). A restart is the unavoidable last mile of any wiring
   repair — wiring docs and breadcrumbs should say so.
2. PowerShell 5.1 ↔ wsl.exe remains a quoting/encoding minefield: nested-quote
   mangling, a BOM injected when piping native→native, and the MCP server's
   stderr logging interleaving with output. Script files + JSON args files beat
   one-liners every time — the probe pattern (`/tmp/mcp_probe.py` +
   `/tmp/args_*.json`) is the reusable shape, and one more argument for CLI
   parity in the `clauderize ops <file>` form.
3. This gameplan's own index still carries the pre-0.6.0 Ending Protocol text
   ("Update PHASE-STATUS.md…") while the template now names the blessed writes —
   lesson #3's backfill asymmetry, second instance.
4. Open-thread drift: **0.6.0 is already on PyPI** (releases …, 0.5.0, 0.6.0 —
   presumably the v0.6.0 tag push). The "Publish 0.6.0" thread is half-stale;
   what remains is proving doctor's identity check catches a stale uvx wiring.
5. What felt good: the cold-start recovery needed zero user input — the digest,
   the cz_* reads, and the docs they point at reconstructed the phases, the
   D3–D9 numbering story, L-01..L-06, H-01's residue, and the open threads, with
   every claim re-verified live (139 tests, 24 tools, 13 checks, gauge
   arithmetic).
