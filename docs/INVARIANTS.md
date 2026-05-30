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
