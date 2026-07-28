# Post-Mortem — clauderizer 2.0 alpha: fourteen vetted mechanisms

> Gameplan: 2026-07-26-clauderizer-2-0-alpha-ten-fractal-vetted-mechanisms
> Closed: 2026-07-28. Nine phases (0–8), all complete. Two publishes.

## What shipped

**v2.0.0a1** (PEP 440 pre-release, `--pre` only): fourteen externally-vetted
mechanisms — ten Fractal-lineage (D-070), four jcode-lineage (D-075) — built
advisory-first under binding conditions, then graduated or deliberately kept
dormant by the D-064 evidence matrix. Verdicts with figures: D-077 (seven
Fractal graduate; stamp env-armed dormant on the DrvFs +86%/op figure; budgets
dormant on 0.0 measured recording coverage), D-078 (gap detection, reinforce
verb, negative-space graduate; jcode-host an honest named gap), D-079
(fleet-vs-solo BOUNDED: quality tie under independent adversarial
verification, 1.57× wall-clock at ~1.7× compute, zero collisions). Fleet
pattern productized (shipped skill + GLOSSARY + ENFORCEMENT at every init
size). Hardening shipped inside the alpha: sanitizer removal echo (H-29),
stamp monotonicity (H-30), the mcp&lt;2 pin (H-31), nine platform capability
gates, a Windows-proofed parity harness.

**v1.14.5** (unplanned, same day): mcp 2.0.0 released upstream mid-gate and
broke every fresh `clauderizer[mcp]` install worldwide. The hotfix — the
staged-but-never-published 1.14.4 content plus the pin — went out from a new
`release/1.14.x` line with 10/10 matrix evidence on the exact sha, and was
verified healed by cold resolve. Suite: 1330 → 1561 passing across the
gameplan; matrix instruments committed (`matrix-p5-harness.py`,
`matrix-p5-results.json`, 12 legs).

## What worked

- **The vet → build-under-conditions → measure pipeline held end to end.**
  Refuters argued from recorded law; binding conditions — not verdicts — were
  the deliverable; every mechanism's signal was pre-named at adoption; two
  mechanisms stayed dormant because the figures said so, and the discards/nulls
  were recorded as successful outcomes (L-50). Nothing shipped on vibes.
- **The guards caught real events, live, repeatedly.** Doctor's
  capability-based MCP identity probe and the H-28 job-granularity CI gate
  caught the worldwide mcp break within hours of the upstream release. The
  version-single-sourcing test fired on a genuine stale-metadata mistake
  mid-ship. The separator-claims and doc-seam ratchets shaped the H-29/H-30
  hardening commit before it could land loose. The merge audit's first
  production observation was a true negative on a real fleet merge. This is
  L-68's "capability vs effect" bar being cleared: checks fired on mistakes
  actually being made.
- **The fleet pattern paid for itself with production work.** The P7 dogfood
  assigned real phases (P8 + the curator loop) to real workers: 0 collisions,
  0 LockHeld across 27 concurrent hub writes, honest closes verified against
  engine state — and the incidental load surfaced the serving-engine
  split-brain (H-30) that a toy dogfood would never have touched.
- **The release ritual absorbed a same-day emergency branch release** with
  zero recorded deviations: release-check tracked the release branch for push
  ordering, counted CI at job granularity on the exact sha, and swept all four
  registries for both versions.
- **Session-scale memory worked as designed**: the handoff notes stopped
  phase 5 from running before its dependencies; the reinforce verb's first
  production use recorded a mistake-class the session itself re-derived;
  dream notes captured what only the working agent saw.

## What didn't — with root causes

- **The split-brain serving engine restamped a version backward (H-30).**
  Root cause: nothing certified which engine build served a stamping op, and
  the stamp had no monotonicity guard. The monotonicity half shipped in the
  alpha; the certification half is live evidence for the workflow-critique
  gameplan's engine-identity phase.
- **Eight phases of code met the CI matrix for the first time on ship day.**
  P1–P8 were built across two days without a single push — so Windows/macOS
  latent defects (nine POSIX/`/proc` test assumptions, one truly-Windows-blind
  normalizer bug in the parity harness) all landed at once, at the worst
  moment. Root cause: push cadence was decoupled from phase cadence.
- **The platform-debt scoping was done wrong the first time.** I gated the
  four tests visible in a truncated CI log excerpt instead of auditing every
  `_freed_pid` consumer in the file — L-68 step 2 (scope with the instrument
  that enforces) violated in the very gameplan that promoted it; it cost one
  extra red CI cycle. The second pass audited the file.
- **One commit landed while the suite was red** — a `&&`-chained
  suite-then-commit where the echo swallowed the exit code. The tree content
  was correct and re-verified, but the ordering inverted verify-then-claim.
- **The CI-evidence PR detour**: a PR that conflicts with its base gets no
  merge ref and silently runs no `pull_request` workflows, and retargeting the
  base emits an `edited` event that triggers nothing. Cost ~20 minutes to
  diagnose; the close/reopen cycle is the reliable kick.
- **The audit's version parser reads `2.0.0a1` as `2.0.0`** — a false
  "version drift" finding at close. Small, but the auditor should speak
  PEP 440.

## Procedure improvements (candidates for the next planning pass)

1. **Push at every phase close** — make CI contact continuous, not a ship-day
   event. Cheap candidate: an advisory preflight/status line when origin/main
   is N commits behind local at a phase boundary.
2. **Upper-bound policy for SDK dependencies** (`mcp>=1.2,<2` class): any dep
   whose majors are breaking-by-convention gets a ceiling and a recorded
   lift-the-pin task, instead of an open range that lets an upstream release
   break the world on its schedule.
3. **`init` pins the portable MCP command when the engine is a pre-release**
   (the documented alpha caveat: portable wiring serves stable until pinned).
4. **The fleet-worker briefing template gains the branch-point verification**
   (archived lesson #4: check the worktree's merge-base against the briefed
   baseline before building).
5. **Teach the audit's version check PEP 440** pre-release suffixes.
6. **Scope enforcement work by auditing the source, never a log excerpt** —
   already law (L-68 step 2); it needed re-learning once here, which is the
   argument for its enforcement, not just its prose.

## Open threads

- **H-31 (open)**: adapt to the mcp 2.x SDK, then lift the pin with tests
  against both majors. Unowned; natural neighbor of the engine-identity work.
- **Workflow-critique gameplan, phase 0 (engine identity)**: now holds two
  live casualties as prior evidence (H-30's backward stamp; the session-long
  serving-vs-tree split this gameplan worked inside).
- **Post-publish re-measures armed**: gap-conversion rate, reinforce
  re-derivation rate, recording coverage (the budgets re-vote gate), and the
  stamp's default re-vote if a cheaper read path lands. All null-with-cause
  today; real telemetry starts with real 2.0.0a1 usage.
- **D-079's follow-on hypotheses**: fleet quality vs solo on tasks hard
  enough not to saturate at zero defects; behavior at N large enough to
  contend the write lock.
- **jcode-host row**: open with a verification-session recipe (P8 outputs).
- **7 staged dream proposals** awaiting triage (a separate session's ritual),
  plus the curator's standing observation that residual project-lesson weight
  is structural and needs an engine lever, not more curation.
