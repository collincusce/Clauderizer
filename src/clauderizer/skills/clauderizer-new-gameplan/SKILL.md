---
name: clauderizer-new-gameplan
description: Plan a new multi-phase gameplan from a goal. Use when the user wants to start a new initiative, project, or large feature and needs it broken into phases with decisions and exit criteria.
---

# Start a gameplan

1. Clarify the goal in one sentence with the user.
2. Capture real source-of-truth values first (versions, baseline test counts, account IDs) — never invent them.
3. Interrogate the goal from multiple perspectives **before** drafting phases — a single planning pass misses what no single viewpoint thinks to ask. Take each lens in turn and ask, of this specific goal, "what's missing, what will bite us, what must come first?", keeping only the findings that apply:
   - Security / data · Performance / scale · Ops / release · Testing / verification · Cost / dependencies · Failure modes · Prerequisite chains.
   Beyond the fixed lenses, derive goal-specific ones from the graph — `cz_graph_query` the entities the goal touches and let their neighbors suggest perspectives (STORM mines perspectives from related articles' outlines, not a fixed list).
   Run the lenses as a cheap fan-out — a faster model per lens is fine; reserve the strong model for the synthesis in step 5. Vet the goal against recorded memory with `cz_analyze`, and let its `adjacent` set surface graph-neighbors you haven't connected yet — gaps, not just contradictions.
4. `cz_create_gameplan` with a descriptive name. This becomes the active gameplan.
5. Synthesize the surviving findings into the plan — each becomes a `cz_add_decision` (scope `gameplan` for tactical, `project` for architectural ADRs), a phase or task, or a tracked `cz_add_open_item`. An unknown is an open item, never a silent omission.
6. Lay out phases with `cz_add_phase` and `cz_set_exit_criteria` — each session-sized (1–3 days), with a goal, dependencies, and verifiable exit criteria. 5–25 phases is typical.
7. `cz_write_handoff` for Phase 0 so the first execution session is self-contained.
8. **Commit the plan before executing.** Creating a gameplan dirties the working tree (the new gameplan dir + `docs/DECISIONS.md`/`docs/INVARIANTS.md` + the `.clauderizer/config.toml` pointer), so the first `clauderizer-do-phase` pre-flight's `clean_tree` check fails until it is committed. `git add` exactly the plan's files and commit. If unrelated pre-existing changes are also dirty, separate them into their own commit first — never fold work you did not author into the plan commit.
