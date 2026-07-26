---
id: subsys.learn
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Learn

The failure miner — scan session transcripts for failure→fix patterns and propose draft corrections and lessons.

## Shape

Read-only, deterministic, stdlib-only. It is **invoked**, never auto-fired, and it **proposes**, never writes: the agent routes accepted proposals through `cz_add_correction` / `cz_add_lesson` (D-015/INVARIANT-05), which keeps the append-only guarantee (INVARIANT-03) intact and keeps a machine out of the business of deciding what this project learned.

- **`mine(path)`** — proposals mined from one JSONL transcript.
- **`mine_dir(d)`** — `{file: [proposals]}` across every `*.jsonl` under a directory.

## Three detectors

1. **Tool error → same-tool success** within a small window. The window is what makes it a *fix* rather than a coincidence; a success an hour later is unrelated work.
2. **`pytest "N failed"` → later "passed"** with no failures in between. A special case of (1) worth its own detector because the test suite is where this project's corrections actually surface.
3. **An explicit short user correction** — "no, …", "that's wrong", "instead …". Short is a real criterion: a long message is usually a new instruction, not a correction of the last one.

## Tuned for precision over recall

This is the design decision that matters most, and it is a deliberate trade. A noisy proposer would flood the curated store that the memory gauge exists to keep small — and the cost asymmetry is stark: a missed lesson can be recorded later by hand, while a corpus full of low-value proposals trains the agent to skim past all of them, including the good ones. A proposer that cries wolf earns its way into the ignore list, and after that it is worse than absent because it still costs tokens.

So all three detectors are narrow by construction, and the honest claim is that this finds *some* of the failure→fix patterns in a transcript, not all of them.

## DAG position

Depends on nothing — stdlib only, no engine imports, which is what lets it run against arbitrary transcript files without a repo. Consumed by `ops` as `cz_mine_failures`. Its proposals converge with `subsys.dreams` (which captures what only the responding agent can observe) and `subsys.telemetry` (which records what the engine can measure); this one mines what the transcript happens to show.
