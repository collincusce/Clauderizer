---
name: clauderizer-modernize
description: Triage the advisory upgrade proposals cz_modernize surfaces — walk each one with the user to handle, dismiss, or defer. Use when the session digest says "N upgrade proposals awaiting triage", after `clauderize upgrade`, or when the user asks to finish/action a modernization.
---

# Triage upgrade proposals

`clauderize upgrade` applies the **mechanical** tier automatically; the **advisory**
proposals (unwired gates, untracked deliverables, un-onboarded specs, …) are the
user's to act on — the engine never writes memory or invents project facts for them
(D-042 / INVARIANT-05). This skill walks the user through those proposals one at a
time so they never pile up or get lost in scrollback.

1. **Ask first — don't hijack the session.** The digest only shows a *count*. Confirm
   the user wants to triage now: *"There are N upgrade proposals pending — go through
   them now, or keep working?"* If they'd rather work, stop; the digest reminds them
   next session.

2. **Get the pending list.** Call `cz_modernize`. It returns only the **pending**
   proposals (already-dismissed/deferred ones are filtered out), each with a stable
   `id`, a `kind`, and a `detail`. If the list is empty, say so and stop.

3. **Walk each proposal — offer handle / dismiss / defer.** Show the `detail` plainly,
   then ask which the user wants:

   - **handle** — do the work now (per-kind playbook below); the proposal disappears
     on its own once the underlying gap is closed (no bookkeeping needed).
   - **dismiss** — `cz_dismiss_proposal(id)`. It won't return unless it *materially*
     changes. Use when it doesn't apply (an intentionally gate-less campaign, a
     placeholder doc meant to stay empty).
   - **defer** — `cz_defer_proposal(id, days=N)` (default 7). Snoozes it; it returns
     after N days. Use for "not now, but remind me."

4. **Per-kind handle playbook** (only for proposals the user chose to handle):

   - **unwired_gates** — create/edit `.clauderizer/preflight.<kind>.toml` with a
     `[gates]` table (`gate = "shell command"`, passes on exit 0). Infer each command
     from the repo's own scripts where you can (grep for a validator matching the gate
     name); where you can't, stub it with a `# TODO` and the exact gate name and ask
     what validates it. **Never guess a validation command into place as if real.**
   - **no_deliverables** — read the gameplan's phases / spec docs, *propose* one
     `deliverable` per execution unit, and only after the user confirms record each
     with `cz_upsert_entity(type='deliverable', fields={'gameplan': '<gid>'})`.
     Propose from what the docs actually say — never invent units.
   - **unseeded_docs** — invoke the **clauderizer-onboard** skill; it reads the
     existing specs and seeds VISION/ARCHITECTURE/memory (the engine never writes that
     prose for you).
   - **no_standing_conditions** — help declare threshold probes in
     `.clauderizer/conditions.<gid>.toml` (loop-gameplan docs).
   - **stale_kind_overlay** — add the `[lifecycle]` table to the overlay, or delete
     the overlay if it no longer customizes anything.
   - **near_dup_invariants** — if one restates a single gameplan's rule, record future
     ones with `scope='gameplan:<id>'`; append-only history stays.

5. **Recap.** Summarize what was handled, dismissed, and deferred. Handled gaps won't
   reappear; dismissed ones are gone until they change; deferred ones return on their
   date.

**Constitution:** you *propose*, the user *decides* — never auto-write memory or a gate
command the user has not approved (INVARIANT-05). Dismiss/defer are recorded in a
per-user, gitignored ledger (`.clauderizer/proposals.local.toml`, D-052).
