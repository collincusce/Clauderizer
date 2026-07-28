# workflow critique repairs — engine identity, ranker length bias, cascade yield, saturated telemetry Gameplan

> Created: 2026-07-24
> Status: Planning
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

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

_(Gameplan-internal decisions D1, D2, … . Project-wide ADRs live in docs/DECISIONS.md.)_

## Open Items

**O-01.** _(phase 1)_ Pre-flight baseline writeback mechanism — decide with the code open in Phase 1. Three candidates: (a) clean_tree exempts a diff that touches ONLY the engine-authored baseline label line; (b) the measured baseline moves to engine-owned gitignored local state and the tracked line becomes a rendered view refreshed at phase close; (c) the writeback moves out of pre-flight entirely to phase completion, a moment that already dirties the tree. Constraint: whichever wins, running cz_preflight twice in a row must not fail the second run, and the digest must never show a fabricated "0".

**O-02.** _(phase 0)_ Should the shipped .mcp.json pin a version floor for `uvx --from clauderizer[mcp]`? Unpinned is what let uv serve 1.12.0 to a 1.13.0 repo. Pinning a floor (clauderizer[mcp]>=X) prevents the skew but couples the emitted config to the release cadence and may fight uv's cache; the D-060 decision is that the WARNING is the fix, not repointing. Decide in Phase 0 whether a floor is additionally warranted, and whether `clauderize init` should stamp the emitting engine's version as that floor. Constraint: whatever ships must stay portable across all 12 wired hosts (D-031 / L-48).

**O-03.** Short-lesson near-dup blindness (dream 09033b98b104): the promote trailer's ~7 ancestry/provenance tokens dilute the Jaccard union enough that a PERFECT-SUBSET probe against a ~5-token lesson scored 0.38 vs the 0.40 threshold — terse lessons are effectively immune to the near-dup/correction advisory while long ones are not. When this gameplan re-registers the threshold (its ranker length-bias phase), add a short-lesson fixture: ~5-token lesson + enriched trailer, asserting the advisory fires on a perfect subset (L-50 pre-registered fixture process; INVARIANT-09 single-sourcing)

## Phase Breakdown

### Phase 0: Engine identity — doctor certifies what it launched

**Goal**: _(one sentence.)_
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] `clauderize doctor` completes an initialize handshake against the Claude Code MCP registration and prints the served serverInfo name AND version, not just "launchable"
- [ ] A synthetic version skew (engine != served) produces a warning line naming the remediation command; a matched pair stays silent
- [ ] The handshake probe is the SAME implementation the kimi-desktop path uses — `grep -c 'def .*handshake\|serverInfo' src/` shows no second probe fork
- [ ] A fresh-process test (subprocess running the real CLI, per L-60) asserts the identity check executes on the CLI leg, not only in-process
- [ ] Running against this repo TODAY, doctor reports the real 1.13.0-vs-served skew instead of green
- [ ] O-02 resolved: a decision recorded on whether init stamps a version floor into the emitted .mcp.json, with the portability constraint (D-031/L-48) addressed either way
- [ ] Full suite green: 1007+ tests

### Phase 1: Pre-flight stops arming its own failure; the baseline stops lying

**Goal**: Make cz_preflight idempotent — running it twice in a row must not fail the second run — and make the digest's baseline honest when nothing has measured it yet.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] O-01 resolved: the chosen mechanism recorded as a gameplan-scope decision with the two rejected candidates and why
- [ ] `cz_preflight` run twice in a row on a clean tree passes BOTH times — the regression test that fails on today's code and passes after
- [ ] After a green pre-flight, `git status --porcelain` is empty (or the only diff is one the clean_tree check provably tolerates by design, not by accident)
- [ ] The status digest never renders a fabricated "Baseline: 0 tests" — an unmeasured baseline reads as unmeasured, and a measured one reads the real count
- [ ] Against this repo, the digest reports the real 1007 (or "not yet measured"), never 0
- [ ] Full suite green, no test count regression

### Phase 2: Adversarial ranking fixture — build the measuring stick before the fix

**Goal**: Build the fixture and naive strawman that can FALSIFY the length-bias claim, per L-50, before any scoring code moves — long-but-off-topic entries paired with short-but-on-topic ones, scored by the current raw-count ranker as the baseline to beat.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] An adversarial fixture exists pairing long-but-off-topic entries with short-but-on-topic ones, plus near-misses (a long entry that IS on topic; a short entry that only shares stopwords)
- [ ] The current raw-count scorer runs against it as the named naive strawman, with its failures recorded as the number to beat
- [ ] The strawman demonstrably FAILS the fixture — if it passes, the length-bias hypothesis is falsified and D-061 must be revised or withdrawn before Phase 3 (a discard is a valid outcome, L-50)
- [ ] The existing saturated benchmark (tests/benchmarks RANKER_ENTRIES) is run and its 1.0 ceiling recorded, with an explicit note that it can only prove no-regression (L-39)
- [ ] A live-corpus probe is captured as a Phase output: what cz_next_phase_context surfaces TODAY for the curation gameplan, and the character length of each surfaced lesson
- [ ] Fixture and strawman are committed and green before any change to analyze.rank_relevant

### Phase 3: Length-normalize the ranker and break the corpus ratchet

**Goal**: Land the length-normalized relevance score (D-061) behind the Phase-2 fixture, apply the same normalization to cz_analyze's suggested_edges payload, and re-measure what the live corpus actually surfaces.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] The length-normalized scorer BEATS the naive strawman on the Phase-2 near-misses, not merely on a no-check baseline (L-40)
- [ ] The saturated benchmark shows no regression (still at its 1.0 ceiling)
- [ ] tests/test_canonical_tokenizer.py stays green — exactly one `def _tokens` under src/, import identity and threshold parity intact (INVARIANT-09 unweakened)
- [ ] Live-corpus re-probe: cz_next_phase_context for the curation gameplan surfaces at least one curation-relevant lesson, with the before/after sets recorded as a Phase output
- [ ] Each of the 7 currently-never-surfaced lessons (L-11, L-24, L-52, L-56, L-57, L-61, L-62) is re-checked against a query it should match; any still unreachable is recorded as a finding, not left silent
- [ ] cz_analyze's suggested_edges no longer emits stopword-dominated shared_terms — payload size for a fixed query measured before and after, and the drop recorded
- [ ] Full suite green

### Phase 4: Cascade self-resolves and stops blocking; utility scoring is parked

**Goal**: Land the two design calls (D-062, D-063): git-provenance auto-resolution plus advisory cascade_hygiene plus a yield metric; and park the derived utility layer while keeping the telemetry log, removing the ratchet's second half.
**Depends on**: 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] cz_cascade auto-resolves a dependent modified in the same commit as the trigger, recording the git provenance as its verdict; a dependent NOT touched still requires the agent's ruling
- [ ] An unresolved cascade report no longer fails cz_preflight — it surfaces in the digest and in pre-flight output instead; regression test covers both the surfacing and the non-blocking
- [ ] A cascade yield metric ships in cz_corpus_health (reports, verdicts, verdicts-that-changed-something) and reports this project's historical 53 / 123 / 0
- [ ] cz_corpus_health states outcome-signal saturation honestly ("N/N complete, 0 failed — utility not computed") instead of publishing pass_rate 1.0 as a result
- [ ] Per-lesson utility/failure_risk is no longer computed or consumed by the curator, and never-surfaced alone no longer generates obsoletion pressure; .clauderizer/telemetry.jsonl still receives surfaced and outcome events unchanged
- [ ] GAMEPLAN-PROCEDURE.md CHECK 7, clauderizer-cascade and clauderizer-do-phase updated in BOTH src/clauderizer/skills/ and .claude/skills/, with a parity test asserting the two copies match (L-16/L-55)
- [ ] Every doc or tool docstring claiming empirically-gated promotion is corrected to match what now ships — claim only what is verified
- [ ] Full suite green

### Phase 5: Close-out, clean-environment verify, ship 1.14.0

**Goal**: Sweep the doc surfaces the changes invalidate, self-audit, verify from a clean environment, publish 1.14.0, and then PROVE the headline defect is gone by re-probing what uvx actually serves.
**Depends on**: 1, 4.

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | _(describe)_ | _(est)_ |

**Exit criteria**:
- [ ] TARGET IS 1.13.0, NOT 1.14.0 — the phase title still says 1.14.0 because no blessed op renames a phase; this criteria list is the authority. Source is already at 1.13.0 in all three local places; this gameplan FINISHES shipping it, it does not open a new minor
- [ ] H-19 addressed: the close-out gate sweeps all FOUR registries (source, remote tags, GitHub Releases, PyPI) — not the three local sources that agree by construction; an unreachable registry reports unverified, never a false green
- [ ] Version single-sourced across pyproject, the package __version__ and the top CHANGELOG entry — all three still 1.13.0, no bump
- [ ] cz_audit run; every mechanical finding resolved or explicitly accepted with a reason, and the judgment checklist affirmed
- [ ] Suite green on EVERY CI matrix leg BEFORE any tag exists — a green on one OS is a guess about the others (L-51 sweep 2)
- [ ] origin/main holds the staged release commit BEFORE any tag or GitHub Release exists (a UI release tags the REMOTE head)
- [ ] Verified from a CLEAN environment (fresh venv / cleared uv cache), not the working editable install (L-23)
- [ ] v1.13.0 tagged, GitHub Release cut, and 1.13.0 published to PyPI — closing the gap that has stood since commit 81a99f4 titled "ship 1.13.0"
- [ ] PROOF the headline defect is closed: `uvx --from clauderizer[mcp] clauderizer-mcp` handshake returns serverInfo version 1.13.0 with the full 67-tool surface, and cz_add_dream is callable in a fresh Claude Code session
- [ ] `clauderize doctor` green FOR THE RIGHT REASON — identity asserted, no skew — not green because the check is weak
- [ ] README's MCP tool listing and count match TOOL_NAMES (the L-62 pin test still holds)
- [ ] A write-time guard rejects tool-call markup in structured-write argument values (3 occurrences this session: D-062, H-19, and one call the schema caught) — no legitimate ADR/finding body contains a closing field tag
- [ ] POST-MORTEM.md written, covering the four repairs, H-19, the no-repair-path gap behind C-01, the absent phase-rename op, and whether D-060's handshake rule should be promoted to an invariant
