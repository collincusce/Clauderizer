---
name: clauderizer-new-gameplan
description: Plan a new multi-phase gameplan from a goal. Use when the user wants to start a new initiative, project, or large feature and needs it broken into phases with decisions and exit criteria.
---

# Start a gameplan

1. Clarify the goal in one sentence with the user.
2. Capture real source-of-truth values first (account IDs, versions, baseline test counts) — never invent them.
3. `cz_create_gameplan` with a descriptive name. This becomes the active gameplan.
4. Record the decisions that shape it with `cz_add_decision` (scope `gameplan` for tactical, `project` for architectural ADRs).
5. Lay out phases with `cz_add_phase` — each session-sized (1–3 days), with a goal, dependencies, and verifiable exit criteria. 5–25 phases is typical.
6. `cz_write_handoff` for Phase 0 so the first execution session is self-contained.
