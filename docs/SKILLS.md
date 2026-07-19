# Project Skills

> Agent Skills available to this project, registered with `cz_register_skill`
> (discover candidates with `cz_discover_skills`). Every future handoff surfaces
> the relevant ones, so this list stays compact: mark entries that stop earning
> their place obsolete (`cz_obsolete_skill` with the `S-NN` id). Entries are
> never deleted, only marked.

## Skills

### Category: Clauderizer workflow

**S-01.** clauderizer-amend — Change a gameplan after it has started executing. Use when scope shifts mid-flight — a phase needs a task it's missing, a dependency changed, or work must be added/removed. *(source: .claude/skills/clauderizer-amend)*

**S-02.** clauderizer-cascade — After changing a tracked entity (subsystem, feature, decision, invariant, or a status/version), walk its dependents and reconcile them. Use whenever you finish an edit that something else might depend on. *(source: .claude/skills/clauderizer-cascade)*

**S-03.** clauderizer-close-gameplan — Close out a completed (or explicitly deferred) gameplan. Use when all phases are done and the user wants to wrap up and capture what was learned. *(source: .claude/skills/clauderizer-close-gameplan)*

**S-04.** clauderizer-do-phase — Execute or continue the current gameplan phase end-to-end — pre-flight, do the work, then close out (handoff + status transitions + cascade). Use when the user says "do the next phase", "continue the gameplan", or "work on phase N". *(source: .claude/skills/clauderizer-do-phase)*

**S-05.** clauderizer-new-gameplan — Plan a new multi-phase gameplan from a goal. Use when the user wants to start a new initiative, project, or large feature and needs it broken into phases with decisions and exit criteria. *(source: .claude/skills/clauderizer-new-gameplan)*

**S-06.** clauderizer-record — Quickly capture a decision, invariant, lesson, correction, or risk into the right place. Use when the user says "remember that…", "we decided…", "note that…", or "that was a mistake, the right way is…". *(source: .claude/skills/clauderizer-record)*

**S-07.** clauderizer-onboard — Seed a freshly clauderized project's memory from its existing documentation. Use right after `clauderize init` on a repo that already has a README or design docs, when init or `clauderize upgrade` suggests onboarding, or when VISION/ARCHITECTURE are still scaffold placeholders. *(source: .claude/skills/clauderizer-onboard)*

**S-08.** clauderizer-modernize — Triage the advisory upgrade proposals cz_modernize surfaces — walk each one with the user to handle, dismiss, or defer. Use when the session digest says "N upgrade proposals awaiting triage", after `clauderize upgrade`, or when the user asks to finish/action a modernization. *(source: .claude/skills/clauderizer-modernize)*
