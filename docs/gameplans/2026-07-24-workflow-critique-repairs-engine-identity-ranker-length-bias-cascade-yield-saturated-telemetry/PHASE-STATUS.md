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

### C-02 — Phase 5

**Phase**: 5
**What gameplan said**: Phase 5 would close by cutting 1.14.0 to PyPI; its title reads "Close-out, clean-environment verify, ship 1.14.0" and its original exit criteria named 1.14.0 in three places.
**What was actually correct**: The target is 1.13.0. A four-registry sweep found that 1.13.0 was never released: source (pyproject, __version__, CHANGELOG top) is at 1.13.0, while git tags local and remote stop at v1.12.0, the newest GitHub Release is 1.12.0 (2026-07-19), and PyPI's latest is 1.12.0. Commit 81a99f4 is titled "ship 1.13.0" and shipped nothing; two later commits built on top of it. So uvx serving 1.12.0 to the MCP client was never a cache or resolution fault — it correctly served the actual latest release, and the whole dreaming-loop tool surface has never been published. Exit criteria are corrected to 1.13.0 and now require the four-registry sweep (H-19). The phase TITLE still reads 1.14.0: no blessed op renames a phase, and hand-editing GAMEPLAN.md would violate the never-hand-edit rule, so the criteria list carries the correction and states that it is the authority.
**Why**: The plan was written from the source version and the commit message, both of which claimed 1.13.0 existed, without sweeping the remote registries first — the source-of-truth capture recorded "engine 1.13.0" as if that were a released fact rather than a local one. The gameplan's own guidance (capture real source-of-truth values, never invent them) was followed for the local legs and skipped for the three remote ones, which is exactly the H-19 gap reproduced at planning time instead of close-out time.
**Lesson**: A version in pyproject is a LOCAL fact, not a release. Before planning or claiming anything version-bearing, sweep the three REMOTE legs (git ls-remote --tags, gh release list, the PyPI JSON index) — the local trio agrees by construction because one commit edits all three, so their agreement certifies nothing about whether the artifact exists. A commit message saying "ship X" is the weakest evidence of all: it is written before the release step and never revisited if that step is skipped. Corollary for planning: a phase title cannot be corrected by any blessed op, so put version targets in exit criteria (replaceable via cz_set_exit_criteria) rather than in phase names.
