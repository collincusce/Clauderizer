---
name: clauderizer-amend
description: Change a gameplan after it has started executing. Use when scope shifts mid-flight — a phase needs a task it's missing, a dependency changed, or work must be added/removed.
---

# Amend a gameplan

First decide: **amend** or **new mini-gameplan**?

- If you'd write the *same* Project Overview paragraph for the new work as the original → **amend**.
- If a fresh overview makes more sense → start a separate gameplan (`cz_create_gameplan`).

To amend:

1. `cz_add_amendment` with the affected sections/phases, what changed, and why. It assigns the next `A-NNN` and references a cascade report.
2. Run `cz_cascade` over the affected phases and reconcile:
   - Unstarted phases: the next handoff picks up the change.
   - In-progress: log it as a correction and reconcile mid-flight.
   - Completed: if the finished work conflicts, add a revisit phase.

Amendments are append-only — superseded ones stay with a note.
