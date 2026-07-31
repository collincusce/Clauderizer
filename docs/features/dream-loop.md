---
id: feat.dream-loop
type: feature
status: active
depends_on:
  - subsys.mcp-server
  - subsys.mutations
  - subsys.rituals
  - subsys.scaffold
last_verified: 2026-07-25
gameplan: 2026-07-23-dreaming-loop
summary: Dream-note journal + cz_add_dream blessed write, ripeness-gated cz_dream assembly, dream proposals in the unified triage queue, clauderizer-dream skill and loop integration. Notes are DREAMED, proposals are TRIAGED — the two are lexically distinct since A-002.
---

# Dream Loop

The experiential layer (D-058/D-059): while an agent works, it leaves short notes about what only *it* could observe — friction, gaps, surprises, corrections, drift, wins — and an offline pass later distills them into proposed memory changes for a human to approve. Sleep for the project's memory. Nothing becomes tracked memory without review.

## Two artifacts, two verbs — and they are not interchangeable

| Artifact | Written by | Consumed by | Digest line |
|---|---|---|---|
| **dream NOTE** — a raw 2–4 sentence capture | `cz_add_dream`, once per substantive exchange | **DREAMING** (`cz_dream` → `cz_dream_propose`) | `Dream notes: N raw capture(s) awaiting DREAMING` |
| **dream PROPOSAL** — the dreamer's judged output | a dreaming pass | **TRIAGE** (`cz_handle_dream_proposal` / `cz_dismiss_proposal` / `cz_defer_proposal`) | `⚙ N proposal(s) awaiting TRIAGE (M dream)` |

Calling both of them "dreams" is not a cosmetic problem, which is why each line now carries its own noun *and* its own verb (A-002). Asked to "take care of the dream notes", a session ran the **dreamer** — capturing more notes and staging four proposals nobody requested — when the ask was to **triage** what the dreamer had already produced. The damage is asymmetric and that is the whole argument: triage is idempotent and reversible, while a dreaming pass advances an append-only watermark, so the notes it consumes **cannot be un-consumed**. When the ask is ambiguous, the skill says to ask.

## The gating

Staged proposals **block** further dreaming (A-001): the loop never piles new proposals onto unactioned ones, so when both halves are pending, triage is the only one that can proceed. Dreaming is additionally **ripeness-gated** — fewer unconsumed notes than the floor returns `not_ripe` and the correct response is to keep capturing, not to force a pass.

## Where the state lives

`.clauderizer/dreams.jsonl` (the journal), `proposals.dream.jsonl` (staged proposals) and `dreams.watermark.json` (which notes this machine has consumed) are **machine-local and gitignored** — the loop runs where the journal lives, so a cloud routine cloning the repo sees an empty journal. Notes and proposal details are PII-linted at write time; only accepted proposals become tracked memory, and then only through the normal blessed writes. `dreams.schedule.toml` is the per-user self-report that retires the session-start plea (A-004) — the engine cannot see crontabs, so an honest self-report is the only available substrate, and `method="manual"` is a legitimate answer that quiets the plea while leaving the loop fully active.

## Judgment stays with the agent

`cz_dream` **assembles** — bounded clusters, exemplar-only full text, corpus-health and lesson-utility flags, one-hop graph adjacency — and never decides (INVARIANT-05). The agent judges each cluster into proposals, or records an honest "dreamed, nothing durable" pass by staging none while still consuming the reviewed notes, so they never re-ripen.
