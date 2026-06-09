# Distilled Lessons

> Project-level lessons promoted from gameplans (`cz_promote_lesson`).
> Every future handoff carries this list, so it must stay compact: obsolete
> entries that stop earning their place (`cz_obsolete_lesson` with the `L-NN`
> id). Entries are never deleted, only marked.

## Lessons

### Category: Process

**L-01.** Markdown round-trip idempotency (apply-twice == apply-once) is the load-bearing test for every mutation. *(from 2026-05-30-clauderizer-v1-bootstrap)*

### Category: Observability

**L-02.** Health checks must verify capability, not just presence — a green check on a non-launchable setup is worse than no check. *(from 2026-05-30-clauderizer-v1-bootstrap)*

### Category: Design

**L-03.** Name tools by their effect: a context fetch must never mutate the tree. *(from 2026-05-30-clauderizer-v1-bootstrap)*

**L-05.** Every tracked write needs a CLI-reachable fallback: an MCP-only mutation surface deadlocks any session whose server cannot connect, stranding exactly the sessions that most need to record what broke. *(from 2026-06-09-context-economics)*

**L-06.** Round-tripping through the engine's own parser is necessary but not sufficient: tests must assert render-validity for external readers too (contiguous tables, valid markdown) - an engine can read its own corruption indefinitely. *(from 2026-06-09-engine-structural-robustness)*

### Category: Integration

**L-04.** Every file the engine writes must round-trip through its own parser in tests; never swallow config parse errors silently. *(from 2026-06-09-discipline-seams)*
