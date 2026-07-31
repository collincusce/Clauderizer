---
id: subsys.telemetry
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.analyze
last_verified: 2026-07-25
---

# Telemetry

Append-only, deterministic telemetry of memory **surfacing** and phase **outcomes** — the empirical signal the engine never used to persist.

## The join that makes self-improvement possible

Two kinds of event, one compact JSON object per line in `.clauderizer/telemetry.jsonl`:

- **`record_surfaced(...)`** — which project lessons and invariants a handoff surfaced for a phase.
- **`record_outcome(...)`** — a phase outcome: terminal status plus exit-criteria checked/total.

Two further event kinds ride the same journal (D-075), counters rather than joins: **`record_gap(...)`** — a memory gap, written best-effort by the `cz_analyze` OP alone (never the analyze library the UserPromptSubmit hook calls — INVARIANT-06) when decisions+invariants both came back empty for a probe with content; TEXT-FREE by construction (surface, scope ids, date, a token *count* — never the probe), surfaced as `corpus_health`'s read-only `gap_events` count (zero renders nothing, the `refusal_events` precedent). And **`record_reinforced(...)`** — a lesson reinforcement (ids and counts only); the durable record is the tracked trailer on the lesson line itself, which is also where `lesson_health` reads strength from (so a fresh clone sees it — the D-063 trap telemetry-only state falls into), the event just marking the activity.

Separately, neither is interesting. **Joined over time**, they are the only way to ask whether surfacing a particular lesson correlated with a phase that passed — which is what per-lesson utility and the curator are built on. Before this existed, every proposer recomputed from a stateless disk read, so nothing in the system remembered whether any of its advice had ever helped.

## The reads

- **`read_events(path)`** — all events in append order, **tolerant of partial and garbled lines**. A half-written line from an interrupted process must cost that one line, not the file.
- **`parse_reconciliation(...)`** — per register, how many entries had their status genuinely *parsed* versus *defaulted*. A metric about the metric: a corpus whose statuses are mostly defaulted is one whose health numbers mean less than they appear to, and this makes that visible instead of letting a confident-looking number rest on guesses.
- **`corpus_health(...)`** — a deterministic snapshot over the project-lesson corpus plus telemetry: size, redundancy, token cost.
- **`lesson_health(...)`** — per-lesson empirical health, joined from telemetry.
- **`curate_proposals(...)`** — **propose** corpus-maintenance actions from that health. Proposals only; consolidation and obsoletion are judgment calls the agent makes through `cz_consolidate_lessons` / `cz_obsolete_lesson`.
- **`loop_step(...)`** — one iteration of a loop gameplan, read-only.

## Constitution

- **Append-only** (INVARIANT-03) — every write is a new line; prior lines are never touched.
- **Local-only** — gitignored. It is per-environment churn and never committed, which also means it carries no cross-developer expectations.
- **Deterministic** — no sampling, no clocks the caller cannot supply.
- **Never written from a hook** (INVARIANT-06). Only blessed, write-locked ops append.

## What the numbers can and cannot prove

Treat any claim built on this data as a falsifiable hypothesis with a pre-named metric, and measure before building (L-50). The failure mode is specific: a cleanly-separable corpus saturates at the ceiling, so a scoring change shows no lift — which proves *no regression*, never *no value*. When a target metric is already saturated, the honest move is to predict the zero and park the feature by analysis rather than build it and report the null as a finding.

## DAG position

Depends on `subsys.paths` (the journal location) and `subsys.analyze` (the canonical tokenizer, so its redundancy metric shares one definition of near-duplicate — INVARIANT-09). Written by `mutations` and `ops`; read by `ops` (`cz_corpus_health`, `cz_lesson_health`, `cz_curate`, `cz_loop_step`). The third blessed writer is the `cz_preflight` op, whose `record_stint` lines (`kind: "stint"`, stamped with the import-time `PROC_TAG`) are the budget ledger's raw material (D-072) — appended raw, deduped to distinct dates by `rituals/budgets.py` at read time. `subsys.dreams` is its experiential counterpart — what only the responding agent can observe, where this records what the engine can measure.
