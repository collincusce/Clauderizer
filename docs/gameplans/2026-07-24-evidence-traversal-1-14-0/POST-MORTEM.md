# Evidence You Actually Traversed (1.14.0) — Post-Mortem

> Author: Claude Opus 5 session, 2026-07-24 → 2026-07-25
> Scope: all 7 phases, planned and executed in one continuous session
> Shipped: **1.14.0 to PyPI, 2026-07-25**, tag `v1.14.0` @ `891c682`
> Suite: 1002 → 1074 passed. CI 10/10 on the released commit before any tag existed.

## Executive Summary

1.14.0 shipped no new capability. It made existing defenses fire, and pinned each
to its source with a test demonstrated **red on the pre-fix tree** first.

The release began as a critique of the workflow and became a repair of one
phenomenon wearing nine costumes: **the engine asserted things from evidence it
never traversed.** A findings register reporting every entry `active` because its
parser matched nothing and the reader defaulted. A curator proposing deletion
because a *gitignored* file was absent. A `doctor` reporting "launchable" from
`shutil.which`. A release gate reporting "wiring verified" from a substring
match. Each defense had been built after a real incident, recorded, declared
resolved — and was live again.

**What actually shipped, measured:**

| | before | after |
|---|---|---|
| `cz_list_findings` | 21 entries, all `active`, all `date: null` | 17 resolved, 4 open, dates populated |
| Status parsers under `src/` | 3 disagreeing | 1, pinned |
| A failed write on `DECISIONS.md` | truncated 92,027 → 38,334 bytes | byte-identical |
| `cz_write_handoff` + planted symlink | wrote outside the repo, `ok: true` | refuses |
| Forged-heading injection | created `D-900`, burned 899 ids | impossible |
| `cz_curate` on a fresh clone | 25 of 25 obsoletion proposals | 0 |
| Lessons reaching a phase | 5 of 25 | 25 of 25 |
| `doctor` on the portable wiring | `shutil.which` | `serverInfo clauderizer 1.14.0` |
| BOM'd `.mcp.json` | co-resident servers deleted | preserved |

## What the Gameplan Got Right

### 1. Red-before-green was the load-bearing discipline
Every new test was demonstrated failing on a detached worktree at
`pre-1.14.0-writepath` before it went green. The most valuable red was
*substantive* rather than a missing symbol — `assert 'active' == 'open'`, the
finding round-trip genuinely failing because the reader could not read the
writer's render. Tests that error at a fixture (Phase 4's) are visibly weaker
evidence, and saying so at the time kept the record honest.

### 2. Reading the repo's own findings beat re-deriving them
Phase 4 resolved H-20 using **H-20's own recorded fix and its own three
regression tests**. The finding had been written by this repo, with the remedy
spelled out — and three independent planning drafts re-derived it from scratch
instead of reading it. Recognizing that and just executing the recorded fix was
the cheapest phase in the release.

### 3. Adversarial review before an irreversible step
An 11-agent pre-ship review returned SHIP WITH FIXES and six blockers. **Two
were regressions this release introduced** (below). The 1074-test suite caught
neither. The review found them by running the real CLI on realistic input.

### 4. Corrections instead of workarounds
Where the plan was wrong, it was recorded and the reasoning kept: C-01 (a
criterion demanded deleting a structural guard), C-02, C-03. Criterion 0.7 was
closed **not-applicable with evidence** rather than ticked. Three existing tests
were *retargeted to a decided contract* rather than weakened, and each rewrite
says which decision governs it.

## What the Gameplan Got Wrong

### 1. A "safety" fix that was a net regression (C-02)
**Cost:** `clauderize init` aborted the entire install on an ordinary commented
config. **Root cause:** Phase 5's preserve-and-refuse raised a bare `ValueError`
that propagated out of the host-sweep loop; because the emitter order puts `zed`
before the emitter that writes `.mcp.json`, the *primary* wiring was never
written. `.zed/settings.json` and `.vscode/mcp.json` are JSONC — a leading
comment is the **default**, not an adversary. A/B against the pre-fix tag: old
code completed the sweep and silently deleted the user's Zed theme; new code
preserved the file and installed nothing.
**Lesson:** ask what the *caller* does with a refusal before choosing a raise. In
a loop over independent items the correct shape is catch-warn-continue. And pick
fixtures from the ecosystem, not from convenience.

### 2. Widening a parser widened what it matches inside prose (C-03)
**Cost:** a decision quoting the register's own shape in a fenced block read as
`superseded (1999-01-01)` and reported `status_source: parsed` — worse than
defaulting, because it looks authoritative.
**Root cause:** Phase 2 closed exactly this class on the *write* side and the
mirror guard was never carried to the *read* side. The phase's own detector was
structurally blind: parse reconciliation counts **defaulted** values, never
values parsed from the **wrong line**.
**Lesson:** a write-side guard against forged structure implies a read-side
mirror. And "my own check is green" is not evidence when the check cannot
observe the failure mode.

### 3. The memory fell two phases behind the work (H-22)
**Cost:** phases 5 and 6 were implemented, tested and pushed across eight commits
while the tracker still read them not-started. It was corrected only because the
user announced a session switch. Had they closed the terminal, the next session
would have inherited a corpus describing work that no longer matched the repo,
and would not have known a release was staged.
**Root cause:** the ending protocol is prose in a skill. The engine has a
detector for every *other* discipline — unresolved cascades, unchecked criteria,
open items, redundancy, wiring drift — and none for the one that keeps memory
current. This is D-065 turned inward: the digest asserts phase state from the
tracker without reading the commits that contradict it.

### 4. Two nested clauderized repos, two contradictory digests (H-23)
`/home/ccusce` is itself a clauderized repo containing this one, so **two**
SessionStart digests fired and the first said *"No active gameplan"* about a repo
mid-release. This was the first thing in the executing session's context and was
read past for the entire release; a second session flagged it before it could
report state. INVARIANT-08's at-most-once guarantee is enforced by an in-memory
per-process signal, which nesting defeats structurally.

### 5. I specified a guard and did not build it
Phase 5 criterion 12 required "a write-time guard rejecting tool-call markup in
structured-write argument values." It was never implemented. **Four** malformed
writes now sit in append-only memory (`DECISIONS.md` ×2, `HARDENING.md` ×2), the
fourth landing while writing H-23 — inside the release whose thesis is that
written intent without an executable check rots.

### 6. Fixing the baseline on one machine broke it on all the others
Moving the measured baseline to a gitignored sidecar left the tracked line with
no writer, so a fresh clone, a teammate, or CI would read a stale number forever.
Traded "wrong on one machine after pre-flight" for "wrong everywhere else,
permanently" — worse in the multi-agent case D-064 exists to weigh. Fixed by
refreshing the tracked line at phase close, which `preflight.py`'s own comment
already promised.

## Procedure Improvements

1. **State criteria as the property required, not the edit imagined to produce
   it.** "Delete line N" encodes an assumption about why line N exists; "the host
   INVARIANT-07 protects is identity-checked" survives being wrong about the
   mechanism (C-01).
2. **A safety fix needs an A/B against the old behavior on realistic input.**
   Preventing destruction is not automatically an improvement if it prevents the
   operation (C-02).
3. **Every write-side structural guard implies a read-side mirror.** Ask in the
   same phase (C-03).
4. **A detector that counts one failure mode is not evidence about another.**
   Name what your check cannot see.
5. **The ending protocol needs an executable check, like every other
   discipline.** H-22 is the finding; the fix is a memory-lag signal derived from
   commits since the phase was last recorded.
6. **Read the repo's own findings before planning against them.** H-20 carried
   its fix and its tests; three drafts re-derived it anyway.
7. **Verify a publish from the job log, not the exit code.** The PyPI index lags
   a successful upload; a fresh negative is unproven, not failed.

## Open Threads → 1.14.1

- **H-22** memory-lag detection — highest value; loses a session's work.
- **H-23** nested clauderized repos violate INVARIANT-08.
- **The markup write-guard** specified in Phase 5 criterion 12, never built, with
  four live acceptance cases already in the corpus.
- **Task 5.2** — `model.from_file` still returns a bare `None`, so a BOM'd entity
  doc vanishes from the graph and `cz_cascade` on it returns `ok:true` with zero
  dependents. A live instance of this release's own thesis.
- **Task 4.6** — `init` spawn-tests the local console script, not the portable
  command it writes.
- **H-16** (symlinked parent directory) and **H-21** (a superseded gameplan
  cannot be closed) remain open with recorded rationale.
- **INVARIANT-10** was drafted and deliberately **not** ratified: an invariant is
  immutable and the repair op is deferred, so mis-worded text would be
  unfixable. Its rule shipped as D-065's machine-checked consequence instead.
