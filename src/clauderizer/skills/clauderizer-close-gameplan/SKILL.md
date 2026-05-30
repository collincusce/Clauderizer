---
name: clauderizer-close-gameplan
description: Close out a completed (or explicitly deferred) gameplan. Use when all phases are done and the user wants to wrap up and capture what was learned.
---

# Close a gameplan

1. Confirm every phase is complete or explicitly deferred (`cz_status`).
2. Run a full cascade pass; resolve any pending reports.
3. Update project-level docs (CHANGELOG, ARCHITECTURE, REQUIREMENTS) to reflect final state.
4. Write a `POST-MORTEM.md` in the gameplan dir: what worked, what didn't (with root causes), and concrete improvements to the procedure. This is where the system itself gets better.
5. Leave the gameplan directory on disk (nothing is deleted) and clear/replace `active_gameplan` in `.clauderizer/config.toml`.
