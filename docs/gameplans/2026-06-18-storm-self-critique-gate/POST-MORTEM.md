# STORM self-critique gate — Post-Mortem

> Author: Claude Opus 4.8 (session 2026-06-18)
> Date: 2026-06-18
> Scope: Phases 0–2, planned and executed in one session, ships under 0.12.0.

## Executive Summary

Shipped the **self-critique gate** (`cz_critique`, D-019) — the deep-research's
top-ranked remaining STORM transfer — plus two skill refinements
(perspective-from-related-entities, outline-before-synthesize). `cz_critique`
assembles a reference-free **Coverage / Coherence / Grounding** rubric for a
target by composing signals the engine already computes; the agent grades, the
engine never scores or blocks (INVARIANT-05), stdlib-only. This gameplan was
itself *chosen* by the methods we built earlier (the deep-research was the
perspective interrogation; the `cz_analyze` gap-finder vetted it) and *closed*
by the gate it added (`cz_critique` on its own gameplan: 2 Coverage gaps = the
deliberate deferrals O-01/O-02, accepted with reason; Coherence/Grounding clean).
Suite 300 → 305; all phases complete.

## What Worked

1. **The gate is composition, not new logic.** `cz_critique` reuses
   `status_bundle`'s open-items/exit-criteria/drift/pending-cascade signals + the
   provenance check, reshaped into STORM's dimensional rubric. Surface-don't-decide
   meant the gaps already existed; the gate just framed them.
2. **The dogfooding loop closed twice.** The methods built in the prior gameplan
   selected this work; the gate built in this gameplan critiqued it at close.
3. **The self-review earned its place.** A code-reviewer pass found four real
   issues — a missing `None`-guard (parity with the dependencies branch), a
   sentence-ending-id mention bug (`subsys.mid.` never matched), a `critique`
   double-read, and a private-symbol coupling — all fixed with a regression test
   (305 green). None were style nits.

## What Didn't / Friction Log

1. **The active-gameplan layering trap** (gameplan lesson #1): `mutations.create_gameplan`
   scaffolds but does not flip `active_gameplan` — the ops wrapper does — so the
   first cut of the critique tests silently critiqued the fixture's gameplan and
   3 failed. Fixed by pointing the test config at the fresh gameplan.
2. **Engine-staleness while dogfooding** (continued from the prior arc): this
   session's MCP server runs the pre-edit engine, so every new-surface write
   (`evidence`, `cz_critique`) went through `clauderize ops` (a fresh process) and
   verification went through `pytest` — never the live `cz_*` tools, which lag
   until restart.

## Procedure Improvements

- **Add `cz_critique` to the close ritual.** Running it before completing a phase
  or closing a gameplan is the reference-free coverage check the procedure has
  lacked; the close-gameplan / do-phase skills should point at it (follow-up: the
  skills currently describe outline-before-synthesize but not the gate).
- **Name the engine-staleness rule** (carried from the prior post-mortem): when a
  gameplan edits the engine serving its own tools, route new-surface writes and
  verification through fresh processes until restart.

## Open Threads

- **O-01 (deferred):** consecutive-same-intent **staleness counter** — trivial
  stdlib, but noise risk (conversational vs phase cadence). Validate the signal
  first.
- **O-02 (deferred):** the mind-map's **deterministic graph cleanup**
  (trim-empty-leaves / collapse-singletons) — collapse-singleton may be unsafe on
  a retention graph. Validate semantic safety; pairs with the prior gameplan's
  O-01 (the full mind map).
- **Release:** 0.12.0 (this gameplan + the prior STORM-inspired-curation arc) ships
  via the release ritual at the end of this session.
