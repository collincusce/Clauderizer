---
name: clauderizer-do-phase
description: Execute or continue the current gameplan phase end-to-end — pre-flight, do the work, then close out (handoff + status transitions + cascade). Use when the user says "do the next phase", "continue the gameplan", or "work on phase N".
---

# Execute a phase

1. Call `cz_next_phase_context` to load the phase bundle (tasks, key files, lessons, exit criteria). Read the key files it lists.
2. Call `cz_preflight`. If any enabled check fails, STOP and report — do not write code.
3. Execute the phase tasks. Honor every rule in `CLAUDE.md` and the accumulated lessons.
4. Closing protocol:
   - Record outcomes: `cz_add_correction` for any divergence; `cz_add_lesson` for anything generalizable; `cz_obsolete_lesson` for lessons this phase made irrelevant.
   - For each subsystem/feature whose state changed, `cz_transition_status` (this fires cascade automatically when enabled).
   - For any other tracked edit, run `cz_cascade`, then record the verdicts with `cz_resolve_cascade` (never hand-edit the report).
   - `cz_write_handoff` for the next phase.
   - Run exit verification (the host test/build commands) and report the final count.
