# Invariants

Rules that hold across all work. Append-only. Numbered `INVARIANT-NN`.

## Invariants

_(Add entries with `cz_add_invariant`.)_

### INVARIANT-01 — Markdown is canonical — the index is rebuilt from it on disagreement.

Markdown is canonical — the index is rebuilt from it on disagreement.

### INVARIANT-02 — Every structured edit goes through markdown/writer.py.

Every structured edit goes through markdown/writer.py.

### INVARIANT-03 — Append-only memory (decisions, invariants, hardening, lessons) is never deleted.

Append-only memory (decisions, invariants, hardening, lessons) is never deleted.

### INVARIANT-04 — The SessionStart hook never blocks a session — it always exits 0.

The SessionStart hook never blocks a session — it always exits 0.

### INVARIANT-05 — Discipline gates (clarify/open-items, exit-criteria, analyze-against-invariants) are advisory and judgment-based: they surface findings in tool results for the agent to act on, and MUST NOT hard-block a mutation or phase transition, nor introduce an enable/disable config flag. The engine surfaces candidates; the agent decides.
**Introduced by**: D-015

Discipline gates (clarify/open-items, exit-criteria, analyze-against-invariants) are advisory and judgment-based: they surface findings in tool results for the agent to act on, and MUST NOT hard-block a mutation or phase transition, nor introduce an enable/disable config flag. The engine surfaces candidates; the agent decides.

### INVARIANT-06 — Every hook event handler is read-only and always exits 0 — a memory tool never mutates docs or blocks a session from inside a hook. Generalizes INVARIANT-04 from SessionStart to all dispatched events (SessionStart, UserPromptSubmit, PreCompact, PostCompact, ...).
**Introduced by**: D-025

Every hook event handler is read-only and always exits 0 — a memory tool never mutates docs or blocks a session from inside a hook. Generalizes INVARIANT-04 from SessionStart to all dispatched events (SessionStart, UserPromptSubmit, PreCompact, PostCompact, ...).
