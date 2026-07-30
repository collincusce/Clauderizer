# Chat Handoff Index — workflow critique repairs — engine identity, ranker length bias, cascade yield, saturated telemetry

> Last updated: 2026-07-24
> Status: Phase 0 ready

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 0

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Engine identity — doctor certifies what it launched | ⬜ READY | — | — | handoffs/PHASE-0-HANDOFF.md |
| 1 | Pre-flight stops arming its own failure; the baseline stops lying | ⬜ NOT STARTED | — | — | handoffs/PHASE-1-HANDOFF.md |
| 2 | Adversarial ranking fixture — build the measuring stick before the fix | ⬜ NOT STARTED | — | — | handoffs/PHASE-2-HANDOFF.md |
| 3 | Length-normalize the ranker and break the corpus ratchet | ⬜ NOT STARTED | — | — | handoffs/PHASE-3-HANDOFF.md |
| 4 | Cascade self-resolves and stops blocking; utility scoring is parked | ⬜ NOT STARTED | — | — | handoffs/PHASE-4-HANDOFF.md |
| 5 | Close-out, clean-environment verify, ship 1.14.0 | ⬜ NOT STARTED | — | — | handoffs/PHASE-5-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

_(None yet.)_

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** A malformed tool-call argument lands in append-only memory as permanent render damage, because append-only plus never-hand-edit leaves no repair path — only a correction beside it. Validation is asymmetric: markup that displaces a required field is rejected harmlessly, while markup inside a present field writes clean-looking success over mangled content. Two cheap guards: reject argument values containing tool-call markup at write time (no legitimate ADR body contains a closing field tag), and re-read the RENDERED entry after any long structured write rather than trusting the ok:true result.

**2.** A version in pyproject is a LOCAL fact, not a release. Before planning or claiming anything version-bearing, sweep the three REMOTE legs (git ls-remote --tags, gh release list, the PyPI JSON index) — the local trio agrees by construction because one commit edits all three, so their agreement certifies nothing about whether the artifact exists. A commit message saying "ship X" is the weakest evidence of all: it is written before the release step and never revisited if that step is skipped. Corollary for planning: a phase title cannot be corrected by any blessed op, so put version targets in exit criteria (replaceable via cz_set_exit_criteria) rather than in phase names.

**3.** Consolidating lessons can delete the one clause that mattered. L-50 absorbed L-39 and dropped its watch-out about length-normalization breaking supersession-demotion's exact-tie secondary sort; the source was then marked obsolete, so the warning that would have prevented a defective change survived only where readers are told not to look. Before marking a source obsolete, diff the synthesis against it clause by clause and carry forward every falsifiable, mechanism-specific warning — those are the clauses that read as noise during consolidation and are precisely what a future change trips over. A coverage gate that only checks the synthesis still RETRIEVES for the source's own tokens cannot detect this: retrieval survived while the load-bearing clause did not.

**4.** For any git analysis with a PATH FILTER, pass --full-history: default history simplification silently drops merges that are TREESAME to one parent for the filtered path — which is exactly the lost-update shape a merge-integrity audit hunts, so the default flag set is blind to precisely the merges such an audit exists to catch. Detailed design vetting did not name this; only executing the real surface against a real fixture did (L-66) — the first seeded fixture returned empty and the flag was found live. *(evidence: merge_audit.py --full-history comment; P4 outputs; dream distillation 2026-07-28)*

**5.** Two agent-editing/setup hazards from the alpha build, both silent-by-shape: (1) when Edit-inserting a helper ABOVE an existing decorated function, anchor old_string on the DECORATOR line, never the def line — an anchor starting at `def X(` cannot see the decorator above it, so the insertion lands between the decorator and its target, silently re-targeting the decorator onto the new helper. (2) Clauderizing $HOME is categorically different from clauderizing a project: HOME/.claude/settings.json IS the per-user Claude Code settings file, so a session-start hook wired there becomes GLOBAL to every session on the machine, and every project clauderized under it becomes a nested install for INVARIANT-08 dedup purposes — init warning candidate for 2.0.0a2. *(evidence: dream distillations 2026-07-28 (Edit-decorator near-miss at ops.py _echoed insertion; HOME-wiring observation))*

**6.** A fix that only reaches FRESH installs reaches nobody — every install in the world has already run the installer, so any change to what the installer produces needs a second delivery path for existing state, plus a detector for the gap. Test the UPGRADE, not just the fresh install: smoke-testing a release into a new repo cannot see this class at all. The shape is always a stale-but-non-empty per-repo record that the merge logic prefers over the new default (a modules list, an enabled-checks list, a hosts list): `existing.X or defaults.X` keeps the old value forever, and the scaffolder reads only the record, so the new asset never lands while the refreshed engine-owned wiring references it by path. Two rules. (1) Ship the delivery: an additive, write-only-if-absent, idempotent action in the upgrade path's mechanical tier — never clobbering, and recording the change in the repo's own record so it happens once. (2) Ship the detector (D-069) at BOTH altitudes: a per-repo check that the engine's own wiring never points at an asset this repo lacks, and a CI-time ratchet that engine wiring may only reference assets some manifest actually delivers — the ratchet is what catches it before release rather than in the field. Arming a guard on the pre-fix tree needs the import path PINNED (PYTHONPATH), because an editable install serves the FIXED source into a pre-fix worktree and every test passes for the wrong reason (H-27's class, met while arming a guard against it). *(evidence: 2.0.0: live 1.13.0→2.0 walk with the published 1.13.0 wheel found docs/GLOSSARY.md + docs/ENFORCEMENT.md referenced by CLAUDE.md/AGENTS.md and the fleet skill, delivered to neither — 77b5135 had fixed the class for fresh init only; doctor printed "✓ corpus modernized" over it. Second occurrence of the class (D-067's ensure_gitignore_current was the first, and its own code comment states the law it did not generalize). CI ratchet armed against 77b5135^, where it fails naming docs/ENFORCEMENT.md from the shipped stanza.)*
