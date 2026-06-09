---
name: clauderizer-cascade
description: After changing a tracked entity (subsystem, feature, decision, invariant, or a status/version), walk its dependents and reconcile them. Use whenever you finish an edit that something else might depend on.
---

# Run cascade

Cascade is **post-hoc and judgment-based**: it finds what *might* be affected; you decide what actually is.

1. `cz_cascade(entity_id, transition)` — walks the Project DAG forward and writes a report listing direct + transitive dependents, each marked "needs review".
2. Open each flagged dependent. Decide: affected or not? If affected, make the edit.
3. Record every verdict with `cz_resolve_cascade(verdicts={...}, updates_applied=...)` — verdicts maps each entity id to what you did ("no change needed", "updated pin to ^2.0.0", …) and updates_applied summarizes the concrete edits. Never hand-edit the report.
4. Resolve every "needs review" marker before the session ends — a report with unresolved markers shows up as a pending cascade in `cz_status` and fails the `cascade_hygiene` pre-flight check.

Status transitions already trigger cascade via `cz_transition_status`; use this skill for manual triggers or to finish reconciling a report.
