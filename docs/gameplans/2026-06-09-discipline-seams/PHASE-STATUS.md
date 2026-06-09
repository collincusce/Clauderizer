# Discipline Seams — Phase Status Tracker

> Living document. Updated after each phase completes.
> Last updated: 2026-06-09

## Phase Status

| Phase | Name | Status | Started | Completed | Handoff |
|-------|------|--------|---------|-----------|---------|
| 0 | Blessed cascade resolution & lesson obsolescence | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-0-HANDOFF.md |
| 1 | Marker-protected handoff regeneration | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-1-HANDOFF.md |
| 2 | Fresh baseline & completed-gameplan status | ✅ COMPLETE | 2026-06-09 | 2026-06-09 | handoffs/PHASE-2-HANDOFF.md |

## Outputs Registry

_(Concrete values produced by completed phases that later phases need.)_

## Corrections Log

### C-01 — Phase planning

**Phase**: planning
**What gameplan said**: gameplan-internal decisions would number from D1
**What was actually correct**: they numbered from D3: next_numbered_id scanned the GAMEPLAN template placeholder text 'Gameplan-internal decisions D1, D2, ...' as real IDs
**Why**: auto-numbering reads the whole document text, including scaffold placeholders, before the first append replaces them
**Lesson**: Auto-numbering must not count IDs that only appear in scaffold placeholder prose — strip placeholders before scanning, or use ID patterns anchored to heading lines.

### C-02 — Phase 2

**Phase**: 2
**What gameplan said**: preflight already measures the test count; phase 2 only needed to write it back
**What was actually correct**: the count was never measured on this repo: init's own profile.lock.toml was invalid TOML (unescaped \d in the regex), load_for_repo silently fell back to packaged defaults, and the packaged 'pytest -q' doubled the project's addopts -q into -qq, which suppresses the summary line the regex parses
**Why**: to_lock_toml emitted lock values without TOML escaping, and parse failures were swallowed silently
**Lesson**: Every file the engine writes must round-trip through its own parser in tests; silent fallback on config parse errors is a footgun — surface it (doctor now checks the lock parses).
