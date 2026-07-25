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

### C-03 — Phase 3

**Phase**: 3
**What gameplan said**: D-061 recorded that relevance ranking should be length-normalized, citing 7 never-surfaced lessons including L-61 as evidence that short lessons are crowded out, and named Jaccard normalization as the fix. Phase 3 was to land it.
**What was actually correct**: The named fix is withdrawn and D-061 is superseded. Three evidence errors: the live never-surfaced roster is 6, not 7 (L-11, L-24, L-52, L-56, L-57, L-62); L-61 is not among them and at 1,262 characters is the 5th LONGEST of 25 active lessons, so it was evidence against the claim it was cited for; and the headline probe was attributed to a gameplan whose phase query is empty, so it cannot have produced that output. Decisively, the fix would have broken a working guarantee: analyze.py sorts on (-score, stale, id) and superseded-entry demotion fires only on EXACT score equality, so normalization collapses 3,222 tied slots to 116 (~96%), failing tests/test_supersession.py — the only two tests in 1002 that catch it. A superseded decision would begin outranking its replacement. The improvement is also unsupported: McNemar exact p = 0.1250 against a length-neutral external label, and the repo's pre-registered benchmark cannot score it (fixture entries span 8-10 tokens against a live corpus spanning 37-166). The OBSERVATION survives on better evidence — Spearman +0.868 between length and surfacing over 220 real phase queries through the real handoff path — but it is a DROP defect, not an ordering defect: RELEVANCE_K = 5 discards lessons rather than reordering them. Restoring full propagation returns the ranker to being a pointer, which is what D-013 always required, and reduces this to display ordering.
**Why**: D-061 was recorded from subagent evidence without verifying it at the point of edit, which is exactly what L-33 exists to prevent, and it was the one proposal exempted from D-064 rule 1 despite resting entirely on this repo's 25-lesson single-author corpus. The deeper cause is a memory failure rather than an analysis failure: L-39 carried the only recorded description of this precise hazard — that length-normalization breaks the stale-vs-current secondary-sort tie supersession-demotion relies on, and needs a length-adversarial fixture before it can be called safe — and L-50 absorbed L-39 while dropping that clause. L-39 is now marked obsolete, so the single most relevant warning was reachable only in an entry the corpus instructs readers to ignore.
**Lesson**: Consolidating lessons can delete the one clause that mattered. L-50 absorbed L-39 and dropped its watch-out about length-normalization breaking supersession-demotion's exact-tie secondary sort; the source was then marked obsolete, so the warning that would have prevented a defective change survived only where readers are told not to look. Before marking a source obsolete, diff the synthesis against it clause by clause and carry forward every falsifiable, mechanism-specific warning — those are the clauses that read as noise during consolidation and are precisely what a future change trips over. A coverage gate that only checks the synthesis still RETRIEVES for the source's own tokens cannot detect this: retrieval survived while the load-bearing clause did not.
