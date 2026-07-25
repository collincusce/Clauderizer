# The Ending Protocol Needs a Detector (1.14.1) — Post-Mortem

> Author: Claude Opus 5 session, 2026-07-25
> Scope: phases 0–3 complete; phase 4 delivered its non-irreversible half
> Suite: 1074 → 1152 passed, 7 skipped (+78)
> Status: **1.14.1 is STAGED, NOT SHIPPED** — commit `a4784e3` on local `main`,
> unpushed, untagged, unpublished. Halted at the release boundary by decision
> (amendment A-001); resume sequence in the Outputs Registry under `RESUME_TO_SHIP`.
> Predecessor: [1.14.0 post-mortem](../2026-07-24-evidence-traversal-1-14-0/POST-MORTEM.md)

## Executive Summary

1.14.0's own execution produced the argument for this patch. Its post-mortem
listed three failures it did not have time to fix, and all three had the same
shape: **a discipline the system asks an agent to perform, with nothing that
notices when it has not been performed.** D-069 generalized that into a standing
test — *name the detector at design time, or say plainly that the practice is
unenforced* — and this release is that test applied to itself.

| | before | after |
|---|---|---|
| Tracker two phases behind eight commits | nothing emitted a signal | `⚠ Memory lag:` in the digest + a pre-flight `warn` |
| Session inside a nested clauderized repo | **2** contradictory digests | 1 |
| Nested installs visible anywhere | no | `doctor` names each by path (found **10** on this machine) |
| `cz_add_decision(context="…</context>")` | leaked verbatim into `DECISIONS.md` | neutralized, prose preserved |
| BOM'd entity doc | `from_file → None`, silently absent | `Drop(reason='bom-before-frontmatter')` |
| `cz_cascade` on a node not in the graph | `ok:true`, `0 dependents` | `ok:false`, names the drop |
| `init` and the portable wiring it writes | never probed | probed, advisory |

## The standing test, graded honestly

D-069 asks whether naming a detector at design time changed how this gameplan was
executed. **It did, and it is measurable — but not uniformly, and the exception
is the interesting part.**

**Where it worked.** Every phase here had its detector named in the exit criteria
*before* implementation, and in three cases that forced a better design than the
one I would have written:

- Phase 0's criterion 7 required running the detector against `eac1c9a`, this
  repo's own drift window. Writing that test first is what made me reject a
  "staleness score" and settle on a falsifiable predicate, because a score cannot
  be asserted against a historical commit.
- Phase 2's criteria named the four live corrupted entries as the acceptance
  corpus. Being forced to clean *real* bytes rather than synthetic ones is what
  killed the field-name blocklist I started with: `D-052`'s body contains prose
  that a blocklist would have eaten, and the unbalanced-closing-tag predicate fell
  out of trying to satisfy the real input.
- Phase 3's criterion named `cz_cascade`'s `ok:false` as the observable. Without
  it I would have "fixed" `from_file` and stopped, leaving the consumer that was
  actually lying — the one answering `0 dependents` — untouched.

**Where it did not.** The standing test says *name the detector*, and it is silent
on **who runs it**. Phase 1's fix is live and correct, and the install that
exhibits the pathology still does not have it: `/home/ccusce/.clauderizer/hook.sh`
runs `uvx --from clauderizer`, i.e. the *published* engine. A green on the
mechanism was recorded as "verified live" and is not the same claim as a green on
the deployment. I caught that only because the live check happened to print the
hook wrapper. It is recorded as output `DEPLOYMENT_GAP` and re-verified below —
but the honest reading is that **D-069 as written would have let it through**, and
the rule wants a second clause: *name the detector, and name the install that runs
it.*

**The other honest note.** The oracle "each new test is demonstrated RED on the
pre-1.14.1 tree" is satisfiable by an `ImportError`, which proves a module is
absent and says nothing about behavior. Phase 0 caught this and the remaining
phases used a standalone probe restricted to APIs present on both trees. That
became Lesson 2, and it is the single most reusable thing this gameplan produced.

## What the gameplan got right

**The RED probes were the real deliverable.** Four of them, each reproducing the
motivating failure in the old engine's own words:

```
efdf210  preflight PASS, no lag line          — with a src/ commit past a NOT STARTED phase
efdf210  digests reaching the session: 2      — one per nested install
efdf210  **Context**: …</context>             — byte-identical to docs/DECISIONS.md:381
efdf210  cz_cascade → ok=True, 0 dependents   — for a node that was never in the graph
```

Each is a *behavioral* red. None of them is an import error.

**Scoping silence, not maximizing it.** Phase 1's ownership rule fires only when
the session's owner is a *proper descendant* of the install's root. The broader
rule — "stay silent for any session that isn't mine" — is more satisfying and
would have quietly broken anyone who wired a global hook deliberately, which
INVARIANT-07 makes a release blocker. The same instinct shaped Phase 0's
`in_progress` exemption and Phase 3's conservative drop classification: in all
three, the narrower claim is the one that survives contact with a real corpus.

**Structural predicates over blocklists.** Phase 2's guard and Phase 3's drop
classifier both replace "a list of the bad values" with a property — *unbalanced*
closing tag, *intended to be an entity* — that needs no maintenance as the tool
surface grows and provably cannot touch well-formed content.

**Dogfooding produced evidence, not decoration.** The memory-lag detector caught
its own author: with Phase 0 committed and the tracker still reading READY,
`clauderize status` named phase 0 and the commit count. That in-band proof
(L-07's rule) is the only evidence that the whole chain fires in a real session
rather than a fixture.

## What the gameplan got wrong

**1. It assumed one nested install.** The plan described `/home/ccusce` containing
`/home/ccusce/Clauderizer`. The live scan found **ten** clauderized repos under
that home directory, and the root cause is sharper than H-23 stated: in `$HOME`,
`.claude/settings.json` *is* the per-user settings file, so clauderizing a home
directory makes that install's hook global to every session on the machine. The
fix is unaffected (ownership scales to N), but the plan's framing would have had
me test the two-repo case and stop. Now documented in the README.

**2. "Verified live" was ambiguous and I used the weaker reading.** See above.

**3. The D-066 boundary shipped in 1.14.0 undocumented.** Phase 2 went to write a
paragraph about the new guard and found there was no section to add it to:
`docs/subsystems/mutations.md` never mentioned `_safe_body`, the forged-heading
fix, or the normalize-never-reject contract at all. This is L-62's class — a doc
enumerating a code-owned surface, drifting silently — and it was found by accident
rather than by a check. Closed here, but nothing would have caught it.

**4. Phase dependencies were narrative, not technical.** Phases 0–3 are fully
independent; the plan declared 1 → 0, 2 → 1, 3 → 0. Nothing was harmed because
one session executed all of them in order, but a second agent could not have
parallelized them, and L-11 says exactly this.

## Numbers

```
suite            1074 → 1152 passed, 7 skipped   (+78: 11 + 16 + 26 + 25)
findings closed  H-22, H-23      (open findings 4 → 2: H-16, H-21, both deferred with rationale)
entities         subsys.rituals 0.11→0.12, subsys.scaffold 0.15→0.16,
                 subsys.mutations 0.7→0.8, subsys.graph 0.3→0.4, feat.init-cli 0.4→0.5
cascades         4 reports, 28 dependent verdicts, all resolved
new modules      rituals/memory_lag.py, nesting.py
lessons          6 gameplan lessons (3 Process, 2 Testing, 1 Process)
registries       v1.14.1 unclaimed on all four before any tag existed
```

## Recommendations for the next gameplan

1. **Amend D-069 to name the install, not just the detector.** A repair that lives
   only in source has not reached anything that runs a published engine.
2. **The corpus is over its lesson threshold** (25 project lessons > 20) and has
   been for several releases. `docs/LESSONS.md` rides in every handoff across all
   gameplans; the digest has been asking for a re-distill for long enough that the
   warning has become furniture.
3. **The four corrupted entries are still corrupted.** The guard stops new ones;
   the amendment op that would repair the existing four remains deferred, and they
   are now load-bearing as `test_toolcall_write_guard.py`'s acceptance corpus —
   which means repairing them later requires updating that test deliberately, not
   quietly.
