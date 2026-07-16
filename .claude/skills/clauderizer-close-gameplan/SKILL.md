---
name: clauderizer-close-gameplan
description: Close out a completed (or explicitly deferred) gameplan. Use when all phases are done and the user wants to wrap up and capture what was learned.
---

# Close a gameplan

1. Confirm every phase is complete or explicitly deferred (`cz_status`).
2. Run a full cascade pass; resolve any pending reports with `cz_resolve_cascade`.
3. **Curate the lessons** — this is where memory earns its keep:
   - `cz_promote_lesson` the few that should outlive this gameplan (they land in
     `docs/LESSONS.md` and ride in every future handoff, across gameplans).
     Promotion is a chance to distill: pass `text` to tighten the wording.
   - `cz_consolidate_lessons` overlapping ones first, then promote the synthesis.
   - The rest stay archived with the closed gameplan — promote deliberately, not in bulk.
4. Update project-level docs (CHANGELOG, ARCHITECTURE, REQUIREMENTS) to reflect final state.
5. **Self-audit your work (`cz_audit`).** Before you write the post-mortem, run
   the work/release self-audit gate. It surfaces the failure modes a green test
   suite does not catch — the ones this system has actually shipped:
   - **Mechanical findings** — resolve each or record why it's acceptable: version
     single-sourcing (pyproject vs the package `__version__` vs the top CHANGELOG
     entry — a mismatch a stale editable install hides), an uncommitted working
     tree, unresolved cascades/open items.
   - **Judgment checklist** — affirm each: did you verify in a **clean environment**
     (fresh venv / cleared cache), not just your working install? Did you re-audit
     every **consumer** of a changed entity, including untracked ones (uninstall,
     CLI, docs claims)? Do your docs/guides claim only what you **verified**?
   It is advisory (INVARIANT-05) and never blocks — but its findings belong in the
   post-mortem's "what didn't / procedure improvements".
6. Write a `POST-MORTEM.md` in the gameplan dir. Outline before you write — list the sections and what each must cover (what worked; what didn't, with root causes; procedure improvements; open threads), then synthesize each from the gameplan's outputs, corrections, lessons, and the `cz_audit` findings. Outline-before-synthesize is how STORM keeps long-form writing complete — and the post-mortem is where the system itself gets better.
7. Leave the gameplan directory on disk (nothing is deleted) and clear/replace `active_gameplan` in `.clauderizer/config.toml`.
