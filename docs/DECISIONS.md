# Decisions

Project-wide architectural decision records (ADRs). Append-only. Numbered `D-NNN`.
Superseded decisions stay in the record with a `Status: superseded` note.

## Decisions

_(Add entries with `cz_add_decision`.)_

### D-001 — Markdown is the source of truth

**Context**: Agents need durable, human-readable, git-diffable memory.
**Decision**: All state lives in markdown; the graph index is a disposable cache rebuilt on demand.
**Consequences**: If index and markdown disagree, markdown wins. No database.

### D-002 — Engine in Python via pipx/uvx

**Context**: Need one broadly-installable engine.
**Decision**: Implement in Python; distribute with pipx/uvx.
**Consequences**: Covers ~99% of dev machines.

### D-003 — Zero-dependency core; mcp optional

**Context**: A drop-in must work with nothing pre-installed.
**Decision**: Core uses stdlib + a vendored frontmatter parser; mcp is an optional extra.
**Consequences**: uvx clauderize init needs nothing; only the server needs the SDK.

### D-004 — Host-language support is profile data

**Context**: Must clauderize Node/Go/Ruby/Python repos.
**Decision**: A profile is a TOML data file of test/build/lint commands; the engine is host-agnostic.
**Consequences**: Adding a language is a new <lang>.toml, not code.

### D-005 — Graph index is JSON, not SQLite

**Context**: Graphs are tens-to-hundreds of nodes.
**Decision**: Cache to a rebuildable index.json.
**Consequences**: Full rescan is milliseconds; no ORM.

### D-006 — Cascade stays judgment-based

**Context**: True affected? calls need human/AI judgment.
**Decision**: The tool finds dependents and marks them needs-review; the agent decides.
**Consequences**: Preserves post-hoc cascade rather than faking automation.

### D-007 — Single mutation path

**Context**: Edits must stay valid and idempotent.
**Decision**: Every structured write routes through markdown/writer.py.
**Consequences**: No tool does a free-form replace.

### D-008 — Engine-regenerated regions in shared docs are marker-delimited

**Context**: cz_write_handoff regenerates PHASE-N-HANDOFF.md by overwriting the whole file, destroying agent enrichment; meanwhile init already merges the CLAUDE.md stanza through marker blocks without clobbering user text.
**Decision**: Any engine-regenerated content inside a document that agents or humans may also edit is delimited by <!-- clauderizer:NAME:start/end --> markers and rewritten via writer.upsert_marker_block. Regeneration replaces only the block; everything outside is preserved byte-for-byte.
**Consequences**: Handoffs become safely enrichable; the CLAUDE.md stanza and handoffs now follow one pattern; future generated regions (e.g. status digests embedded in docs) inherit it.
