# Skill-Awareness — Post-Mortem

> Author: Claude Code (Opus 4.8) session, 2026-06-22
> Scope: Full retrospective on phases 0–4, planned and executed 2026-06-22.
> Outcome: **1.0.0rc1 shipped to PyPI** — the first 1.0 release candidate.

## Executive Summary

Made projects **skill-aware** by mirroring the lesson architecture: skills are
line-entries in `docs/SKILLS.md` with a one-grammar state module, registered via
blessed writes, discovered read-only (propose-confirm), and surfaced *focused by
relevance* in the handoff + status gauge. The auto-PR idea was dropped at the
user's direction (D3) — discovery has no write path by construction. Shipped as
`1.0.0rc1` through the full release ritual: 9-cell CI matrix green, `release-check`
exit 0, tag, prerelease, Trusted-Publishing to PyPI, `uvx --refresh` verified.
Suite **573 → 601**; zero regressions (INVARIANT-07). One feature surprise (the
host-neutral tool-surface test) was caught by the suite and fixed before any push.

## What the Gameplan Got Right

### 1. Mirroring the lesson pipeline kept the new surface tiny
`register_skill` ≈ `promote_lesson`'s write half; `obsolete_skill` ≈
`obsolete_lesson`; discovery ≈ `cz_curate`'s propose-confirm shape; surfacing ≈
`relevant_lesson_pointer`. The only genuinely-new code was `skill_state.py` (~90
lines incl. the entry grammar) + a template + 3 thin ops. Reuse of
`analyze.rank_relevant`, `_insert_under_category`, `_ensure_doc`,
`next_numbered_id` meant almost no new mechanism to trust.

### 2. The existing suite caught the cross-cutting regression (L-34)
`cz_discover_skills`'s docstring leaked `.claude` into the host-neutral tool
surface; `test_tool_surface_is_host_neutral` (D-032) failed on the full-suite
run. Per-phase TDD alone would have missed it — the seam is owned by a test of
the WHOLE surface, exactly L-34's warning. Fixed by describing the locations
host-neutrally (the Claude-specific paths stay an impl default + the O-01 residual).

### 3. The propose-confirm constitution made "no auto-PR" structural
Discovery returns proposals read-only (`writes=False`); `register` is the only
write. "No auto-PR" isn't a policy to enforce — there is no code path that could.

## What the Gameplan Got Wrong / Friction

### 1. The wsl.exe-from-Git-Bash pipe swallows pytest's summary line
Every full-suite run lost the "N passed" line through the `wsl.exe` stdout pipe
(also broke `tail`/`grep` on it). Exit code + dot-counting from a *redirected
file read directly* was the reliable signal. Cost: several extra commands hunting
the count. **Lesson:** on this host, capture to a file and Read it; never trust
the piped tail's last line for a process's final line.

### 2. Curation parity didn't map; recorded as A-001 rather than forced
`promote`/`consolidate` are lesson-tier concepts; forcing them onto skills would
have added awkward surface to a 1.0 rc. Amendment A-001 records the honest scope
cut (L-38). The `superseded` state ships as a *tested forward-compat seam* — a
judgment call between dead-code and future-proofing, resolved by documenting the
seam (a future `cz_supersede_skill`).

### 3. README tool-surface had drifted (pre-existing, L-21)
The README listed 31 tools vs. the real 35 (the 0.17.0 loop ops were never
added). Fixed to 38 while adding the Skills group — the L-21 "reference docs
drift together" sweep, applied.

## Procedure Improvements

None structural — the procedure (v1.3.0) held. The discipline gates earned their
place: the **analyze gate** surfaced INVARIANT-07 (parity-never-regresses) at
decision-recording time, before a line of code; **exit criteria** drove each
phase's close honestly; the **amendment** gate captured the curation scope cut
without faking a checkbox.

## Open Threads

- **G6 cold-start restart-validate** (named residual): the rc must be observed
  delivering the `[Clauderizer]` digest in a REAL new session before final 1.0.0.
  The session that ships wiring cannot observe its own next cold start (L-11).
- **`docs/LESSONS.md` re-distill**: 23 active project lessons (> 20) — owed to the
  standing curator loop (`2026-06-21-standing-curator-loop-memory-maintenance`),
  unchanged by this gameplan.
- **`cz_supersede_skill`**: deferred; the grammar seam exists (A-001).
- **Final 1.0.0**: flip the classifier to `5 - Production/Stable` once the
  cold-start residual closes; promote 1.0.0 (non-pre-release) so `uvx` resolves it
  by default.
