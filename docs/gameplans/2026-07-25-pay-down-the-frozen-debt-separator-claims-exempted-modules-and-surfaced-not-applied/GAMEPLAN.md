# pay down the frozen debt — separator claims, exempted modules, and surfaced-not-applied Gameplan

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

### Phase 0: Triage the 24 separator-shaped assertions and make the class machine-rejectable

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE: each new test demonstrated RED on the pre-1.14.3 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError. Suite >= 1232 is a precondition, never a criterion
- [x] All 24 assertions matching `assert "…/…" in …` are TRIAGED and each classified in writing as a platform claim (the right-hand side is a real filesystem path) or a message assertion (a rendered string) — a count is not a triage
- [x] Every site classified as a platform claim is fixed to assert the separator-agnostic token, per L-51's rule: assert the FILE, not the slash
- [x] The CLASS is machine-rejectable, not just the instances: a check that flags a new separator-shaped assertion, ratcheted at the post-triage count so a new one has to be justified rather than merely noticed
- [x] The check is demonstrated FIRING on the exact line that shipped three Windows cells red in 1.14.2 (`"uv/archive-v0" in serving_path`), reconstructed — if it would not have caught that, it is the wrong check
- [x] False-positive floor stated honestly: message assertions must NOT be flagged, asserted by test, or the check earns its way into the ignore list

### Phase 1: Pay down the 32 exempted modules

**Goal**: Document the modules currently exempted from the doc ratchet, ratcheting modules_with_no_subsystem_doc DOWN as each lands, so the frozen debt actually shrinks instead of merely not growing.
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE: each new test demonstrated RED on the pre-1.14.3 tree BEHAVIORALLY — a probe using only APIs present on both trees, never an ImportError. Suite >= 1232 is a precondition, never a criterion
- [ ] modules_with_no_subsystem_doc shrinks from 32 — every module removed from the exemption list is genuinely documented under a subsystem doc, and the ratchet test proves it by refusing to let the list grow back
- [ ] nesting.py and engine_identity.py are documented specifically — both were written during 1.14.1/1.14.2 and landed in the blind spot the ratchet was built to close
- [ ] undocumented_per_subsystem is re-baselined DOWNWARD wherever docs improved; the both-directions ratchet already fails if a gain is not locked in
- [ ] No module is removed from the exemption list without real prose — a one-line mention that satisfies the substring check but tells a reader nothing is the false green this whole line of work exists to end

### Phase 2: Close out and ship 1.14.3 with both ratchets tighter

**Goal**: Audit, four-registry sweep, CI green pre-tag at job granularity, publish, prove by handshake, and a post-mortem answering whether a machine check at the point of the mistake changes behaviour where a surfaced lesson did not.
**Depends on**: 0, 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_audit run; mechanical findings resolved or explicitly accepted with a reason
- [ ] OPEN FINDINGS ARE ZERO at close — the register's own count, or each survivor carries a dated acceptance
- [ ] Version single-sourced across pyproject, __version__ and the top CHANGELOG entry; editable install refreshed (H-03)
- [ ] Four-registry sweep reports 1.14.3 unclaimed before any tag exists
- [ ] CI green on EVERY matrix cell plus fresh-clone, on the exact released commit, BEFORE any tag, verified at JOB granularity
- [ ] origin/main holds the release commit before any tag or Release
- [ ] Published, then PROVEN by handshake with stdin HELD OPEN (never the fire-and-close pipe whose race 1.14.2 fixed); upload evidence read in-band from the publish log
- [ ] POST-MORTEM answers the question that motivated this gameplan: L-51 was surfaced and still not applied — did adding a machine check at the point of the mistake change that, and what remains unenforced
