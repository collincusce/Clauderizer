# Post-mortem — pay down the frozen debt

> Gameplan: `2026-07-25-pay-down-the-frozen-debt-separator-claims-exempted-modules-and-surfaced-not-applied`
> Closed: 2026-07-26 · 3/3 phases complete · shipped 1.14.3 (and 1.14.4 staged)
> Suite 1232 → 1330 · open findings 0

## What this was for

1.14.2 froze two debts **visibly** rather than laundering them into a passing
check: 32 modules with no subsystem doc, and a class of separator-shaped
assertions that L-51 had described for three releases. Freezing was the right
call then. It is not a resting place, and a frozen debt with no schedule is just
a debt with better manners.

Underneath sat a sharper question, and it is the one the gameplan was really
named for: **L-51 was surfaced — ranked into the handoff of the very session that
then violated it — and was still not applied.** Does putting a machine check at
the point of the mistake change that?

## What worked

**Swapping the instrument before trusting the count.** The phase was scoped at 24
sites from a grep; an AST scan found 40. Recording that as C-01 rather than
quietly proceeding mattered because the count is *load-bearing* — the ratchet gets
pinned to it, so a scoping count from the wrong instrument bakes the blind spot
into the guard. Pinning at 24 would have left 16 sites permanently outside the
check while the phase read as complete.

**Building for the failure rather than the criterion.** Exit criterion 5 named one
line (`"uv/archive-v0" in serving_path`). Git history showed the fix commit had to
change *two*, and the second (`... in digest`) announces nothing about being a
path. Rule B exists only because of that: a detector satisfying the criterion
exactly would have missed half the real regression.

**Paying the exemption list to zero instead of shrinking it.** The gain is
discontinuous. At 32 exemptions the ratchet says "the debt cannot grow"; at zero
the same test says "a new module with no doc fails immediately." That is a
different guarantee, and it was affordable only because the design rationale
already lived in module docstrings — the work was distillation, not invention,
which is why all 32 docs reached 0 undocumented callables.

**Behavioral oracles against real artifacts.** Both guards were demonstrated red
using only APIs present on both trees: the separator detector against the actual
pre-fix blob at `f9f8343^` (2/2 flagged), the doc ratchet against the pre-1.14.3
doc set fetched with `git ls-tree` (32 escaped, 29 baseline keys with no doc).
No `ImportError` stood in for evidence.

**Arming every guard.** Each ratchet was tested against an injected violation and
watched go red, then green on removal. A ratchet at zero that was never tested
against a violation is just a list that happens to be empty.

**Saying "vacuous" out loud.** Zero of the 40 sites turned out to be platform
claims — `f9f8343` had already fixed the only real instance. Criterion 3 was
therefore satisfied by doing nothing, and reporting that plainly was more useful
than manufacturing repair work to make the checkbox feel earned.

**The release ritual catching its own operator.** `release-check` went RED on an
unpushed tree and forced the ordering invariant to hold by construction rather
than by memory.

## What didn't, with root causes

**The gameplan's own scoping count was wrong (C-01).** *Root cause:* the class is
defined syntactically and was counted lexically. Grep cannot see single-quoted
literals, a second literal on one line, the arms of an `or` chain, or `not in`
forms. *Generalized as L-68 step 2.*

**An exit criterion was satisfied vacuously.** Criterion 3 — "every site
classified as a platform claim is fixed" — had nothing to fix. *Root cause:* the
phase was planned without first checking whether the previous release's fix had
already emptied the class. A criterion that turns out vacuous is a planning
smell, not a win; the cheap prevention is to run the detection *before* writing
the criterion that depends on its result.

**Criterion 5 was met by hand, with nothing enforcing it.** CI was verified at job
granularity on the exact release commit — 10/10 jobs, 0 skipped — but only
because the criterion said to. `release-check` gated four registries and push
ordering and never asked whether CI passed, and GitHub reports a workflow as
`success` when a matrix cell is *skipped*. *Root cause:* the ritual was built when
the observed failure was the registries; the observed failure had since moved to
the matrix. Recorded as **H-28** with a dated acceptance, then fixed in 1.14.4
(job-granularity CI gate, 16 tests, behavioral oracle).

**A doc went stale inside the gameplan that wrote it.** `docs/subsystems/release-check.md`
was authored in Phase 1 saying the check "cannot check the thing that has bitten
hardest: CI green on every matrix cell" — and was false within hours of H-28
landing. `docs/ARCHITECTURE.md` opened "Eight tracked subsystems" while this
gameplan took the directory to 40. *Root cause:* both enumerate a code-owned
surface with no executable pin — L-65 exactly, committed by the gameplan that
was applying L-65 elsewhere. Fixed with `tests/test_architecture_pins.py`
(count + every-doc-linked + no-dead-links, all three arm-tested).

## Procedure improvements

1. **Count a class with the instrument that will enforce it.** If the guard will
   be an AST walker, scope it with an AST walker. Never a grep count feeding a
   ratchet.
2. **Run detection before writing criteria that depend on its result.** It costs
   minutes and prevents a vacuous criterion — or reveals, as here, that the work
   is triage plus a guard rather than a set of repairs.
3. **Sweep your own gameplan's docs at close.** The phase that writes a doc is
   often not the phase that invalidates it. Two of this gameplan's own documents
   were stale before it ended.
4. **Any count-bearing prose gets a pin.** "Eight tracked subsystems", "N tools",
   "seven checks" — every one of these has rotted here at least once. Append-only
   history (CHANGELOG, handoffs, cascade reports) is exempt on purpose: it records
   the old count deliberately.
5. **When a guard is added, name the sibling clauses it does *not* cover.**
   Enforcing one clause of a multi-part lesson reads as enforcing the lesson.

## The motivating question, answered

**Did the machine check change what surfacing could not?**

The diagnosis is solid, and the telemetry is blunt about it: **L-51 was the
most-surfaced lesson in the corpus — 42 surfacings, utility 1.0 — and is the one
that failed.** Surfacing count is not adherence, and no amount of re-ranking or
firmer wording addresses the actual gap, which is *temporal*: surfacing lands at
session start, the mistake happens at line 64 of a test file, and the lesson must
survive the distance between. A check at the point of the mistake collapses that
distance and puts the remedy in the failure message.

**But what has been proven is capability, not effect.** The check fired on a
reconstruction of the real regression and on a deliberately injected probe. It
has not yet fired on a mistake someone was actually making. Until it does,
"adding the check changed behaviour" is a hypothesis — and asserting more would
be the same false green the check exists to refuse. The honest claim: the
*mechanism* is verified, the *outcome* is untested, and the next path assertion
written under time pressure is the real experiment.

**What remains unenforced**, stated rather than implied:

- **The undecidable remainder.** A detector keyed on evidence the source supplies
  cannot classify a value that supplies none (`assert "a/b" in opaque_string`).
  The inventory ratchet is the backstop: it cannot triage such a site, but it
  refuses to let one appear *unclassified*. That converts silence into forced
  judgment, which is the most a static check can honestly offer.
- **L-51's third sweep.** The `.git/info/exclude` remedy for untracked files
  blocking `clean_tree` is still prose.
- **Whether a subsystem doc is *accurate*.** Both doc ratchets check that public
  callables are *named* and subsystems are *linked*. No mechanical check
  distinguishes "this doc discusses the right ideas" from "this doc is stale" —
  which is precisely how `release-check.md` was correct on Monday and wrong on
  Tuesday.

## Open threads

- **The lesson corpus needs a re-distill.** 21 project lessons, ~6168 tokens in
  every handoff, over the 5000 threshold. Two things make this harder than it
  looks, and both are measured rather than assumed: **utility cannot drive it** —
  every scored lesson sits at 1.0, the saturated ceiling L-50 warns about, so the
  metric has no discriminating power; and **"never surfaced" is not evidence of
  low value** — H-25 found exactly that misreading, where L-11's zero reflected
  where the ranker was wired, not what the lesson was worth. Consolidation alone
  will not shrink the token cost either, since a synthesis outranks its own
  sources and gets rendered in full. This belongs to
  `2026-06-21-standing-curator-loop-memory-maintenance`, not to an ad-hoc pass.
- **1.14.4 is staged and unreleased** on `origin/main` (`fad0cbb`): version
  single-sourced, CHANGELOG written, CI green at job granularity. Not tagged.
- **Six dream notes await distillation** (`cz_dream`).
- **H-28's fix has the same unproven-effect status** as the separator check: armed
  and tested, never yet fired on a real mistake.
