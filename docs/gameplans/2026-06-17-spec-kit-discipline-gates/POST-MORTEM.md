# Post-Mortem — 2026-06-17-spec-kit-discipline-gates

> Closed: 2026-06-17, all 4 phases complete. Borrowed GitHub spec-kit's three
> discipline gates into the engine — **clarify** (open items), **exit-criteria**,
> **analyze** — as 5 new tools (24 → 29), all always-on / advisory / judgment-based
> with no config flags (D-015 / D-016 / INVARIANT-05). Suite 270 → 283, zero
> regressions. Lessons L-15 / L-16 promoted; `active_gameplan` cleared. No release
> cut (that's a separate ritual; CHANGELOG Unreleased is staged).

## What worked

1. **The analysis → gameplan → dogfood loop.** A "what do you think of this repo?"
   question (spec-kit vs. Clauderizer) became a verified, four-phase engine feature —
   using Clauderizer's own discipline to build improvements to Clauderizer.
2. **The gates verified each other at close-out, not just in unit tests.** The analyze
   gate surfaced D-016 / D-014 / D-013 when recording its own relevance decision (D2);
   each phase completed with **0 advisories** once its machine-checkable exit criteria
   were checked. The feature dogfooded itself as it landed.
3. **The advisory / judgment-based design held (D-015, the user's "avoid configs, be
   intelligent" steer).** An always-on *advisory* gate needs no enable/disable knob —
   the agent's judgment is the control surface — so the whole feature stayed config-free
   and on `cz_cascade`'s grain ("the engine finds and reports; it does not decide").
4. **Per-phase commits from a green base.** Each phase ran its preflight gate, then
   committed; the open → 4-phase arc reads cleanly (`4936e7d` … `1510eb2`).
5. **The suite caught a cross-feature regression instantly** — exit-criteria surfacing
   fired on the `_(verifiable)_` template placeholder, breaking two Phase 0 tests the
   moment it landed. Write→read→idempotent-rewrite tests earned their keep on an
   *interaction*, not the happy path.

## What didn't (root causes)

1. **The exit-criteria phase was scoped as "toggle a criterion," but nothing could
   author one (C-01).** Criteria were template placeholders, and hand-edits are
   forbidden — so the phase also needed `cz_set_exit_criteria`. Root cause: the plan
   assumed criteria already existed; the no-hand-edit invariant means *every* content
   surface needs a blessed authoring write, not just a mutating one.
2. **The new surfacing regressed Phase 0** by flagging the scaffold placeholder as an
   "unchecked criterion." Root cause: a new always-on surfacing source turns
   previously-inert scaffold into live input. Fixed by skipping placeholders (gameplan
   lesson #2); the suite caught it before it shipped.
3. **The codebase map misattributed the parity test** (claimed `test_blessed_surfaces`;
   it was `test_ops`). Root cause: fan-out exploration locates code fast but its
   `file:line` claims are leads, not facts — reading the real file before editing
   prevented changing the wrong test. Promoted as **L-15**.

## Friction log

1. **The PS→wsl quote chain, again.** An inline `python -c` to parse `clauderize ops`
   output died on bash quote parsing; the `/tmp` runner-script pattern (with a
   `tr -d '\015'` CRLF guard) ran clean. The standing rule held: WSL/complex logic
   goes in a file, never inline.
2. **The engine-stale dance.** Editing the engine while this session's MCP server ran
   the *old* build meant the new `cz_*` tools weren't on the live MCP surface; every
   close-out write went through `clauderize ops` (a fresh process) — the L-05 CLI
   fallback, dogfooded the whole gameplan.
3. **A pre-existing flaky locking timing test** failed once under full-suite load
   (`test_crashed_holder_blocks_at_most_stale_timeout` — it measures wait from *after*
   lock setup, not from lock creation). Diagnosed as test fragility, not a lock bug;
   flagged for a separate fix; proceeded.

## Procedure improvements (concrete)

1. **Edit the source template, not just the render (L-16).** Managed content (the
   CLAUDE.md stanza, `.claude/skills`) renders from `src/clauderizer/` at `init`; update
   the source for durability AND the render for current effect — no test enforces sync,
   so the drift is silent.
2. **Every content surface needs a blessed *authoring* write.** When planning a
   "toggle/edit X" tool, confirm X can be *created* via a blessed path first
   (the `set_exit_criteria` gap).
3. **The advisory shape is reusable.** `result["advisories"] = [{kind, ids, message}]`
   on `cz_transition_phase` is the pattern for any future judgment-based gate: surface
   candidates, the agent rules, never block.

## Carried forward (deferred, recorded — none blocks the feature)

- Wire `cz_analyze` into the `clauderizer-new-gameplan` / `clauderizer-record` skills
  (engine support exists; skill prose only).
- A `cz_status` / digest line for the current phase's unchecked exit criteria (the
  open-items line already exists).
- The flaky locking test — independent fix (task chip raised this session).
- All three are Phase-3 outputs in PHASE-STATUS.

## Final state

Three spec-kit-borrowed discipline gates in the engine: **clarify**
(`cz_add_open_item` / `cz_resolve_open_item`), **exit-criteria**
(`cz_set_exit_criteria` / `cz_check_exit_criterion`), **analyze** (`cz_analyze` +
`cz_add_decision` enrichment). **24 → 29 tools** (MCP + CLI parity). New module
`src/clauderizer/analyze.py` (lexical relevance, no new dependency). Decisions
D-015 / D-016 (project) + D1 / D2 (gameplan); INVARIANT-05; 3 lessons (L-15, L-16
promoted, #2 archived). Suite **270 → 283**, 4 skipped, zero regressions. CHANGELOG
Unreleased staged; `active_gameplan` cleared.
