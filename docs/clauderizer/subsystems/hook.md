---
id: subsys.hook
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.rituals
  - subsys.nesting
  - subsys.tools-list
last_verified: 2026-07-25
---

# Hook

The event dispatcher behind the `clauderizer-hook` console script (D-025) — how a cold session learns where it is without anyone asking.

## The dispatcher

`dispatch.py` reads the host's hook payload (JSON on stdin), routes on `hook_event_name` to a read-only handler, prints whatever the handler returns, and **always exits 0**.

Always exiting 0 is INVARIANT-04, generalized to every event by INVARIANT-06. A hook that can block a session is a hook that can make the memory system the reason someone cannot work — which would be a worse failure than having no memory at all.

Two back-compatibilities the hardened probes depend on:

- **`--version` / `--help` answer before any stdin or repo read.** The identity probe must be fast and must not hang waiting for input that will never come (L-09/L-10). `init` and `doctor` both rely on this to identify the engine.
- **Empty, garbage, or non-object stdin falls back to the SessionStart digest.** Hosts differ in what they send and some send nothing; the useful default is to orient the session anyway.

## The handlers

One per host hook event, each taking the parsed payload (a dict, or `None`) and returning text to surface — or `None` to stay silent.

- **`session_start`** — the digest. The main event.
- **`user_prompt_submit`** — the relevance nudge on a new prompt.
- **`pre_compact`** / **`post_compact`** — orientation across a context compaction, which is exactly when a session is most likely to lose the thread.
- **`read_payload(stdin)`**, **`repo_paths_config(...)`**, **`build_digest(...)`** — the shared plumbing.

**Quiet when empty**: a handler returning `None` prints nothing. A hook that always says something trains the reader to skip it.

## What the host does with the output is not our contract

Claude Code injects `SessionStart` and `UserPromptSubmit` stdout and **drops** `PreCompact`/`PostCompact` stdout; kimi injects all four. The engine emits for every event it is wired for and does not pretend to know which land — the capability matrix in `docs/CROSS-HOST.md` records what is known, and `subsys.session` encodes it for the injection gate.

## Read-only, and why that is absolute

No handler writes. Not telemetry, not a dream note, not a cache. A hook fires on someone else's schedule, possibly concurrently with a session that holds the write lock, and possibly many times — so a hook that wrote could deadlock a session or corrupt a doc at exactly the moment nobody is watching. Registration self-heal, which *does* write, therefore rides CLI entry points instead (`subsys.bespoke_hosts`).

## At most once

The digest reaches the model at most once per session across all tiers (INVARIANT-08), via the in-memory signal in `subsys.session`. Nested installs defeat that structurally — two processes, each correct — which is `subsys.nesting`'s ownership test: an install that does not own the session's cwd stays silent.

## The wrapper below it

`sessionstart.py` is a back-compat shim re-exporting the handler and digest builder, so wiring that still points at `clauderizer.hook.sessionstart:main` behaves identically.

Below the engine sits the wrapper script (`subsys.hosts`): the harness injects only **stdout**, so a hook whose engine cannot spawn used to die silently with its error on stderr. The wrapper prints a breadcrumb instead.

## DAG position

Depends on `subsys.rituals` (the digest), `subsys.nesting` (the ownership gate), `subsys.tools-list` (the advertised surface), plus `paths`, `config` and `assets`. Invoked by the host, never imported by the engine.
