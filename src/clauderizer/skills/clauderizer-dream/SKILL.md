---
name: clauderizer-dream
description: The dream loop has TWO halves with two artifacts — do the one being asked for. TRIAGE staged dream PROPOSALS (handle/dismiss/defer what the dreamer already produced); DREAMING distills raw dream NOTES into new proposals via cz_dream. Use for TRIAGE when the digest shows "proposal(s) awaiting TRIAGE (N dream)" or the user says "triage the dream proposals" / "take care of the dream notes" / "action what the dreamer produced" — that last phrasing means triage, not a new dreaming pass. Use for DREAMING when the digest shows "Dream notes: N raw capture(s) awaiting DREAMING" or the user says "dream" / "run the dreamer" / "distill the notes". When genuinely ambiguous, ask — a dreaming pass consumes notes irreversibly.
---

# The dream loop — two artifacts, two verbs

**Read this before acting. The loop has two halves, and doing the wrong one is
not recoverable.**

| Artifact | Written by | Consumed by | Digest line |
|---|---|---|---|
| **dream NOTE** — a raw 2–4 sentence capture | `cz_add_dream`, per exchange | **DREAMING** (`cz_dream` → `cz_dream_propose`) | `Dream notes: N raw capture(s) awaiting DREAMING` |
| **dream PROPOSAL** — the dreamer's judged output | a dreaming pass | **TRIAGE** (handle / dismiss / defer) | `⚙ N proposal(s) awaiting TRIAGE (M dream)` |

**Which half is being asked for?** "Triage the dream proposals", "action what
the dreamer produced", and — the phrasing that once misrouted a live session —
"take care of the dream notes" all mean **TRIAGE**: act on what already exists.
"Dream", "run the dreamer", "distill the notes" mean **DREAMING**: produce new
proposals. If the ask is genuinely ambiguous, **ask** — a dreaming pass advances
an append-only watermark, so the notes it consumes cannot be un-consumed, and it
stages proposals nobody requested.

Triage is also the half the loop *gates* on: staged proposals block `cz_dream`
(A-001), so when both are pending, triage is the only thing that can proceed.
The two halves usually happen in DIFFERENT sessions — staged proposals wait for
next session's fresh eyes, which is the point of dreaming offline (D-059).

1. **Triage first — the last dream's output.** If the digest shows "(N dream)"
   proposals awaiting TRIAGE, ask-first like modernize ("triage now or keep
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
   `dreams.watermark.json` are engine-owned, machine-local state. Only
   `dreams.jsonl` is gitignored by `init` today; `proposals.dream.jsonl` and
   `dreams.watermark.json` are committed unless you ignore them yourself
   (fix landing in 1.14.0). That matters on a shared repo: the watermark
   records which notes THIS machine has consumed, so a teammate who pulls it
   can be told notes were already dreamed against a journal they do not have
   (notes and proposal details are PII-linted at write time; only accepted,
   reviewed writes ever become tracked memory).

**Headless variant** (no MCP, scheduled/`-p` sessions): the identical flow runs
via `clauderize ops <file.json|->` with the exact op names and args above — a
cron or batch session can dream unattended and leave staged proposals for the
next interactive session to triage.

**Headless behavior**: there is no one to ask, so skip every ask-first prompt
and do NOT triage — triage is the interactive session's half of the loop. If
`cz_dream` is `ripe`, judge and stage in one pass (`cz_dream_propose` with
`reviewed_note_ids`); if `blocked_on_triage` or `not_ripe`, report one line and
exit. Never register or change the schedule from a headless run.

**Schedule it, then say so.** If the session-start digest carries the 🌙 plea
(notes accumulating, no schedule registered), help the user set one up —
a Claude Code daily routine running `/clauderizer-dream` in this repo, or
cron (the headless-verified shape — `-p` sessions do NOT auto-attach the
project MCP server and need the tool allowances up front):

```
0 7 * * * cd <repo> && claude -p "/clauderizer-dream" \
  --mcp-config .mcp.json \
  --allowedTools "mcp__clauderizer__*,Bash(clauderize:*),Bash(.venv/bin/clauderize:*)" \
  >> "$HOME/.clauderizer-dream-cron.log" 2>&1
```

The dreaming loop runs where the JOURNAL lives — dream notes are machine-local
and gitignored, so a cloud routine cloning the repo sees an empty journal;
schedule on the machine you work from. Then record it so the plea retires:
`cz_register_dream_schedule(method="claude-code-routine"|"cron", cadence="daily 07:00", command="...")`.
A user who prefers running it by hand records `method="manual"` — an honest
verdict that quiets the plea while the loop, gauges, and this skill stay fully
active. Clearing (`method=""`) revives the plea.
