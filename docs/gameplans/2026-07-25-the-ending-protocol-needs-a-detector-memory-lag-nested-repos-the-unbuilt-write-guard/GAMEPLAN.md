# the ending protocol needs a detector — memory lag, nested repos, the unbuilt write guard Gameplan

> Created: 2026-07-25
> Status: Planning
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

### Phase 0: Memory-lag detection so a session cannot silently drift from the repo

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.1 tree before it goes green. Suite >= 1074 is a precondition, never a criterion
- [ ] `clauderize status` emits a memory-lag line when the focus gameplan's current phase has non-docs commits landed after its last recorded state change, naming the phase and the commit count
- [ ] The line is CONDITIONALLY emitted: byte-identical digest to 1.14.0 when there is no lag (INVARIANT-08), asserted by test
- [ ] cz_preflight surfaces the same signal as an advisory check that never fails the ritual (INVARIANT-05, D-024 keeps preflight blocking for its OWN checks)
- [ ] Reproduction test: a fixture repo with a phase marked not_started and a commit touching src/ afterwards produces the signal; the same repo with the phase recorded produces nothing
- [ ] The signal derives from evidence actually read — git log, not the tracker asserting itself (D-065). No persisted flag, no config key (INVARIANT-05/D-015)
- [ ] Historical check: run it against this repo's own history at eac1c9a, where phases 5 and 6 were implemented while the tracker read not-started, and assert it would have fired
- [ ] H-22 resolved with the shipped evidence

### Phase 1: Nested clauderized repos stop contradicting each other

**Goal**: Two installs must not both inject status, and the outer one must never announce 'No active gameplan' about the repo the session is working in (H-23, INVARIANT-08).
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE: demonstrated red first
- [ ] With a clauderized ancestor present, the INNER repo's hook emits the digest and the outer emits nothing — asserted by test with two nested fixture repos
- [ ] `clauderize doctor` names a detected nested install by path, since the outer stanza and wiring rot invisibly and nothing else reports it
- [ ] `clauderize init` inside an existing clauderized repo warns rather than silently creating a second install
- [ ] Hooks stay read-only and exit 0 throughout (INVARIANT-06); the dedup remains in-memory and session-scoped, never a persisted flag (INVARIANT-08/INVARIANT-05)
- [ ] Verified live on this machine: /home/ccusce is a clauderized repo containing /home/ccusce/Clauderizer — a session in the inner repo must receive exactly ONE digest
- [ ] H-23 resolved with the shipped evidence

### Phase 2: Build the write guard 1.14.0 specified and did not ship

**Goal**: Reject tool-call markup in structured-write argument values at the mutations render boundary, with the four already-corrupted live entries as acceptance cases.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE: demonstrated red first
- [ ] A structured-write argument containing tool-call markup (a closing field tag, or `<parameter name=`) is rejected or neutralized at the mutations render boundary — no legitimate ADR, finding, correction or lesson body contains one
- [ ] The four live corrupted entries are the acceptance cases: docs/DECISIONS.md D-052 and D-062, docs/HARDENING.md H-19 and H-23. A test asserts the guard would have caught each
- [ ] Consistent with D-066: NORMALIZE, never reject where neutralizing is possible, so no write is lost (INVARIANT-03) and no mutation gains a hard block (INVARIANT-05)
- [ ] The four existing occurrences are NOT retro-edited — append-only (INVARIANT-03), they parse, and they are the acceptance corpus. Repair belongs to the amendment op, still deferred
- [ ] A test asserts the guard fires on the exact shapes that landed: `</consequences>`, `</context>`, `</root_cause>`, `</impact>`, and a bare `<parameter name=` line

### Phase 3: Close the graph drop gap and the init spawn-test carried from 1.14.0

**Goal**: model.from_file stops returning a bare None for an unreadable entity doc, and init spawn-tests the portable command it actually writes (tasks 5.2 and 4.6).
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] STANDING ORACLE: demonstrated red first
- [ ] model.from_file returns a drop record rather than a bare None; graph.index.build accumulates drops AND duplicate-id collisions, both surfaced in cz_corpus_health and doctor
- [ ] A BOM'd entity doc under docs/ yields a non-zero drop count naming the path, and entities_indexed + dropped == entities_on_disk
- [ ] cz_cascade on an entity that is not in the graph returns ok:false with 'unknown entity', not ok:true with zero dependents — the current behavior makes a dropped doc indistinguishable from one with no edges, which silently voids D-018
- [ ] init spawn-tests the PORTABLE command it is about to write, as report.warnings and never WiringRefused — an offline or proxied first run must still install
- [ ] Suite green; no regression in the 1.14.0 behavior any of these touch

### Phase 4: Close out and ship 1.14.1

**Goal**: Audit, doc sweep, clean-environment verify, publish, and prove the published artifact serves what the digest advertises.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_audit run; mechanical findings resolved or explicitly accepted with a reason; the judgment checklist affirmed
- [ ] The remote-registry sweep shipped in 1.14.0 reports 1.14.1 unclaimed before any tag exists
- [ ] Version single-sourced across pyproject, __version__ and the top CHANGELOG entry; the editable install refreshed so dist-info matches (H-03 turned 15 tests red in 1.14.0 for exactly this)
- [ ] CI green on EVERY matrix cell plus the fresh-clone leg, on the exact commit being released, BEFORE any tag exists (L-51 sweep 2)
- [ ] origin/main holds the release commit before any tag or GitHub Release
- [ ] Published to PyPI, then PROVEN: plain `uvx --from clauderizer[mcp] clauderizer-mcp` returns serverInfo 1.14.1 with the full tool surface. Read the publish job log for in-band upload evidence — the index lags, so a fresh negative is unproven, not failed
- [ ] POST-MORTEM.md written, and it answers whether D-069's standing test (name the detector at design time) actually changed how this gameplan was executed
