# Clear the Findings Backlog to Zero (1.14.2) — Post-Mortem

> Author: Claude Opus 5 session, 2026-07-25
> Shipped: **1.14.2 to PyPI**, tag `v1.14.2` @ `d9a018d` on `35b5268`
> Suite: 1164 → 1232 passed, 7 skipped. CI 10/10 on the released commit before any tag.
> Open findings at close: **0 of 27.**

## Why this existed

1.14.1 closed two findings and opened four, one of them high. That is the shape
D-069 exists to catch, arriving one level up: a register that *lists* open
findings but has no signal that they are aging reads an item carried across four
releases exactly like one opened an hour ago. The user's objection was the whole
brief — *"I really don't like having open items before a push"* — and the phase-5
criterion was written as the register's own count, not a claim.

| Finding | | The RED that proved it |
|---|---|---|
| `H-27` | high | old tree: no bundle key, no line — and `engine_source_newer_than` returns `False` on **both** trees, which is the blindness itself |
| `H-25` | med | identical on-topic corpus → no lesson keys, no plan-time telemetry |
| `H-26` | med | still fires at ~6168 tok after 26→20 entries, refusing to call that an improvement |
| `H-16` | low | old tree **wrote through** a symlinked parent; the file escaped the repo |
| `H-21` | low | `DEFERRED` parsed as `unknown`; all-deferred stuck in `planning` forever |
| `H-24` | low | two ratchets, each demonstrated firing |

## What went wrong, and it is the useful part

**I built the thing I had just criticized.** My first doc-seam draft printed
per-subsystem coverage and failed only when a doc mentioned *nothing* — so
`rituals` at 8-of-42 named passed cleanly. The user named it in five words:
*"that's exactly how you get rot."* They were right. An advisory that never fails
is the same write-only shape as the register this gameplan existed to empty. The
replacement is a strict **ratchet** — no invented target to argue about, existing
debt frozen visibly, growth becomes a decision someone writes down.

Fixing it exposed a second hole worth more than the first: the per-subsystem
ratchet watched **8 of ~40 modules**, and both modules written during 1.14.1/1.14.2
had landed in that blind spot. A check with a blind spot that large is the false
green again. Hence the second ratchet, over the watched set itself. *Check your
detector's coverage before trusting it.*

**Two release gates caught two real defects, and one of them was mine.** The
published-MCP probe was a **coin flip** — it piped its JSON-RPC messages and
closed stdin, so the server could exit on EOF before answering. Green on 1.14.1's
commit, red on 1.14.2's, green on a bare re-run, artifact healthy throughout. I
reproduced it locally *before* re-running, which is what separated "the artifact
is broken" from "the check is." Re-running first would have hidden a real
regression behind a green.

Then **three Windows cells red on a path assertion**: `"uv/archive-v0"` asserts a
*separator*, and Windows renders `uv\archive-v0`. That is L-51 sweep 2 verbatim,
down to the cell count — *"0.14.0 shipped with 3 Windows cells red on such an
assertion"* — and the lesson was in my surfaced set when I wrote the line. A
lesson being surfaced is not the same as it being applied, which is the humbling
counterpart to H-25.

## Did the register stay at zero?

The honest answer this gameplan was built to test. It did **not** stay at zero
during its own execution: the two gate defects above surfaced while closing, and
neither is recorded as a finding because both were *fixed in flight* rather than
filed. That is the distinction worth keeping — a register grows when discovery
outpaces repair, and shrinks when they move together. Zero is not a steady state
to defend; it is a signal that nothing found has been left unacted.

## Proof, not claims

```
CI            10/10 on 35b5268 pre-tag, verified at JOB granularity
              (9 matrix cells + fresh-clone; a workflow-level green hides a cell)
publish       in-band log evidence: both artifacts uploaded, attestations, View at
handshake     uvx --refresh → serverInfo clauderizer 1.14.2, 67 tools
              — probed with the CORRECTED shape this release shipped, not the
                fire-and-close pipe whose race was the gate defect it fixed
H-27 live     the published build flags itself: "NOT running this repo's source …
              (both report 1.14.2)" — the PATH catching what a version-only
              check would have certified healthy
```

## For next time

1. **A detector's coverage is itself a claim.** Ask what fraction of the surface
   it watches before believing a green.
2. **Diagnose a red gate before re-running it.** One local reproduction is the
   difference between finding a defect and hiding one.
3. **A surfaced lesson is not an applied lesson.** L-51 was in front of me and I
   wrote the separator assertion anyway. H-25 fixed *reachability*; nothing yet
   addresses application.
