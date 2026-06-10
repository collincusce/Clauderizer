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

### H-04 — Repaired wiring was host-scoped: Windows-host session cold-started with no digest and no cz_* tools while doctor reported 13/13 green

- **Severity**: high
- **Status**: resolved (2026-06-09)
- **Affected**: .mcp.json; .claude/settings.json; scaffold init --run-cmd composition; doctor launchability checks (host-blind)
- **Invariant violated**: L-02 one layer up again: capability was verified, but in the wrong environment - a runnability check is only as good as the host it spawns from
- **Preconditions**: Session host (Windows Claude Code over \\wsl.localhost) differs from engine host (WSL venv); wiring written as WSL-native absolute paths
- **Impact**: On the Windows host (this machine's primary session entry point, repo opened via \\wsl.localhost UNC), the SessionStart hook and MCP server commands were WSL-native venv paths Windows cannot exec: no [Clauderizer] digest, no cz_* tools, no in-session breadcrumb - H-01's exact impact, reintroduced one layer up by the H-01 fix itself. Meanwhile clauderize doctor, running inside WSL, certified the same wiring runnable (13/13 green), so the health check actively misled for the host that consumes sessions.
- **Root cause**: init writes one wiring for one host and has no host-of-record concept. A composition bug compounds it: init --run-cmd 'wsl.exe -d ubuntu <venv>/bin/clauderize' appends the console-script name as a CLI argument, producing 'clauderize clauderizer-mcp' / 'clauderize clauderizer-hook' - invalid subcommands argparse rejects (exit 2) - so init cannot express split-host wiring at all
- **Reproduction**: From Windows: open a session on the UNC repo with WSL-native wiring -> no digest, no tools, doctor (in WSL) all green. Composition bug: clauderize init --run-cmd 'wsl.exe -d ubuntu /home/ccusce/Clauderizer/.venv/bin/clauderize', then echo '{}' | wsl.exe -d ubuntu /home/ccusce/Clauderizer/.venv/bin/clauderize clauderizer-hook -> exit 2 invalid choice
- **Recommended fix**: init: accept a session-host-of-record (e.g. --session-host windows-wsl) and compose wsl.exe-shimmed console-script wiring (command/args split for .mcp.json, single command string for the hook); doctor: spawn the wiring's exact commands from the recorded session host, or at minimum flag a host mismatch instead of certifying from the wrong side; until then the two wiring files are hand-maintained
- **Regression tests**: None yet - candidate: init round-trip test asserting that for any --run-cmd form, the composed wiring argv is accepted by the binary it names (spawn with --help)
- **Resolution**: Closed by agent-autonomy Phase 2 (D3): config records a session host of record ([host] session_host, native | windows-wsl:<distro>); init composes the wsl.exe shim from it (command/args split for .mcp.json, one command string for the hook) and spawn-tests every composed command with --version before writing, refusing on failure (WiringRefused; src/clauderizer/hosts.py); doctor verifies launchability FOR the recorded host via a real wsl.exe interop round-trip or honestly reports 'unverifiable from this host' (exit 3, never a false green). Evidence: clauderize init on this repo regenerated the hand-maintained wiring byte-identically (.mcp.json and settings.json 'kept', config gained the session_host line) and doctor through the PowerShell shim certified 14/14 with 'verified end-to-end via wsl.exe round-trip (clauderizer 0.6.0)'. Regression: tests/test_hosts.py (composition matrix, the exact 'clauderize clauderizer-mcp' exit-2 shape refusing init with nothing written, doctor 3-state messaging). Residual boundary (documented): a mid-session wiring repair still needs a session restart to attach MCP tools - harness enumerates servers at session start.

### H-05 — No write lock on tracked docs: concurrent sessions on one repo can silently lose updates or duplicate IDs

- **Severity**: medium
- **Status**: resolved (2026-06-09)
- **Affected**: mutations.py (all 18 public write functions); .clauderizer index cache; any multi-window or multi-agent workflow on one repo
- **Invariant violated**: Append-only trackers assume appends are serialized; numbering assumes allocation+write is atomic
- **Preconditions**: Two writer processes (MCP servers, future CLI ops, or shims) mutating the same repo concurrently; sub-second collision window per write
- **Impact**: Every mutation is read-modify-write on markdown with no inter-process lock (verified: no flock/lockfile/mutex anywhere in src/clauderizer; the only 'lock' is profile.lock.toml, a pin file). Two sessions - or one session plus a subagent - mutating the same repo in the same window can last-writer-wins erase each other's appends, and two concurrent ID allocations (H-NN, L-NN, D-k, A-NNN) can both compute the same next number. Cross-project concurrency is unaffected: state is per-repo by construction (server per session, repo = spawn cwd).
- **Root cause**: The engine assumes one interactive session per repo, but stdio MCP spawns one server process per session - the assumption breaks the moment a second window or subagent opens the same project
- **Reproduction**: Open two sessions on one repo and fire cz_add_lesson in both within the same second; inspect numbering and the lessons section for a lost append or duplicate number
- **Recommended fix**: Advisory lock in the single mutation path (D-007 makes it one choke point): e.g. .clauderizer/write.lock created O_EXCL with a stale-lock timeout, held per mutation. Covers MCP, CLI ops, and shims uniformly; read tools stay lock-free (L-03). Until then: one writer session per repo at a time; reads are always safe; git history is the recovery backstop. Candidate task for the agent-autonomy gameplan Phase 0 alongside clauderize ops
- **Regression tests**: None yet - candidate: N concurrent add_lesson processes against one repo yield N distinct sequential numbers and N surviving entries
- **Resolution**: Closed by agent-autonomy Phase 0: advisory write lock at the mutation choke point (src/clauderizer/locking.py; all 18 public mutations.* functions serialize on .clauderizer/write.lock, reentrant, stale takeover ~30s). Regression evidence: tests/test_locking.py::test_concurrent_writer_processes_lose_nothing (8 concurrent writer processes -> 8 distinct sequential ids, 8 surviving appends) and test_crashed_holder_blocks_at_most_stale_timeout. This resolution was itself written through the locked path.
