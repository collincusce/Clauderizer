---
id: subsys.proposals
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-25
---

# Proposals

Persistent triage for advisory proposals (D-052) — the state layer that `modernize` deliberately does not have.

## The gap it fills

`modernize.report()` re-derives its advisory proposals on every run and never writes anything (D-042). That statelessness is correct — it keeps the memory tier purely advisory — but it has a consequence: a proposal can be neither dismissed nor tracked. It reappears every session until the underlying condition changes, and once a corpus is version-current the digest stops surfacing proposals at all, so there is nowhere to look for what was declined.

This module adds the missing state **without breaking the two-tier contract**.

## Stable ids from content

Each proposal carries a **content-derived** id: `<kind>:<12-hex>`, from `proposal_id(kind, *parts)`. The derivation is the mechanism, not an implementation detail — a *materially changed* proposal (a newly declared gate, a different target) hashes to a new id and re-surfaces, while an unchanged one stays suppressed.

A sequential id would not do this: dismissing proposal #3 would suppress whatever #3 became. Content-addressing means "I have considered this" attaches to the actual thing considered.

## A per-user ledger

`.clauderizer/proposals.local.toml` — gitignored, per-user, never committed. Two verdicts:

- **dismissed** — hide until it materially changes.
- **deferred** — snoozed to a date, after which it returns.

There is deliberately **no third verdict for "handled"**. Doing the work resolves the underlying condition, so the detector stops emitting the proposal on its own. Recording a handled state would create a second source of truth that could disagree with reality — the ledger would claim something was done that a later regression undid.

Gitignoring is a D-067 consequence: per-machine state is local, team memory is tracked. One developer's decision to snooze a proposal is not a project decision.

## The surface

- **`ledger_path(paths)`** — the location.
- **`proposal_id(kind, *parts)`** — the stable id.
- **`load_ledger(path)`** — `{"dismissed": {id: date}, "deferred": {id: until-date}}`. A missing or malformed ledger reads as empty rather than raising: a corrupt local file must not break the digest.
- **`dismiss(...)`** / **`defer(...)`** — record a verdict.
- **`is_suppressed(pid, ledger, today)`** — dismissed, or deferred to a date still in the future.
- **`filter_pending(proposals, ...)`** — the proposals the user has not dismissed or actively deferred. What the digest actually shows.

## DAG position

Depends on `subsys.paths`. Consumed by `modernize` (filtering its report), `dreams` (the dreamer's proposals use the same triage), `cli` (`clauderize upgrade`), and `ops` (`cz_dismiss_proposal`, `cz_defer_proposal`, `cz_handle_dream_proposal`).
