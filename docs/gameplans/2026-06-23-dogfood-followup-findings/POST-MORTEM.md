# Post-Mortem — dogfood-followup-findings

> Closed 2026-06-23. 8 phases (P0–P7) complete. Suite 602 → 617 green. Ships as 1.0.4.

## Outcome

Remediated the non-blocking follow-ups the 2026-06-23 stranger-readiness dogfood logged
(F1, F4–F13):

- **F4** — `clauderize ops --list` / `--schema <op>`, introspected from the shared ops/MCP
  registry; the dead "see tools_list" hint now points at `--list`.
- **F8** — **retired as a false finding** (C-02): `ops` already exits non-zero on `ok:false`;
  the dogfood's "exit 0" was the L-29 `$?`-in-outer-shell trap.
- **F9** — `cz_resolve_cascade` now states the exact close contract (verdicts + updates_applied)
  in its result and docstring; no more silent "pending".
- **F6** — a manual `cz_cascade` reuses a pending report for the same entity instead of
  duplicating (transition-agnostic match).
- **F5** — preflight emits an advisory when a `generic` profile leaves test/build empty in a
  now-detectable repo (read-only; never rewrites profile.lock).
- **F7** — MCP serverInfo reports clauderizer's version (set on the wrapped lowlevel server).
- **F10** — retire an entity via `cz_transition_status` → `retired`/`obsolete` (demoted, never
  deleted; INVARIANT-03).
- **F1** — a `clauderizer` console alias so `uvx clauderizer …` works.
- **F12** — amendment list args render readably; the amendment cascade line is a conditional
  prompt, not a false "pending"; the first-append placeholder strip was already correct (locked
  with a test).
- **F13** — the intentional-by-design behaviors documented for humans in P7.

## What worked

- **Verify-before-fix.** F8 was a phantom (a shell-quoting artifact in how the dogfood checked
  an exit code). Re-running it with `&&`/`||` instead of `$?` saved a needless `--strict` flag
  and produced a reusable lesson. Same discipline retired the premise of O-01.
- **Shared-source leverage.** F4 reused the one `REGISTRY` the MCP tools already use, so the CLI
  and agent surfaces can't drift — no second schema to maintain.
- **Fresh-human-reader audit (P7).** A read-only subagent reading the docs cold surfaced the
  real readability gaps (internal-ID jargon, an unverifiable alias claim, unexplained
  intentional behaviors) far better than self-review would have — the dogfood method applied to
  docs.

## What didn't (root causes)

- **The docs-philosophy misread.** The user's "docs must be human-usable" guidance was first
  recorded as a *dual-audience (agent + human)* decision (D-036) — wrong. It took two
  corrections (C-01, C-02) and three supersessions (D-036 → D-037 → D-038, then the layer
  distinction D-039) to land it. **Root cause:** treating a *corrective* instruction ("change
  how you write") as *additive* ("add a second audience"). A correction that sounds additive is
  the signal to re-read it as "stop doing X."
- **The two layers were latent all along.** The fix was naming the distinction (D-039): the
  **working-memory layer** (gameplans, handoffs, cz_* memory — agent-facing, dense is correct)
  vs the **product-doc layer** (README, procedure, CLI help — human-facing, plain prose). Prior
  gameplans likely blurred these too — hence the backlog initiative for a future session to
  audit and rectify.

## Procedure improvements

- Exit-code / CLI findings gathered via `…; echo $?` over the WSL shim are unreliable (the
  outer shell answers, not WSL bash) — re-verify with `(cmd) && echo OK || echo FAIL`.
- Docs are the product layer's responsibility on every engine change: refresh them in-phase and
  at close-out (D-038); keep internal IDs out of human prose (D-039).

## Open threads

- **Audit past gameplans** for dogfood-vs-engine-update / two-layer conflation, then rectify —
  carried as a backlog note for a future session (memory: audit-dogfood-vs-engine-conflation).
- **docs/LESSONS.md is 23 > 20** — a re-distill is owed; left to the standing curator loop
  rather than promoting this gameplan's two process-lessons (already captured by D-038/D-039 and
  L-29). Promotion deliberately skipped to avoid bloat.
- **1.0.4 ship** is the immediate next step; the fresh-reader's "docs say 1.0.4, binary says
  1.0.3" note resolves on publish.
