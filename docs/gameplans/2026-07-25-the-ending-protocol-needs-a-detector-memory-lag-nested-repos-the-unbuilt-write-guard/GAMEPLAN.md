# the ending protocol needs a detector — memory lag, nested repos, the unbuilt write guard Gameplan

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

### A-001 — 1.14.1 is staged, not shipped — the release halts before every irreversible step

- **Date**: 2026-07-25
- **Affected sections in GAMEPLAN.md**: Phase Breakdown (Phase 4), CHANGELOG.md, POST-MORTEM.md
- **Affected phases**: 4
- **Triggered by**: User decision at the release boundary: asked how far to take the release with everything staged and green, the answer was "Stop here — nothing leaves this machine."
- **What changed**: Phase 4 delivers its non-irreversible half and stops. DONE: cz_audit run with both mechanical findings accepted with reasons and all four judgment checks affirmed; the four-registry sweep confirming v1.14.1 unclaimed on the remote tag, GitHub Releases and PyPI; version single-sourced across pyproject / __version__ / the top CHANGELOG entry with the editable install refreshed so dist-info matches (H-03); README documenting the two user-visible behaviors; POST-MORTEM.md written and grading D-069's standing test. NOT DONE, and left unchecked rather than waived: CI green on every matrix cell on the released commit, origin/main holding the release commit, and the PyPI publish plus its uvx serverInfo proof. The release commit a4784e3 sits on local main, unpushed. CHANGELOG's top entry is headed "1.14.1 — UNRELEASED (staged 2026-07-25)" so the corpus never claims a release that does not exist. Phase 4 stays in_progress; the gameplan stays open.
- **Why**: Publishing is irreversible and outward-facing, and the standing preference on this project is that tag/push/publish are confirmed rather than assumed — "do all phases" scopes the work, it does not pre-authorize the release. Recording this as an amendment rather than checking the criteria off is the same discipline the release itself is about (D-069): a criterion that was not met must read as not met. Leaving the phase in_progress with the resume sequence recorded is also what makes the memory-lag detector shipped in Phase 0 correct about this repo — a phase marked complete while the release is unshipped would be precisely the drift it exists to catch.

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
- [x] STANDING ORACLE (every phase): each new test is demonstrated RED on the pre-1.14.1 tree before it goes green. Suite >= 1074 is a precondition, never a criterion
- [x] `clauderize status` emits a memory-lag line when the focus gameplan's current phase has non-docs commits landed after its last recorded state change, naming the phase and the commit count
- [x] The line is CONDITIONALLY emitted: byte-identical digest to 1.14.0 when there is no lag (INVARIANT-08), asserted by test
- [x] cz_preflight surfaces the same signal as an advisory check that never fails the ritual (INVARIANT-05, D-024 keeps preflight blocking for its OWN checks)
- [x] Reproduction test: a fixture repo with a phase marked not_started and a commit touching src/ afterwards produces the signal; the same repo with the phase recorded produces nothing
- [x] The signal derives from evidence actually read — git log, not the tracker asserting itself (D-065). No persisted flag, no config key (INVARIANT-05/D-015)
- [x] Historical check: run it against this repo's own history at eac1c9a, where phases 5 and 6 were implemented while the tracker read not-started, and assert it would have fired
- [x] H-22 resolved with the shipped evidence

### Phase 1: Nested clauderized repos stop contradicting each other

**Goal**: Two installs must not both inject status, and the outer one must never announce 'No active gameplan' about the repo the session is working in (H-23, INVARIANT-08).
**Depends on**: Phase 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE: demonstrated red first
- [x] With a clauderized ancestor present, the INNER repo's hook emits the digest and the outer emits nothing — asserted by test with two nested fixture repos
- [x] `clauderize doctor` names a detected nested install by path, since the outer stanza and wiring rot invisibly and nothing else reports it
- [x] `clauderize init` inside an existing clauderized repo warns rather than silently creating a second install
- [x] Hooks stay read-only and exit 0 throughout (INVARIANT-06); the dedup remains in-memory and session-scoped, never a persisted flag (INVARIANT-08/INVARIANT-05)
- [x] Verified live on this machine: /home/ccusce is a clauderized repo containing /home/ccusce/Clauderizer — a session in the inner repo must receive exactly ONE digest
- [x] H-23 resolved with the shipped evidence

### Phase 2: Build the write guard 1.14.0 specified and did not ship

**Goal**: Reject tool-call markup in structured-write argument values at the mutations render boundary, with the four already-corrupted live entries as acceptance cases.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE: demonstrated red first
- [x] A structured-write argument containing tool-call markup (a closing field tag, or `<parameter name=`) is rejected or neutralized at the mutations render boundary — no legitimate ADR, finding, correction or lesson body contains one
- [x] The four live corrupted entries are the acceptance cases: docs/DECISIONS.md D-052 and D-062, docs/HARDENING.md H-19 and H-23. A test asserts the guard would have caught each
- [x] Consistent with D-066: NORMALIZE, never reject where neutralizing is possible, so no write is lost (INVARIANT-03) and no mutation gains a hard block (INVARIANT-05)
- [x] The four existing occurrences are NOT retro-edited — append-only (INVARIANT-03), they parse, and they are the acceptance corpus. Repair belongs to the amendment op, still deferred
- [x] A test asserts the guard fires on the exact shapes that landed: `</consequences>`, `</context>`, `</root_cause>`, `</impact>`, and a bare `<parameter name=` line

### Phase 3: Close the graph drop gap and the init spawn-test carried from 1.14.0

**Goal**: model.from_file stops returning a bare None for an unreadable entity doc, and init spawn-tests the portable command it actually writes (tasks 5.2 and 4.6).
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] STANDING ORACLE: demonstrated red first
- [x] model.from_file returns a drop record rather than a bare None; graph.index.build accumulates drops AND duplicate-id collisions, both surfaced in cz_corpus_health and doctor
- [x] A BOM'd entity doc under docs/ yields a non-zero drop count naming the path, and entities_indexed + dropped == entities_on_disk
- [x] cz_cascade on an entity that is not in the graph returns ok:false with 'unknown entity', not ok:true with zero dependents — the current behavior makes a dropped doc indistinguishable from one with no edges, which silently voids D-018
- [x] init spawn-tests the PORTABLE command it is about to write, as report.warnings and never WiringRefused — an offline or proxied first run must still install
- [x] Suite green; no regression in the 1.14.0 behavior any of these touch

### Phase 4: Close out and ship 1.14.1

**Goal**: Audit, doc sweep, clean-environment verify, publish, and prove the published artifact serves what the digest advertises.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [x] cz_audit run; mechanical findings resolved or explicitly accepted with a reason; the judgment checklist affirmed
- [x] The remote-registry sweep shipped in 1.14.0 reports 1.14.1 unclaimed before any tag exists
- [x] Version single-sourced across pyproject, __version__ and the top CHANGELOG entry; the editable install refreshed so dist-info matches (H-03 turned 15 tests red in 1.14.0 for exactly this)
- [ ] CI green on EVERY matrix cell plus the fresh-clone leg, on the exact commit being released, BEFORE any tag exists (L-51 sweep 2)
- [ ] origin/main holds the release commit before any tag or GitHub Release
- [ ] Published to PyPI, then PROVEN: plain `uvx --from clauderizer[mcp] clauderizer-mcp` returns serverInfo 1.14.1 with the full tool surface. Read the publish job log for in-band upload evidence — the index lags, so a fresh negative is unproven, not failed
- [x] POST-MORTEM.md written, and it answers whether D-069's standing test (name the detector at design time) actually changed how this gameplan was executed
