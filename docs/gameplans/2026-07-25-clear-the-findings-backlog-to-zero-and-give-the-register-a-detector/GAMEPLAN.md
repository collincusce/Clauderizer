# clear the findings backlog to zero and give the register a detector Gameplan

> Created: 2026-07-25
> Status: Executing
> Kind: driven
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

_(1–2 paragraphs: what this gameplan accomplishes.)_

## Subsystems Touched

_(list the subsystems/features this gameplan affects.)_

## Source-of-Truth Captures

_(Real values captured from real systems at gameplan start. Authority over the
gameplan body. Account IDs, ARNs, baseline test counts, versions.)_

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

_(Auto-numbered O-NN via cz_add_open_item; close with cz_resolve_open_item. Blockers and cross-phase questions — unresolved ones surface in cz_status and when a phase is completed.)_

## Phase Breakdown

### Phase 0: Engine identity — the digest says when it is not the build the working tree describes

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.2 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError (gameplan lesson 2 of the 1.14.1 plan). Suite >= 1164 is a precondition, never a criterion
- [x] cz_status surfaces it when the module serving the call is NOT the working tree's source — compare the running clauderizer.__file__ location and __version__ against the repo's src/, which the process already has in hand; no subprocess, no handshake needed for the self-check
- [x] Silent for an ordinary consumer: a repo with no src/clauderizer, or a served build that IS the working tree, emits zero bytes (INVARIANT-08) — asserted by test on both
- [x] The uvx case is the one that must fire: a served build resolving outside the repo while src/clauderizer exists is named, with the served version and the tree's version both shown
- [x] Honest about scope in the module docstring: this detects the SERVING process, and says plainly what it cannot see
- [x] H-27 resolved with the shipped evidence, including a replay of the exact conditions that produced the corrupt H-26

### Phase 1: Planning surfaces the lessons that govern planning (H-25)

**Goal**: Rank project lessons against a new gameplan's GOAL at plan time, the way handoff.assemble already does per phase, so lessons about planning can reach planning at all.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.2 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError (gameplan lesson 2 of the 1.14.1 plan). Suite >= 1164 is a precondition, never a criterion
- [x] cz_create_gameplan returns ranked project lessons for the gameplan's GOAL text — read-only, advisory, a pointer not an authority (D-013/INVARIANT-05); it never blocks or edits the plan
- [x] The never-surfaced set shrinks for a real reason: after this, a planning-relevant lesson (L-11's synthesis among them) can be surfaced by the ranker at plan time — asserted by test, not assumed
- [x] Telemetry records the surfacing through the same blessed path handoff.assemble uses, so lesson-utility scoring sees plan-time surfacings and a future never-surfaced judgment is sound
- [x] H-25 resolved; the finding's own claim that five lessons were unreachable is re-measured and the new number recorded

### Phase 2: The digest nudges on the cost it names, and the register stops being write-only (H-26 + the aging detector)

**Goal**: Warn on the lesson block's token contribution rather than an entry count, and surface how long an open finding has been open so an aged finding stops reading like a fresh one.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.2 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError (gameplan lesson 2 of the 1.14.1 plan). Suite >= 1164 is a precondition, never a criterion
- [x] The memory warning fires on the lesson block's estimated TOKEN contribution — the gauge already computes handoff_est_tokens — with the entry count demoted to a secondary detail
- [x] Re-measured against the 1.14.1 re-distill: the corpus that went 26 -> 20 entries while growing 1.1% in bytes must now read as NOT improved, which is the whole point of H-26
- [x] An open finding's AGE is surfaced (opened date vs today, or releases since), so an aged finding stops reading identically to a fresh one — conditionally emitted, quiet when the register is young
- [x] Zero bytes when there is nothing to say; the golden single-gameplan digest test is updated deliberately, never loosened
- [x] H-26 resolved

### Phase 3: Two core-path lows: a symlinked parent directory, and a gameplan that cannot be closed (H-16 + H-21)

**Goal**: Resolve the whole parent chain in the atomic writer, not just the leaf; and give the phase-row vocabulary the deferred/superseded state the close ritual already names.
**Depends on**: Phase 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.2 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError (gameplan lesson 2 of the 1.14.1 plan). Suite >= 1164 is a precondition, never a criterion
- [ ] writer.write_atomic refuses a target whose PARENT chain contains a symlink, not merely a symlinked leaf — with a test that plants a symlinked parent directory and asserts the write is refused and nothing escapes the repo (L-29: prove the isolation)
- [ ] The phase-row vocabulary gains the deferred/superseded state the close ritual already names, threaded through _tables._STATUS_WORDS, the lifecycle derivation and the portfolio open/closed computation so all three agree
- [ ] A superseded gameplan can actually be closed end-to-end — asserted by test, since H-21's whole point is that the documented path is unreachable
- [ ] H-16 and H-21 resolved

### Phase 4: Subsystem docs get an executable seam against their module (H-24)

**Goal**: An advisory test asserting each docs/subsystems/<name>.md still names its module's load-bearing public callables, derived from source so the assertion cannot itself go stale.
**Depends on**: Phase 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.2 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError (gameplan lesson 2 of the 1.14.1 plan). Suite >= 1164 is a precondition, never a criterion
- [ ] A test asserts each docs/subsystems/<name>.md mentions its module's load-bearing public callables, DERIVED from the source rather than hand-listed so the assertion cannot go stale as the code moves
- [ ] Advisory in spirit: prose need not name every private helper, so the check targets whole missing CONTRACTS — the D-066 boundary going a release undocumented is the acceptance case
- [ ] It fails on that acceptance case when run against the pre-1.14.1 tree, and passes on the current one
- [ ] H-24 resolved

### Phase 5: Close out and ship 1.14.2 with the backlog at zero

**Goal**: Audit, doc sweep, the four-registry sweep, CI green pre-tag on the exact commit, publish, prove by handshake, and a post-mortem that answers whether an empty register stays empty.
**Depends on**: 0, 1, 2, 3, 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_audit run; mechanical findings resolved or explicitly accepted with a reason; the judgment checklist affirmed
- [ ] OPEN FINDINGS ARE ZERO — the register's own count, not a claim; if any finding survives it carries a dated disposition explaining why it is accepted rather than fixed
- [ ] Version single-sourced across pyproject, __version__ and the top CHANGELOG entry; editable install refreshed so dist-info matches (H-03)
- [ ] The four-registry sweep reports 1.14.2 unclaimed before any tag exists
- [ ] CI green on EVERY matrix cell plus the fresh-clone leg, on the exact commit being released, BEFORE any tag exists, verified at JOB granularity (L-51 sweep 2)
- [ ] origin/main holds the release commit before any tag or GitHub Release
- [ ] Published, then PROVEN by handshake: plain uvx --refresh returns serverInfo 1.14.2 with the full tool surface; upload evidence read in-band from the publish log
- [ ] POST-MORTEM answers the question this gameplan exists to test: does a register emptied to zero STAY at zero, or does the next release refill it — and if it refills, is that healthy discovery or the same rot one level up
