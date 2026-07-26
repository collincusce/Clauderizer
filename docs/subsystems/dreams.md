---
id: subsys.dreams
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.paths
  - subsys.telemetry
  - subsys.proposals
last_verified: 2026-07-25
---

# Dreams

The dream journal — append-only, local-only **experiential** telemetry (D-058).

## What it records that telemetry cannot

`subsys.telemetry` records what the engine can observe: which lessons a handoff surfaced, whether a phase passed. Dream notes record what only the **responding agent** can observe — friction, gaps, surprises, corrections, ritual drift — as 2–4 sentence notes appended after a substantive exchange.

Full transcripts are never retained. That is the whole point of the substrate: a note is cheap in tokens and carries no PII, where a transcript is expensive in both.

## The two halves, and why they are separate

- **Capture** is cheap, continuous, and happens during work: `add_note(...)`.
- **Dreaming** is a distillation pass that runs offline over accumulated notes and produces advisory proposals.

They are separate because they have different costs and different failure modes. Capture must be nearly free or it will not happen; distillation is expensive and benefits from seeing many notes at once. A dreaming pass **consumes** notes irreversibly, which is why the watermark exists and why the two halves are never triggered by the same phrase.

## Capture

- **`note_id(...)`** / **`validate(note)`** — the id and the shape check. A note names a `kind` (friction, gap, surprise, correction, drift, win) and uses repo-relative paths.
- **`add_note(...)`** — the append. Written only by the blessed, write-locked op — never from a hook (INVARIANT-06).
- **`read_notes(path)`** — all notes in append order, tolerant of garbled lines.
- **`plea_state(...)`** — whether, and how loudly, the digest should ask for a dreaming pass.

## Distillation

- **`watermark_path(...)`** / **`consumed_ids(...)`** / **`unconsumed_notes(...)`** — the watermark. Notes already distilled are not distilled again, so a second pass over an unchanged journal produces nothing rather than duplicates.
- **`assemble(...)`** — the bundle a dreamer reasons over.
- **`dream_proposal_id(...)`** / **`stage_proposals(...)`** / **`read_proposals(...)`** / **`pending_proposals(...)`** / **`mark_handled(...)`** — staging and triage, sharing `subsys.proposals`' content-derived id scheme so a materially changed proposal re-surfaces and an unchanged dismissed one stays quiet.
- **`proposals_path(...)`** — where staged proposals live.
- **`schedule_path(...)`** / **`schedule_info(...)`** / **`register_schedule(...)`** — the optional recurring dreaming pass, recorded rather than executed: the engine never runs a scheduler.

## Constitution

Mirrors `telemetry.py` exactly — append-only (INVARIANT-03), local-only and gitignored (`.clauderizer/dreams.jsonl`, `dreams.schedule.toml`), deterministic, and never written from a hook. Nothing a dreamer produces is ever applied automatically; proposals go through triage, and the agent decides.

## Proven in practice

The first dream-sourced promotion was real and traceable end to end: a gap noticed mid-build was captured as a note, distilled by the dreamer, staged, triaged, accepted — and became the README tool-list pin test that caught the MCP surface sitting 14 tools behind. That is the loop working as designed: an observation that would otherwise have evaporated became an executable check.

## DAG position

Depends on `subsys.paths`, `subsys.telemetry` (the shared journal discipline) and `subsys.proposals` (the triage ledger). Written and read through `ops` (`cz_add_dream`, `cz_dream`, `cz_dream_propose`, `cz_handle_dream_proposal`, `cz_register_dream_schedule`) and surfaced by `rituals/status_bundle`. `feat.dream-loop` is the feature record.
