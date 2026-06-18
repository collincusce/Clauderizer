# STORM-inspired curation methods — Post-Mortem

> Author: Claude Opus 4.8 (session 2026-06-18)
> Date: 2026-06-18
> Scope: Full retrospective on phases 0–3, planned and executed in one session.

## Executive Summary

Imported three reasoning methods from Stanford OVAL's STORM/Co-STORM into
Clauderizer **as deterministic engine-surfacing + skill guidance, never as
runtime dependencies** (D-017) — the only shape that fits a stdlib-only engine
whose primary consumer is an agent. Shipped (staged as 0.12.0): the analyze-gate
**gap-finder** (D-018, `cz_analyze.adjacent` — Co-STORM's moderator move as
one-hop graph adjacency), **provenance/citations** on lessons and decisions
(optional `evidence`), and **perspective-guided planning** in the
`clauderizer-new-gameplan` skill. Suite 289 → 300, zero failures, four phases,
five commits, all on `claude/storm-inspired-curation-methods` (not pushed).

The work was dogfooded end to end: the gameplan was planned and tracked **with
Clauderizer**, the foundational decision was vetted **through the analyze gate it
extends**, and the finished gap-finder was demonstrated **on Clauderizer's own
dependency graph** (`subsys.rituals` → `subsys.graph`, `subsys.markdown-core`,
`subsys.mcp-server`). The deferred Co-STORM "mind map" (#3) is tracked as O-01.

## What the Gameplan Got Right

1. **The split-layer framing settled the architecture instantly.** Reading
   `dependencies = []` early turned "can we use STORM?" into "the engine surfaces
   the inputs, the agent does the reasoning, skills carry the method" — so every
   phase was additive and small. No dependency was ever a temptation.
2. **The `introduced_by` bridge made graph adjacency work for decisions.**
   Decisions aren't graph nodes; the bridge (a feature's `introduced_by` is the
   one structural link from an ADR into the graph) let the gap-finder honor
   D-018's "walk one hop from the top-ranked decision" literally.
3. **Provenance riding inline survived the handoff for free.** Placing the
   `*(evidence: …)*` marker on the lesson line — where the rollup already copies
   verbatim and `lesson_state` can't misread it — meant zero rollup-code change.
4. **Doctor's identity check earned its keep.** Bumping the source version
   without reinstalling the editable package failed 7 doctor tests immediately
   (dist-info 0.11.0 vs source 0.12.0). That is the check working, not breaking.
5. **TDD + per-phase commits + a green suite at every boundary** kept the blast
   radius visible and each phase independently revertable.

## What the Gameplan Got Wrong / Friction Log

1. **`pytest -qq` swallowed the summary line.** `pyproject` already sets `-q`;
   passing another `-q` made `-qq`, which hides the `N passed` line — two runs
   were spent recovering the count. **Fix applied:** run the bare configured
   command; captured as a Phase-0 output.
2. **PowerShell → `wsl.exe` → bash quoting broke commands twice** (a `for` loop
   and a `python -c` with nested quotes). **Fix applied:** avoid nested quotes;
   write JSON/scripts to files and pass paths — exactly why `clauderize ops` is
   file-based (L-05's design vindicated).
3. **Editable version bump needs a reinstall.** Source-only `__version__` +
   `pyproject` bump left the install's dist-info stale; the fix was the normal
   `pip install -e . --no-deps`. Cost: ~1 cycle to diagnose (caught honestly by
   the doctor tests).
4. **Dogfooding staleness.** Editing the engine mid-session means the live
   `cz_*` MCP tools run the pre-edit build (`engine_stale: true`); verification
   and the one new-surface write had to go through fresh processes (`pytest`,
   `clauderize ops`). The engine warns about this — but it means an agent
   upgrading its own engine cannot trust the live tools until restart.

## Procedure Improvements

Candidate edits for the next `GAMEPLAN-PROCEDURE.md` / dev-workflow docs:

- **New anti-pattern — "editable version bump without reinstall."** Bumping
  `__version__`/`pyproject` in an editable install without `pip install -e .`
  leaves dist-info stale and fails identity checks (here: 7 doctor tests). Pair
  the version bump with the reinstall in the release/dev ritual.
- **Make the dogfooding-staleness rule explicit.** When a gameplan edits the
  engine that serves its own `cz_*` tools, route verification and tracked writes
  through fresh processes (`clauderize ops`, `pytest`) until session restart;
  treat live-tool output as the old build.
- **Minor:** note the `-qq` summary-suppression gotcha wherever the test command
  is documented (don't double `-q`).

## Open Threads

- **O-01 (deferred):** the Co-STORM hierarchical lesson **mind map** (#3) —
  reorganize lessons into a graph-backed concept hierarchy so consolidation is
  concept-scoped and the digest surfaces gap-clusters. Its own gameplan; it would
  build directly on this gameplan's lesson #1 (the `introduced_by` graph bridge).
- **Gap-finder at decision-record time.** `cz_add_decision`'s automatic analyze
  enrichment computes `adjacent` but does not yet surface it (Phase 1 scoped to
  `cz_analyze`); surfacing it would put gap-finding exactly where decisions are
  recorded. Easy follow-up.
- **Release.** 0.12.0 is staged in source (CHANGELOG + version) but **not
  released** — run `clauderize release-check` and the publish ritual when ready.
- **Promotion candidates.** Gameplan lessons #1 (`introduced_by` bridge) and #2
  (one-writer-many-readers grammar — close to L-06) are candidates for
  `docs/LESSONS.md` if the mind-map gameplan proceeds; left un-promoted now to
  respect cross-gameplan handoff cost (D-009).
