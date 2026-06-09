# Hardening

**Append-only** persistent risk tracker. NEVER delete entries — mark a risk
resolved with a date instead. This is a permanent audit trail. Numbered `H-NN`.

## Risks

### H-01 — Checked-in launch wiring was non-launchable on the working machine; cold start silently lost the digest and every cz_* tool

- **Severity**: high
- **Status**: mitigated (2026-06-09)
- **Affected**: .mcp.json; .claude/settings.json; scaffold/init.py command resolution; CLAUDE.md stanza (documents cz_status but no CLI fallback)
- **Invariant violated**: L-02: health checks must verify capability, not presence - the committed wiring itself was never capability-checked on the host that runs sessions
- **Preconditions**: Session host without uvx on PATH (here: both Windows host and the WSL distro)
- **Impact**: On this machine the SessionStart hook and MCP server both invoked uvx, which is installed neither in WSL nor on Windows. A cold session got no [Clauderizer] digest and no cz_* tools - the entire blessed-write surface was unreachable - and nothing in-session surfaced the failure: a hook that cannot spawn prints nothing, and a missing MCP server just looks like an un-clauderized repo.
- **Root cause**: Wiring files were committed with the uvx fallback command rather than the venv console scripts; doctor catches the breakage but only when run by hand - the cold-start path has no breadcrumb when the hook dies
- **Reproduction**: Start a Claude Code session on a host without uvx: no digest, no cz_* tools. `clauderize doctor` (repo source) -> 'MCP server command runnable' and 'SessionStart hook command runnable' both FAIL
- **Recommended fix**: Local wiring repaired this session: editable venv reinstalled and `clauderize init` re-run from .venv, doctor now all-green. Engine-side (open): the CLAUDE.md stanza should name the CLI fallback (`clauderize status`) so a session without MCP can self-orient; doctor could also compare the executed engine version against the repo source version when the repo IS the engine (dogfood skew).
- **Regression tests**: None yet - candidate: init warns loudly when the command it writes does not resolve on the current host
- **Resolution**: Wiring repaired to the editable venv (doctor 13/13 incl. new D9 identity checks); stanza now names the CLI fallback. Residual: a hook that cannot spawn still leaves no in-session breadcrumb - carried as an open thread in the 0.6.0 post-mortem.
### H-02 — Blessed phase-table writes emit invalid markdown tables, and the engine's own parser hides it

- **Severity**: medium
- **Status**: resolved (2026-06-09)
- **Affected**: mutations.add_phase (row appended via writer.append_to_section as a paragraph); templates/gameplan/CHAT-HANDOFF-INDEX.md (legend inside the table's section, directly after row 0); rituals/_tables.parse_phase_table (tolerates non-table layout)
- **Invariant violated**: Extends L-01/L-04: round-tripping through the engine's own parser is necessary but not sufficient - written artifacts must be valid for external renderers too
- **Preconditions**: Any gameplan with more than one phase
- **Impact**: Every gameplan's Phase Status Table renders broken for humans: rows appended after phase 0 are separated by blank lines - and in CHAT-HANDOFF-INDEX by the legend paragraph - so renderers show a one-row table plus orphaned row fragments. parse_phase_table scans any pipe-prefixed line in the section, so cz_status reads the corrupt layout fine and round-trip tests pass. Evidence: all four tracker docs of the two closed 2026-06-09 gameplans.
- **Root cause**: Phase rows are appended as new paragraphs at the end of the section instead of being inserted into the existing table block
- **Reproduction**: cz_add_phase twice on a fresh gameplan, then render CHAT-HANDOFF-INDEX.md: blank line and legend split the table
- **Recommended fix**: Table-aware row insertion in the writer (insert after the last contiguous row of the section's first table block); move the legend out of the table section in the template; add a render-validity regression (no blank lines or prose between a table's rows). One-time repair of the four existing broken trackers via the fixed write path.
- **Regression tests**: None yet - candidate listed in recommendation
- **Resolution**: 0.6.0 Phase 0: rows write through markdown/tables.py (contiguous block rebuild); all six fractured trackers healed in place by blessed touches; render-validity regression tests added.
### H-03 — Memory gauge silently drops the handoff-size estimate exactly when a gameplan completes

- **Severity**: low
- **Status**: resolved (2026-06-09)
- **Affected**: rituals/status_bundle.compute (token estimate gated on a target phase); render_digest (omits the figure with no explanation)
- **Preconditions**: Active gameplan with all phases complete
- **Impact**: CHANGELOG 0.5.0 and the gameplan exit criteria promise 'Memory: N active lessons, M project (~K tok handoff)'. The token estimate is computed only when a current or next phase exists, so a completed gameplan's digest - the close-out moment when memory weight matters most - shows no size and nothing explains the absence. Observed on this repo's own digest today.
- **Root cause**: The estimate sizes the next phase handoff; a finished gameplan has no target phase, and the gauge is deliberately best-effort-silent
- **Reproduction**: `clauderize status` on this repo (all phases of 2026-06-09-context-economics complete): memory line reads 'Memory: 0 active lessons, 4 project.' with no token figure
- **Recommended fix**: Size a synthetic close-out bundle (project lessons + decisions still ride into the next gameplan), or render an explicit 'handoff size n/a - gameplan complete' so the absence is explained rather than silent
- **Regression tests**: None yet
- **Resolution**: 0.6.0 Phase 2: completed-gameplan digest renders '(handoff n/a: gameplan complete)' instead of silently dropping the size.
