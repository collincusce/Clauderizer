---
name: clauderizer-dream
description: Run the dreaming ritual — triage staged dream proposals, then distill accumulated dream notes into new staged proposals via cz_dream. Use when the digest says "Dreams. N note(s) awaiting the dreamer", shows "(N dream)" proposals awaiting triage, or the user says "dream" / "run the dreamer".
---

# The dreaming ritual

Dream notes (`cz_add_dream`, one per substantive exchange) accumulate in a
local journal; this skill turns them into durable memory. The two halves
usually happen in DIFFERENT sessions — staged proposals wait for next session's
fresh eyes, which is the point of dreaming offline (D-059).

1. **Triage first — the last dream's output.** If the digest shows "(N dream)"
   proposals awaiting triage, ask-first like modernize ("triage now or keep
   working?"), then walk each pending proposal (ids and details via `cz_dream`'s
   `blocked_on_triage` state or the store the digest counts):
   - **handle** — do the work via its suggested `op`/`args` (or your better
     judgment) through the normal blessed writes, then
     `cz_handle_dream_proposal(id)`;
   - **dismiss** — `cz_dismiss_proposal(id)` — not durable signal after all;
   - **defer** — `cz_defer_proposal(id, days)` — real, but not now.

2. **Then dream, if ripe.** Call `cz_dream`:
   - `blocked_on_triage` → back to step 1; dreaming never piles proposals onto
     unactioned ones (A-001).
   - `not_ripe` → report the count and stop — keep capturing notes.
   - `ripe` → judge each cluster: a durable lesson, correction, decision, doc
     gap, or procedure drift? Draft ONE proposal per real signal:
     `{detail (≤600 chars, PII-free), op (the blessed cz_* write a handler
     would run), args, evidence (the cluster's note ids)}`.

3. **Stage everything in one call.** `cz_dream_propose(proposals=[...],
   reviewed_note_ids=[every note id across ALL clusters — including clusters
   judged NOT durable, so they never re-ripen])`. Empty `proposals` with
   `reviewed_note_ids` is a legitimate "dreamed, nothing durable" outcome.
   Restaging identical content is a safe no-op (content-hash ids), so an
   interrupted pass just re-runs.

4. **Never hand-edit** the journal, the proposal store, or the watermark —
   `.clauderizer/dreams.jsonl`, `proposals.dream.jsonl`, and
   `dreams.watermark.json` are engine-owned, local-only, gitignored state
   (notes and proposal details are PII-linted at write time; only accepted,
   reviewed writes ever become tracked memory).

**Headless variant** (no MCP, scheduled/`-p` sessions): the identical flow runs
via `clauderize ops <file.json|->` with the exact op names and args above — a
cron or batch session can dream unattended and leave staged proposals for the
next interactive session to triage.

**Schedule it, then say so.** If the session-start digest carries the 🌙 plea
(notes accumulating, no schedule registered), help the user set one up —
a Claude Code daily routine running `/clauderizer-dream` in this repo, or
`cron: 0 7 * * *  cd <repo> && claude -p "/clauderizer-dream"` — and then
record it so the plea retires:
`cz_register_dream_schedule(method="claude-code-routine"|"cron", cadence="daily 07:00", command="...")`.
A user who prefers running it by hand records `method="manual"` — an honest
verdict that quiets the plea while the loop, gauges, and this skill stay fully
active. Clearing (`method=""`) revives the plea.
