---
id: subsys.session-ledger
type: subsystem
version: 0.1.0
status: active
depends_on:
  - subsys.paths
last_verified: 2026-07-27
---

# Session Ledger

Per-machine session evidence for heal-on-proof stranded-state detection (D-070
P1): an append-only, gitignored `.clauderizer/sessions.jsonl` that turns a
tracker row's "in_progress" from an assertion into a checkable claim.
Disposable evidence, never authority (D-067/D-013) — markdown stays canonical,
deleting the file merely degrades detection to inconclusive.

**`stamp(paths, gameplan, phase, today=None)`** appends one line of claimant
identity — pid, `/proc` start time (None where unmeasurable), hostname, agent
(`session.detect_session_agent`), transport (mcp | cli | unknown, from argv0)
— when `transition_phase` moves a phase to `in_progress`. Best-effort and
silent on any failure: identity bookkeeping never fails a transition. The
caller already holds the write lock.

**`last_stamp(paths, gameplan, phase)`** returns the most recent stamp for the
pair, tolerant of torn/corrupt lines (a bad line is "no evidence", never a
crash). Read-only.

**`probe(entry)`** grades a stamp `dead` | `alive` | `inconclusive`. Only a
same-host, **mcp-transport** stamp can grade dead — a CLI process exits by
design the moment it returns, so its death proves nothing. Dead means the pid
is gone (`ProcessLookupError`) or the recorded start time no longer matches
the live process (PID reuse). Everything unprovable — different host, cli or
unknown transport, unreadable `/proc`, malformed pid — is inconclusive, which
downstream heals nothing: a wrong "dead" strands a healthy session, a wrong
"alive" merely delays healing.

**POSIX gate** (binding vetting condition): on non-posix platforms `probe`
returns inconclusive **without any `os.kill` call** — win32's `os.kill`
delivers CTRL_C_EVENT/TerminateProcess, and a read path must never signal a
live process. On POSIX, signal 0 is an existence check that delivers nothing.

Consumers: `rituals/stranded.py` (the judgment-menu detector) and
`rituals/interrupted.py` (whose liveness gate keeps one voice per repo state).
Pinned by `tests/test_stranded_state.py`, including the display-only contract
(the read path writes zero bytes) and the never-signal-on-non-posix spy.
