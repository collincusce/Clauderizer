# workflow critique repairs — engine identity, ranker length bias, cascade yield, saturated telemetry — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-07-24

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Engine identity — doctor certifies what it launched | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pre-flight stops arming its own failure; the baseline stops lying | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Adversarial ranking fixture — build the measuring stick before the fix | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Length-normalize the ranker and break the corpus ratchet | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Cascade self-resolves and stops blocking; utility scoring is parked | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, clean-environment verify, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

## Outputs Registry

_(Concrete values produced by completed phases that later phases need.)_

## Corrections Log

### C-01 — Phase 0

**Phase**: 0
**What gameplan said**: D-062 would be recorded with a clean Consequences field and a separate Evidence line, like D-060/D-061/D-063.
**What was actually correct**: D-062's Consequences field in docs/DECISIONS.md ends with a literal closing tag followed by a raw tool-call parameter fragment: a malformed call put the evidence text inside the consequences argument instead of its own field. The content is all present and correct — the 0-of-123 cascade measurement reads normally after the stray markup — but the entry renders with XML noise and has no structured Evidence line. Not repaired in place: docs/DECISIONS.md is append-only (INVARIANT-03) and the cz_* surface has no amend-an-entry operation, so hand-editing it would violate the blessed-writes rule this project exists to enforce.
**Why**: Author error in the tool call, not an engine defect. It surfaces a real gap: every mutation surface here is append-or-add-new, so a malformed WRITE has no sanctioned repair path — only a correction beside it or a superseding entry. Note the asymmetry the same session demonstrated twice: when the malformed markup replaced a REQUIRED field the schema rejected the call outright and nothing was written, but when it rode inside an otherwise-valid required field the write succeeded and the damage persisted. Validation catches missing fields, not markup smuggled into present ones.
**Lesson**: A malformed tool-call argument lands in append-only memory as permanent render damage, because append-only plus never-hand-edit leaves no repair path — only a correction beside it. Validation is asymmetric: markup that displaces a required field is rejected harmlessly, while markup inside a present field writes clean-looking success over mangled content. Two cheap guards: reject argument values containing tool-call markup at write time (no legitimate ADR body contains a closing field tag), and re-read the RENDERED entry after any long structured write rather than trusting the ok:true result.
