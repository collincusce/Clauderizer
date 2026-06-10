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

### D-009 — Cumulative memory gets consolidation pressure, not caps

**Context**: Finding 5: append-only memory + cumulative handoffs grow monotonically; the only pruning was the (obsolete) marker, with nothing driving it and no cross-gameplan continuity for lessons.
**Decision**: Memory stays append-only — no caps, no auto-deletion, no LRU. Counter-pressure is three blessed writes plus visibility: cz_consolidate_lessons (N->1 within a gameplan), cz_promote_lesson (gameplan lesson -> compact project docs/LESSONS.md carried by all future handoffs), and a memory gauge in the status digest that warns past a documented threshold and names the remedies.
**Consequences**: Handoffs can shrink without losing the audit trail; lessons survive gameplan close through deliberate curation rather than bulk carryover; bloat is a visible, nudged state instead of a silent failure mode.

### D-010 — Probes must traverse the consumer's executor or downgrade their claim

**Context**: H-08: doctor certified the SessionStart hook "verified end-to-end via wsl.exe round-trip" while every harness session got no digest — the harness on Windows interposes Git Bash, whose MSYS2 path conversion mangles the shim's argv before wsl.exe spawns. The probe spawned wsl.exe directly and so traversed a leg the consumer never uses (L-09; third instance of the false-green family after H-06 and the D4/spawn-probe composition).
**Decision**: Every launchability/identity check must name the executor it actually traversed, and may claim "end-to-end" only when it traversed the consumer's real leg — for SessionStart hooks on a windows-wsl session host, that means spawning through the harness's executor (Git Bash via WSL interop when present). Where the real leg is untraversable from the checking host, the check reports honest unverifiability (the exit-3 pattern), never a green.
**Consequences**: Doctor's hook-leg check gains an executor-traversing probe and reworded verdicts; the wiring validation matrix (Git Bash, cmd.exe, PowerShell) becomes part of init's spawn-test contract; any future probe design starts from "which leg does the consumer use and can I traverse it".

### D-011 — Push-then-release is enforced by a check, not remembered by a person

**Context**: v0.7.0 and v0.8.0 were both double-claimed in one day by the same mechanism: a GitHub-UI Release tags the REMOTE branch head, and the staged work — including the publish gate that would have caught it — was local-only at that moment (H-07, lesson L-08). The four version registries (source, remote tags, Releases, PyPI) never sync themselves, and uvx-by-name answers from cache.
**Decision**: Ship a release preflight check (O3) that fails red unless: origin/main == the staged release commit; the version is unclaimed across all four registries queried fresh (git tag -l, git ls-remote --tags, Releases API, PyPI index directly); and publish.yml at the staged commit contains the tag==source gate. No tag or Release is cut while the check is red.
**Consequences**: The release ritual becomes mechanical (run the check, then tag/Release); lesson #8's release-flow steps and L-08's sweep stop being prose-only; O4's 1.0 readiness gates get a natural home next to this check; the check itself needs a way to simulate skew in tests (prove the guard fires).
