# Workflow-Critique Repairs — Post-Mortem

> Author: Claude Opus 5 session, 2026-07-24/25
> Date: 2026-07-25
> Scope: Planned 2026-07-24, superseded the same day before Phase 0 executed.
> Disposition: **CLOSED — SUPERSEDED** by `2026-07-24-evidence-traversal-1-14-0`.
> Zero phases executed. No code shipped under this gameplan.

## Executive Summary

This gameplan was planned from a single session's reading of the system and
superseded within hours by a six-agent audit and a sixteen-agent
reconcile/refute/architect/judge workflow. Two of its four decisions survive
(D-060 amended, D-063 to be implemented as already written); one was superseded
before execution (D-062 → D-064); one had its named fix withdrawn on evidence
that it would have **broken a working guarantee** (D-061 → C-03).

Closing it is the honest disposition. Its premise was not merely incomplete —
Phase 2/3's hypothesis was refuted at p = 0.1250 and Phase 4's mechanism was
impossible (cascade runs inside the closing protocol, *before* any commit
exists, so "auto-resolve same-commit dependents" resolves zero). Amending a
refuted premise would have produced a plan whose amendment history was longer
than its content.

**What it produced that outlives it:** four project decisions, three
corrections, two hardening findings (H-19, H-20), the documentation truth
repair shipped in `26195ab`, and the release of 1.13.0 — which had sat
unreleased in the working tree since the day before, with commit `81a99f4`
titled "ship 1.13.0."

## What the Gameplan Got Right

### 1. It found real defects, and the severe ones survived adversarial refutation
Five independent skeptics were tasked with killing the findings. The write-path
injection, non-atomic writes, symlink escape, findings-register mis-parse,
zero-telemetry corpus wipe, and doctor false-greens all survived. Those are now
Phases 0–5 of the successor.

### 2. Releasing 1.13.0 first was the right sequencing call
The user's instruction to ship 1.13.0 before starting the repair work was
correct and non-obvious. It unblocked the five dream tools for every consumer,
gave the successor a clean 1.14.0 target, and — because the release ritual was
executed rather than described — surfaced H-19: `cz_audit` certifies "version
single-sourced" from three local sources that one commit edits together, so it
passes on a version that exists on **zero** remote registries.

### 3. Recording decisions before executing them made the supersession cheap
Because D-060 through D-063 were written down with their evidence, the audit
could attack the *evidence* rather than re-litigate the conclusions. C-03 is a
precise record of exactly which clause of D-061 failed and why. Had the work
been done first and recorded after, the ranker change would have shipped.

## What the Gameplan Got Wrong

### 1. D-061 was recorded on unverified subagent evidence — L-33 names this exactly
**Cost:** would have shipped a change breaking supersession demotion.
**Root cause:** the roster of never-surfaced lessons was wrong (6, not 7), L-61
was cited as evidence for "short lessons don't surface" when it is the **5th
longest** of 25, and the headline probe was attributed to a gameplan whose phase
query is empty. L-33 — carried in memory the whole time — says a subagent's
`file:line` claims are leads to verify at the point of edit, not facts.
**Lesson:** recorded as C-03's lesson and as the corpus-level finding below.

### 2. The plan had empty task tables and no source-of-truth captures
**Cost:** an executing session would have received `_(describe)_` as its task
list. All substance lived in exit criteria, which is why they inflated to 6–13
per phase against a corpus norm of 4.
**Root cause:** treating `cz_set_exit_criteria` as the plan rather than as its
acceptance gate. The procedure calls Source-of-Truth Captures "the single
most-reused artifact across phases"; it was left as scaffold in a gameplan whose
entire premise was version and count truthfulness.
**Lesson:** the successor's captures block is 30 lines of measured values, and
every phase has real task rows.

### 3. Phase 2's kill criterion was rigged, and it cited the lesson it violated
**Cost:** would have "validated" D-061 by construction.
**Root cause:** the fixture author picks the entries, so under raw overlap any
long off-topic entry can be made to outscore any short on-topic one. Pass/fail
was set by authorship, not by the ranker. This is precisely L-50(b) — *"when you
author BOTH fixture and detector, a 100%-detection result is suspicious by
construction"* — which the plan cited in Phase 3 and failed to apply to Phase 2.

### 4. Every decision was scoped to a single agent's session
**Cost:** three findings inverted under a multi-agent frame. The zero-telemetry
corpus wipe looked like a corner case and is the *default* experience of the
second agent, the teammate, and every CI runner. D-062's demotion was measured
on a repo where `git shortlog` attributes 358 of 368 commits to one author whose
cascade always ran in the same commit as the edit — the exact condition that
makes cascade a no-op.
**Root cause:** the audit lenses were authored without a concurrency lens.
**Lesson:** D-064, and the sixth audit agent that produced the multi-agent
findings the first five structurally could not see.

## Procedure Improvements

1. **A version in `pyproject.toml` is a local fact, not a release.** Sweep the
   three remote legs before planning anything version-bearing. The local trio
   agrees by construction because one commit edits all three. Recorded as C-02.
2. **Put version targets in exit criteria, not phase names.** No blessed op
   renames a phase, so this gameplan's Phase 5 title still reads "ship 1.14.0"
   while its criteria say 1.13.0. `cz_set_exit_criteria` replaces; nothing
   renames.
3. **Re-read the rendered entry after any long structured write.** Two entries
   in this gameplan's own record carry literal tool-call markup accepted by a
   schema that only validates field presence. `ok: true` is not proof the
   content landed intact.
4. **Consolidating lessons can delete the clause that mattered** — see below.
   This is the most important improvement this gameplan produced and it belongs
   in the consolidation ritual, not in the ranker.

## The Finding That Outranks Everything Else Here

`L-39` carried the only recorded description of the hazard that would have
stopped D-061:

> *"BM25 length-normalization breaks the stale-vs-current SECONDARY-sort tie
> that supersession-demotion relies on … needs a length-adversarial fixture
> before it can be called safe."*

`L-50` absorbed L-39 during consolidation and **dropped that clause**. L-39 is
now marked obsolete, so the single most relevant warning for the change this
gameplan was about to ship survived only in an entry the corpus instructs
readers to ignore.

The coverage gate that governs consolidation (L-26) checks that the synthesis
still *retrieves* for the source's own tokens. Retrieval survived; the
load-bearing clause did not. **A retrieval-based coverage gate cannot detect the
loss of a falsifiable, mechanism-specific warning.** That is the first measured
cost of the consolidation ritual, and it is a finding about D-009/L-57 policy —
not about ranking.

## Open Threads

- Everything actionable moved to `2026-07-24-evidence-traversal-1-14-0`
  (7 phases, 78 exit criteria, O-01…O-07).
- **D-061's successor** is a separate 1.15.0 gameplan, ordered
  instrument-before-change per D-026: widen the benchmark fixture → adopt the
  provenance-tag external label → make the supersession guarantee
  score-independent *as its own decision* → make L-26's coverage gate
  executable → validate on a second real corpus.
- **`cz_amend_entry` / corpus repair** deferred to 1.14.1. Acceptance cases
  already exist: `DECISIONS.md:382`, `:467`, `HARDENING.md:245`.
- **The consolidation-coverage gap** above needs its own decision. Nothing in
  1.14.0 addresses it, and D-068 only removes the *drop* mechanism, not the
  consolidation one.
