# Hardening

**Append-only** persistent risk tracker. NEVER delete entries — mark a risk
resolved with a date instead. This is a permanent audit trail. Numbered `H-NN`.

## Risks

### H-01 — Generated .mcp.json uvx fallback omits the [mcp] extra, so the MCP server cannot start in clean environments

- **Severity**: high
- **Status**: open (2026-06-09)
- **Affected**: src/clauderizer/scaffold/init.py (DEFAULT_RUN), generated .mcp.json
- **Impact**: In a fresh container (no console scripts on PATH, cold uvx cache) the SessionStart hook works but the MCP server prints an install hint and exits before the stdio handshake; the session silently gets zero cz_* tools and the whole blessed-write surface is unreachable.
- **Root cause**: DEFAULT_RUN = ["uvx", "--from", "clauderizer"] resolves the package without the mcp optional dependency (D-003 makes mcp an extra), so clauderizer-mcp aborts on import.
- **Reproduction**: Clone a clauderized repo into a clean container; run uvx --from clauderizer clauderizer-mcp; it prints: The MCP server needs the mcp package, and exits.
- **Recommended fix**: Fallback should be uvx --from "clauderizer[mcp]"; this repo .mcp.json hand-fixed 2026-06-09 as immediate wiring repair.

### H-02 — doctor MCP-server check verifies presence, not capability — green while the server cannot serve

- **Severity**: medium
- **Status**: open (2026-06-09)
- **Affected**: src/clauderizer/doctor.py (MCP server command check)
- **Invariant violated**: L-02: health checks must verify capability, not just presence
- **Impact**: doctor reported "MCP server command runnable" in the exact session where the server could not complete an MCP handshake (missing mcp SDK). The install looks healthy while the entire tool surface is down — the failure mode promoted lesson L-02 exists to prevent.
- **Root cause**: The check only confirms the command resolves/launches; it never drives an initialize round-trip, so an import-error banner on stdout still passes.
- **Reproduction**: Break the mcp extra (clean uvx env), run clauderize doctor: MCP check is green; an actual stdio initialize fails.
- **Recommended fix**: doctor should perform a real JSON-RPC initialize handshake against the configured .mcp.json command and require a valid response.

### H-03 — doctor treats the absent (gitignored) index cache as fatal drift and prescribes the wrong remedy

- **Severity**: low
- **Status**: open (2026-06-09)
- **Affected**: src/clauderizer/doctor.py (index cache check + drift message)
- **Impact**: Every fresh clone of a clauderized repo fails doctor (exit 2) on "index cache present", even though the cache is deliberately gitignored as a disposable artifact (D-001/D-005) and everything self-heals. The suggested fix, re-run clauderize init, is heavier than the actual remedy, clauderize reindex.
- **Root cause**: The check asserts file presence for a cache the same project defines as rebuildable-on-demand; the drift epilogue hardcodes init as the repair.
- **Reproduction**: Fresh clone, run clauderize doctor: exit 2 with only the index-cache check failing; clauderize reindex fixes it.
- **Recommended fix**: Auto-rebuild the cache during doctor (or downgrade to advisory), and make the epilogue name the per-check remedy.

### H-04 — Gameplan closure is not machine-readable; the digest nags forever after close-out

- **Severity**: medium
- **Status**: open (2026-06-09)
- **Affected**: src/clauderizer/rituals/status_bundle.py (completed-gameplan next_action), gameplan tracker state
- **Impact**: context-economics was fully closed (post-mortem on disk, D6 final cascade run and resolved, pending cascades 0 — commit 5487b0b), yet cz_status/SessionStart still tell every new session to "Close out the gameplan (post-mortem, final cascade)". A cold-start session cannot determine from memory alone whether close-out happened; this session had to consult git log. "Closed" only exists implicitly when the next gameplan repoints [active_gameplan].
- **Root cause**: No closed status is ever written anywhere the digest reads; all-phases-complete is indistinguishable from closed-and-awaiting-next-initiative.
- **Reproduction**: Repo at 7cf5ae1: POST-MORTEM.md exists, pending cascades 0, digest next_action still says to write the post-mortem and run the final cascade.
- **Recommended fix**: Give the gameplan a blessed closed transition (natural fit with the tracker-header blessed write: GAMEPLAN.md "> Status:" line) and have the digest read it.

### H-05 — Tracker header lines contradict reality on disk — live confirmation of the unblessed-writes open thread

- **Severity**: medium
- **Status**: open (2026-06-09)
- **Affected**: docs/gameplans/*/GAMEPLAN.md and CHAT-HANDOFF-INDEX.md header lines; missing blessed writes in src/clauderizer/mutations.py
- **Impact**: Cold-start recovery hits direct memory-vs-reality contradictions: both recent GAMEPLAN.md headers read "> Status: Planning" and both CHAT-HANDOFF-INDEX.md headers read "> Status: Phase 0 ready" while every phase is COMPLETE and post-mortems exist. An agent trusting headers over the graph would re-plan finished work. Both post-mortems predicted this (unblessed tracker headers / Outputs Registry / per-phase summaries); this records the live evidence with a closeable ID.
- **Root cause**: No cz_* tool may touch "> Status:" / "> Last updated:" headers, the Outputs Registry, or per-phase completion summaries; the no-hand-edit rule then guarantees they go stale.
- **Reproduction**: head -5 docs/gameplans/2026-06-09-context-economics/CHAT-HANDOFF-INDEX.md on 7cf5ae1: "Status: Phase 0 ready"; cz_status: all phases complete.
- **Recommended fix**: Blessed header/summary writes via writer.py (D-007), marker-delimited where regenerated (D-008); slated for the engine-robustness gameplan.
