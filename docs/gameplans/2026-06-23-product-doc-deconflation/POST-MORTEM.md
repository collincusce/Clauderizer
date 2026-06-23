# Post-Mortem — 2026-06-23-product-doc-deconflation

> Closed 2026-06-23. 7 phases (0–6), all complete. Deliverable commit e375f09 (docs scrub),
> gameplan record 0319fdc + completion 21a5d2f; scaffold 719f278. Suite green at 617 throughout.

## Goal & outcome

Audit the 23 existing gameplans for where **dogfooding** (using Clauderizer to manage work) got
conflated with **engine updates** (changing Clauderizer's code + its human product docs), and
rectify the layer-2 human product docs that drifted or carried agent shorthand — per D-039 (two
doc layers, working-memory vs product). Verify with a fresh-human cold read.

Done. 19 internal-ID cross-refs rewritten to plain prose across docs/TRUST.md (6),
docs/TROUBLESHOOTING.md (4), docs/gameplans/GAMEPLAN-PROCEDURE.md (9), and the cz_* tool-description
docstrings in src/clauderizer/ops.py (13). README/SECURITY/UPGRADING were already clean + accurate.
A cold fresh-human reader (no source access) and an independent regex sweep both confirmed zero
unexplained internal IDs in visible prose.

## What worked

- **Make "jargon" mechanical before editing (D1).** Recon disagreed on whether INVARIANT-NN counts.
  A written regex + allow-list rule (banned ID patterns / allowed product vocab / affordance
  exemptions) turned a taste debate into a reproducible sweep. The cold reader later validated the
  kept IDs (the GAMEPLAN-PROCEDURE Numbering-Conventions definitions) as exactly correct.
- **Scope boundary as a guardrail (D2).** Meta-dogfooding invited two symmetric failures —
  over-reach (scrubbing the layer-1 shorthand that is SUPPOSED to stay) and under-reach (skipping
  the in-code tool descriptions). D2 named both edges; no layer-1 artifact was touched, and the
  tool descriptions got done.
- **Two independent verifications agreed.** A human-style cold read and a mechanical sweep both
  returned clean — convergence is stronger evidence than either alone.

## What surprised / didn't go to plan

- **The first drift we caught was in our own plan.** Phase 0 preflight measured 617 tests, not the
  602 the SessionStart digest advertised; carrying 602 would have made Phase 4's "tests green at
  baseline" gate check a phantom number (correction C-01).
- **Recon was full of confident false alarms — all caught by verifying at the point of edit
  (L-33).** README "≈40 tools" (it's 38, correct); H-08/H-09 "in UPGRADING" (they were in
  TROUBLESHOOTING); the survey subagent's "missing tools / unreferenced CROSS-HOST" doc-debt (all
  present). Trusting recon would have "fixed" non-problems and bloated the docs.
- **The conflation's residue was STYLE, not gaps.** Engine work that added tools DID keep the
  README accurate; what leaked was layer-1 shorthand written into layer-2 prose during
  gameplan-driven doc edits. The fix was a scrub, not a rewrite.
- **A stale claim that would have become a lie.** TROUBLESHOOTING's "H-01..H-09 all resolved" was
  stale (HARDENING goes to H-15) — but naively bumping it to "all resolved" would have been FALSE
  (open findings exist). Rewrote it to assert the tracker's discipline, not a drifting snapshot.

## Open threads (deferred, tracked as open items)

- **O-01** — README MCP-surface list not single-sourced from tools_list.py (a drift HAZARD;
  accurate today). Fix = a parity test or a generated section. Engine task.
- **O-03** — CLI RUNTIME-output messages leak IDs (`release-check` prints "(L-08)"); a surface
  distinct from the scoped `--help`. Needs a sweep of release_check.py / doctor output paths.
- **O-04** — concept-onboarding gaps (SECURITY/TRUST assume MCP/hooks/key-merge are known); a
  different quality axis from ID-jargon.
- **Lesson corpus over threshold** (23 project lessons > 20) — standing re-distillation pressure;
  not addressed here. This close-out added only one gameplan-scoped lesson (#1), no net-new project
  lesson.

## Procedure note

CHANGELOG was intentionally deferred to the imminent release gameplan — the doc scrub is unreleased,
so its CHANGELOG line belongs to the next version entry, not a duplicate edit here. For this
gameplan the project-doc update WAS the rectification itself.
