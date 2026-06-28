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

### INVARIANT-07 — Claude Code parity never regresses: any change that degrades the current Claude Code experience (hook-driven SessionStart/UserPromptSubmit auto-injection, the cz_* tool surface, skills, or the status digest) is a release blocker. Cross-host generalization is strictly additive.

Claude Code parity never regresses: any change that degrades the current Claude Code experience (hook-driven SessionStart/UserPromptSubmit auto-injection, the cz_* tool surface, skills, or the status digest) is a release blocker. Cross-host generalization is strictly additive.

### INVARIANT-08 — Cross-host status injection reaches the model at most once per session, across all active tiers (hook, auto-resource, prompt, AGENTS.md floor, and the server-side bootstrap), deduplicated via an in-memory, read-only, session-scoped signal — never a persisted/config flag (per INVARIANT-05) and never from a path that mutates docs or blocks the session (per INVARIANT-06). Injected status stays focused and minimal (per D-027).

Cross-host status injection reaches the model at most once per session, across all active tiers (hook, auto-resource, prompt, AGENTS.md floor, and the server-side bootstrap), deduplicated via an in-memory, read-only, session-scoped signal — never a persisted/config flag (per INVARIANT-05) and never from a path that mutates docs or blocks the session (per INVARIANT-06). Injected status stays focused and minimal (per D-027).

### INVARIANT-09 — All lexical-overlap and similarity computations in the engine use the single canonical tokenizer analyze._tokens — there is exactly one token-splitter definition under src/, and the near-duplicate-lesson threshold is single-sourced (analyze._LESSON_DUP_JACCARD), so relevance ranking, the abstract-index token_set, the write-time near-duplicate advisory, and the corpus-health/curator redundancy metric all share one definition of "near-duplicate". Promotes D-041 from a project decision to a hard, machine-checked rule now that tests/test_canonical_tokenizer.py enforces it (exactly one `def _tokens` in src/ + import identity + threshold parity); a second fork makes the suite fail.
**Introduced by**: D-041

All lexical-overlap and similarity computations in the engine use the single canonical tokenizer analyze._tokens — there is exactly one token-splitter definition under src/, and the near-duplicate-lesson threshold is single-sourced (analyze._LESSON_DUP_JACCARD), so relevance ranking, the abstract-index token_set, the write-time near-duplicate advisory, and the corpus-health/curator redundancy metric all share one definition of "near-duplicate". Promotes D-041 from a project decision to a hard, machine-checked rule now that tests/test_canonical_tokenizer.py enforces it (exactly one `def _tokens` in src/ + import identity + threshold parity); a second fork makes the suite fail.
