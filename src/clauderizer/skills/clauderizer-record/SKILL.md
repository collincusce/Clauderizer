---
name: clauderizer-record
description: Quickly capture a decision, invariant, lesson, correction, or risk into the right place. Use when the user says "remember that…", "we decided…", "note that…", or "that was a mistake, the right way is…".
---

# Record to memory

Route the capture to the correct tool so the graph stays consistent — never hand-edit the logs:

- **A decision** ("we decided X because Y") → `cz_add_decision` (project-wide ADR, or scope `gameplan` for tactics).
- **A rule that must always hold** → `cz_add_invariant`.
- **A reusable lesson** → `cz_add_lesson` (pick a category; it rolls into every future handoff).
- **A lesson that no longer applies** → `cz_obsolete_lesson` (marks it; the log keeps the line, handoffs stop carrying it).
- **A divergence from the plan** → `cz_add_correction` (optionally promote a `lesson` in the same call).
- **A persistent risk / audit finding** → `cz_add_finding`; resolve later with `cz_resolve_finding` (append-only; never delete entries).
- **A new subsystem/feature/external service** → `cz_upsert_entity`.
