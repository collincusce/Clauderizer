# Post-Mortem — integrity-patch (1.3.1)

> Closed: 2026-06-28 · Shipped: 1.3.1 (PyPI, GitHub Release v1.3.1, uvx --refresh verified)
> Baseline 711 → 716 passed / 5 skipped · tool surface 42 (unchanged)

## Summary

A read-only integrity audit at 1.3.0 produced six findings (one keystone + five
P2–P4) plus four open items. This gameplan fixed them as a **patch** — no new
features, no user-facing behavior regression, the tool surface held at 42 — and
shipped 1.3.1 via the D-011 release ritual on the user's explicit go (INVARIANT-07).

The keystone reframed itself under measurement. The audit predicted a divergent
"fork" tokenizer in `telemetry` was *hiding* near-duplicate lesson pairs that the
canonical `analyze._tokens` would surface. Phase-0 measurement falsified that:
**both** tokenizers report 0 redundant pairs at every threshold from 0.3 to 0.7
(the real corpus's max pairwise Jaccard is 0.19). The genuine defect was
**incoherence**, not under-counting — two different definitions of "near-duplicate
lesson" coexisted (the fork tokenizer at threshold 0.6 vs. the write-time advisory's
canonical tokenizer at 0.40). The fix was therefore to single-source *both* the
tokenizer and the threshold (D-041), not to lower a threshold to manufacture pairs.

## What worked

- **Fixture-first measurement (L-39/L-40 → L-46).** Phase 0 measured before
  changing anything and overrode the gameplan's own premise via amendment A-001.
  This is the gameplan's most valuable output: the fix matches the data, not the
  audit's prose.
- **Single-sourcing as the unifying move.** The keystone (tokenizer + threshold),
  the `L-NN` lesson-line grammar (#5), and the digest tool list (#3a) were all
  "two copies that can drift" problems; each collapsed to one source + a guard
  test. D-041 graduated to INVARIANT-09 once `test_canonical_tokenizer.py` made it
  machine-checked.
- **Behavioral test integrity (D1).** Replacing the tautological
  `writes is False`/`__name__` asserts with a snapshot-the-repo-and-run gate
  (`test_read_only_ops.py`) means "read-only" is now *proven*, not *claimed*. The
  count dropped honestly (716, not inflated) while every remaining test is
  load-bearing.
- **The loud-warn fix (#6a).** The false-green was a verdict problem, not a logic
  problem; warning + "PASS WITH WARNINGS" satisfied the constraint without a
  hard-fail, honoring INVARIANT-05.
- **Clean release.** release-check stayed green across the four-registry sweep;
  push → 9-cell CI → squash-merge → tag-on-full-SHA → Release → OIDC publish ran
  without an incident; PyPI + uvx verified.

## What didn't (root causes)

- **Missed the PHASE-1 handoff.** Completing Phase 0 then moving straight into
  Phase 1 work skipped `cz_write_handoff(phase_n=1)`; `handoff_presence` caught it
  at the Phase-5 preflight (root cause: the handoff for phase N is written when
  N-1 completes, and that step is easy to skip when one session runs consecutive
  phases). Backfilled before release. **Improvement:** when running phases
  back-to-back in one session, write the next phase's handoff as part of each
  phase's close, not just at the boundary between sessions.
- **Shell quoting traps during the release (L-29).** Two release commands lost a
  nested `$(...)`/`$VAR` to the outer Git-Bash shell before reaching WSL (the PR
  body heredoc; the `gh run list` run-id capture; the `--target` SHA echo printed
  empty). No harm done — the tag still landed on the correct commit (verified
  explicitly), the PR body went via `--body-file`, and the run id was fetched
  directly — but it cost retries. **Reinforces L-29:** inside
  `wsl.exe -d ubuntu bash -lc "..."`, avoid nested command substitution and shell
  variables; pass bodies via files and fetch ids in their own call.
- **The audit hypothesis was wrong (not a failure, a finding).** That the predicted
  cause was falsifiable and falsified is exactly why Phase 0 exists; captured as
  L-46.

## Procedure improvements

- L-46 added: an audit names a symptom + a *falsifiable* hypothesized cause;
  measure before fixing (extends L-39/L-40 to audit-remediation).
- INVARIANT-09 added: one canonical tokenizer + one near-duplicate threshold,
  machine-checked — a structural rule, not a convention.
- The behavioral read-only gate (`test_read_only_ops.py`) is the reusable pattern
  for any future "is this op read-only?" claim — prefer it over a registry-flag
  assertion.

## Open threads

- **Pre-existing PII (out of scope, flagged).** Three older tracked files still
  carry a hardcoded home-dir username — two append-only handoffs from prior
  gameplans and one `_experiments` script. Spun off as a separate task
  (`task_455387ca`); not hand-edited here (append-only discipline + scope).
- **Downstream unblock.** With the tokenizer unified and `cz_corpus_health` now on
  a trustworthy, single-sourced basis, the **2026-06-21-standing-curator-loop**
  gameplan can do the 30-lesson consolidation on a sound redundancy metric — its
  long-standing blocker is cleared.
- **Lesson-corpus bloat.** 30 → 31 active project lessons (L-46 added). The corpus
  is over the 20-lesson handoff-weight threshold; the curator-loop (now unblocked)
  is the right place to re-distill, not this patch.
