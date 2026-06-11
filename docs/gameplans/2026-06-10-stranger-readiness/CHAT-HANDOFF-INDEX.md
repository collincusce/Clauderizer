# Chat Handoff Index — stranger-readiness

> Last updated: 2026-06-10
> Status: All 5 phases complete

## How This Works

This is the coordination point for sessions executing this gameplan. A fresh
session gets current state automatically from the Clauderizer SessionStart hook,
then calls `cz_next_phase_context` for the active phase. No manual reading order.

## Pre-Flight Verification

Run `cz_preflight` before any code. If any enabled check fails: STOP, report.

**Current baseline test count**: 260

## Ending Protocol

1. `cz_transition_phase` the finished phase to complete.
2. `cz_add_output` each concrete produced value; `cz_add_phase_summary` the recap;
   `cz_add_correction` / `cz_add_lesson` as earned.
3. `cz_transition_status` on touched entities (fires cascade); `cz_resolve_cascade`
   the verdicts.
4. `cz_write_handoff` for the next phase.
5. Run exit verification; report the test count.

## Phase Status Table

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | The stranger's first hour: quickstart truth, live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Upgrade and uninstall stories, walked live | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Trust model on the record (TRUST.md + SECURITY.md) | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-2-HANDOFF.md |
| 3 | Troubleshooting runbook from the scar tissue | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-3-HANDOFF.md |
| 4 | README positioning pass + B5 consolidation | ✅ COMPLETE | 2026-06-10 | 2026-06-10 | handoffs/PHASE-4-HANDOFF.md |

**Status legend**: ⬜ NOT STARTED · 🟢 READY · 🟡 IN PROGRESS · ✅ COMPLETE · ⚠️ BLOCKED · 🔴 FAILED

## Per-Phase Completion Summaries

### Phase 0 — completed 2026-06-10

Walked the stranger's first hour in a fresh-HOME simulation (D1's local vehicle) and fixed everything it hit. The published quickstart command was broken outright — `uvx clauderize init` resolves no such package — and the walk found three defects deeper than the spelling: a bare `clauderize doctor` that doesn't exist on a uvx-only PATH; init under uvx wiring the ephemeral uv-cache path into .mcp.json and the hook wrapper, so `uv cache clean` killed the MCP wiring and replaced every digest with an engine-unreachable breadcrumb until re-init; and cold-cache uv progress noise riding the wrapper's stderr-rerouting (L-07) straight into session context, in front of the --version identity line the probes parse. Fixes: the README's four occurrences plus pyproject's comment now carry `uvx --from clauderizer clauderize init` (with a zero-install note covering every bare `clauderize` in the docs); `_under_uv_cache()` makes invocation resolution refuse cache-resident bindir AND which() results, wiring the durable absolutized `uvx -q --from clauderizer` form instead — proven live pre-release by running init via a locally built wheel: the wiring came out durable and the digest returned PURE after `uv cache clean`, self-healing by re-resolution. Suite 261 → 264 (three resolution tests).

The walk is now a permanent guard: .github/workflows/quickstart.yml runs the README's exact install path against the PUBLISHED package on a clean runner (push + weekly cron + dispatch), with a doc-drift grep tying CI to the documented command and a SELF-ARMING cache-clean assertion — it explains itself on 0.9.0 (which predates the fix) and hard-asserts from the next release. First quickstart run green (27316260960); the 9-cell matrix green on the same commit (27316260956, third consecutive all-green today). Known state recorded: published 0.9.0 still wires ephemerally; the fix ships with GP-C's flip release, and doctor catches the 0.9.0 failure shape as drift meanwhile.

### Phase 1 — completed 2026-06-10

Made leaving and upgrading as documented as arriving. docs/UPGRADING.md ships the upgrade contract (engine and wiring are separate; upgrading is always "update the engine, re-run init, doctor exit 0") with a decoder for doctor's three post-upgrade verdicts, the 0.9.0 ephemeral-wiring note for zero-install users, and a five-step uninstall that keeps docs/ — the project's memory, not the tool's. Every command is copy-paste runnable.

Both stories were walked live exactly as written: the pre-H-09 template and a moved engine each produced their precise doctor nudge (exit 3, message verified verbatim) and healed to exit 0 + byte-idempotency with one plain re-init; the uninstall's five steps left doctor honestly reporting "Not a clauderized repo" (exit 1) while a decoy MCP server, hand-written CLAUDE.md text, and the whole docs/ tree survived untouched — zero clauderizer residue in the executing surfaces.

### Phase 2 — completed 2026-06-10

Put the trust model on the record. docs/TRUST.md states, with a code citation for every behavioral claim (all twelve grep-verified), exactly what init writes (the complete six-surface table with per-surface preservation contracts), what executes and when (the hook wrapper's anchored-cd/stdout-only/always-exit-0 contract; the read-only engine hook; the repo-local stdio MCP server with reads-never-mutate and lock-serialized writes), the pre-write guards (spawn-test refusal, the ephemeral-cache refusal), the cloned-repo-with-preseeded-wiring scenario (nothing runs on clone; the harness's own trust flow is the execution gate; foreign paths fail as visible breadcrumbs, never silently), and the supply-chain posture (zero runtime dependencies, Trusted Publishing, the tag==source gate, the four-registry release sweep, the quickstart-vs-published-package CI job). The doc opens with the standing rule that a claim disagreeing with the code is a bug.

Root SECURITY.md follows GitHub convention: private vulnerability reporting, the scope pointer into TRUST.md, the pre-1.0 support statement, and the public append-only findings tracker. README links to both land in Phase 4's single copy pass.

### Phase 3 — completed 2026-06-10

Turned the project's scar tissue into a stranger-usable runbook. docs/TROUBLESHOOTING.md leads with the failure that matters most — no digest at session start — as a ladder: doctor first, then a decoder table mapping each breadcrumb prefix to the layer that failed and its cure, then the windows-wsl executor note, and finally the harness transcript's per-hook attachments as the durable diagnostic surface (the exact method that took H-08 from silent absence to byte-identical root cause). Around it: the doctor exit-code contract (with the designed-honesty note that ? is a verdict, not a failure), the mid-session MCP-absence reality (restart is the last mile; clauderize ops is the always-available write path), the unborn-branch skip, release-check's designed post-release red, and uvx cache staleness.

Discipline matched the trust doc: every quoted string was grep-verified against the source (9/9), so the runbook cannot drift from the code silently — and each entry names its evidence, a HARDENING finding or a live walk in a gameplan registry. README linkage is deferred to Phase 4's single copy pass.

### Phase 4 — completed 2026-06-10

Executed D3's single copy pass and consolidated B5. The README now leads with "Git-native working memory for coding agents", carries the adoption wedge (prose conventions rot because nothing executes them; personal-agent memory follows the person; project memory belongs in the repo as tool calls), states its maturity honestly with receipts (a section linking the public beta gates and what each already evidences), links the four stranger docs with absolute GitHub URLs so the PyPI rendering survives, completes doctor's exit-code contract in the CLI block, and — a G7 catch — its maintainers' release section now follows the ritual it used to contradict (push-first, release-check exit 0 before any tag). Verified on the final text: quickstart.yml green against the published package (run 27317115908) and the 9-cell matrix green (run 27317115901) on the same commit; suite 264.

B5's evidence row is filled, completing B1–B5 — only B6 (the flip) remains. GP-C's scope is recorded in the outputs registry, refined by what this gameplan learned: the flip release doubles as the release that ships the ephemeral-wiring fix and arms quickstart.yml's self-arming cache-clean assertion; the burn-down list (bare-IO meta-test, MCP-staleness nudge, TRUST.md release-time sync) and the carried G6 residual ride with it.

## Accumulated Lessons

_(Numbered sequentially across the whole gameplan. Categorized. Pruned of
obsolete items — mark with "(obsolete)" rather than deleting.)_

### Category: Process

_(none yet)_

**1.** Distribution claims need distribution execution: the author's repo never exercises the published install path (an editable venv is not `uvx --from PyPI`), so the front door was broken in four documented places — and the wiring it produced died on a cache clean — while every test passed. Walk the published artifact from a fresh environment, fix what it hits at the right layer, then pin the walk as a CI job that executes the doc's exact text (doc-drift grep included), with assertions that self-arm when unreleased fixes ship. (promoted 2026-06-10: L-13)
