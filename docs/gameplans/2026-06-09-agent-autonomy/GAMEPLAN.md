# agent-autonomy Gameplan

> Created: 2026-06-09
> Status: Complete
> Procedure: docs/gameplans/GAMEPLAN-PROCEDURE.md

## Project Overview

Make the agent fully self-sufficient against the failure modes the last two live
tests exposed: tracked writes that require an MCP client (L-05), wiring that is
only valid for the host that did *not* spawn it (H-04), races between concurrent
writer sessions (H-05), hooks that die without a trace (H-01 residue), and guards
that have never been seen to fire (D9 vs stale uvx). The through-line: **the
recording machinery must work — and fail — out loud, from any host, under any
concurrency, with or without MCP.**

Every phase closes a named finding or open thread from the 0.6.0 post-mortem and
its same-day addendum: H-05 (Phase 0), CLI write parity / L-05 (Phase 1), H-04
residuals (Phase 2), H-01 residue (Phase 3), stale-uvx proof + the
cz_add_amendment pointer + the 0.7.0 release (Phase 4).

## Subsystems Touched

- `subsys.mutations` — write-lock acquisition in the single mutation path (D1)
- `subsys.scaffold` — `clauderize ops` in cli.py (D2), session-host-of-record init
  + doctor checks (D3), hook wrapper templates (D4), amendment pointer fix
- `subsys.mcp-server` — dispatch moves onto the shared ops registry (D2); tool
  count unchanged
- `subsys.rituals` — amendment rendering; thread-hygiene touches
- `subsys.profiles` — config schema gains the session-host field (D3)

## Source-of-Truth Captures

Captured 2026-06-09 (second session, all values observed live):

- **Engine 0.6.0 everywhere**: source, editable venv, and PyPI (releases: 0.2.0,
  0.2.1, 0.3.0, 0.5.0, 0.6.0 — the v0.6.0 tag push already published; the
  "publish 0.6.0" thread is half-done, only the proof half remains)
- **Baseline**: 139 tests (cz_preflight, real run); 24 MCP tools; 13 doctor
  checks; CLI surface = `init/status/reindex/doctor/mcp` (read-only beyond init)
- **Mutation surface**: 18 public functions in `src/clauderizer/mutations.py`
  (the parity and lock targets)
- **Locking today**: none — the only "lock" in source is `profile.lock.toml`, a
  pin file (H-05's repro basis)
- **H-04 repro**: `clauderize init --run-cmd 'wsl.exe -d ubuntu <venv>/bin/clauderize'`
  composes `clauderize clauderizer-mcp` → argparse exit 2. Current working wiring
  is hand-maintained: `.mcp.json` command `wsl.exe`, args
  `["-d","ubuntu","/home/ccusce/Clauderizer/.venv/bin/clauderizer-mcp"]`; hook =
  the same as one command string ending `clauderizer-hook`; distro `ubuntu`
- **Harness behavior**: MCP servers enumerate once at session start — a
  mid-session .mcp.json repair does not attach (verified via ToolSearch re-check);
  restart is the last mile of any wiring fix
- **Amendment pointer**: `rituals.amendments = false` here; A-001 in the 0.6.0
  gameplan cites `_cascade-reports/2026-06-09-A-001.md`, which does not exist
- **Windows-host ergonomics**: PS 5.1 mangles nested quotes and injects a BOM in
  native→native pipes — drive everything via script files + JSON args files (the
  `/tmp/mcp_probe.py` stdio-probe pattern from the addendum)
- **uv/uvx**: uvx 0.11.19 installed in WSL via the official installer
  (`~/.local/bin`, on login-shell PATH; non-login invocations need the absolute
  path). `uvx --from clauderizer clauderize --version` → **0.6.0 from PyPI** —
  Phase 4's by-name half pre-verified, uv cache warmed

## Amendments

_(None yet. Append A-NNN entries here once Phase 0 starts.)_

## Decisions

### D1 — Tracked writes serialize through one advisory file lock at the mutation choke point

**Context**: H-05: every mutation is read-modify-write markdown with no inter-process lock; one MCP server per session means a second window or subagent races appends and ID allocation. D-007 already funnels every write (MCP, shim, future CLI) through one mutation path.
**Decision**: Acquire .clauderizer/write.lock (O_EXCL create; holder pid+timestamp inside; stale takeover after a timeout) around each mutation in that single path; read tools stay lock-free (L-03). Contention surfaces as a clear, retryable error naming the holder.
**Consequences**: N concurrent writers yield N sequential IDs and N surviving appends; CLI ops and MCP writers can coexist safely; a crashed holder delays writers at most the stale timeout; no daemon and no platform-specific fcntl dependence.

### D2 — CLI parity ships as one batch entry point (clauderize ops), not per-mutation subcommands

**Context**: L-05 demands a CLI-reachable fallback for every tracked write. Two sessions of shim experience (JSON ops files + args files) proved the batch shape under the worst conditions - PS 5.1 quote mangling, BOM-injecting pipes - while 18 separate argparse surfaces would drift from the tool schemas.
**Decision**: clauderize ops <file.json|-> executes [{op, args}, ...] against the same registry the MCP server dispatches; per-op JSON results on stdout; op names and arg shapes are exactly the tool names and schemas (one source of truth). Read ops are included.
**Consequences**: Parity is testable by enumeration (tools_list vs ops registry); the shim pattern retires; quoting hazards are bypassed by design (args live in files); every future tool gets CLI parity for free.

### D3 — Wiring carries a session-host-of-record; init composes for it and spawn-tests what it writes

**Context**: H-04: wiring valid inside WSL was dead on the Windows session host while doctor stayed 13/13 green, and init mis-composed a shimmed run-cmd into an invalid subcommand (clauderize clauderizer-mcp, exit 2). The consuming host was recorded nowhere, so no check could speak for it.
**Decision**: Config gains a session host-of-record (e.g. native | windows-wsl:<distro>); init composes host-appropriate wiring (.mcp.json command/args split, hook as one command string, console-script targets) and refuses to write any command whose spawn probe fails; doctor verifies launchability for the recorded session host or reports 'unverifiable from this host' instead of green.
**Consequences**: The hand-maintained wiring becomes regenerable; a green doctor regains meaning across host boundaries; L-02 extends to 'verify from the host of record'; supported session hosts become an explicit, testable matrix.

### D4 — The registered hook is a host-native wrapper that cannot fail silently

**Context**: H-01 residue, twice-bitten: a hook whose command cannot spawn prints nothing, indistinguishable from an un-clauderized repo. The engine cannot breadcrumb a process that never starts, so the breadcrumb must live one layer below the engine.
**Decision**: init writes a thin host-native wrapper (.clauderizer/hook.cmd / hook.sh per session host) and registers the wrapper as the SessionStart command; the wrapper invokes the engine hook and on any failure prints '[Clauderizer] engine unreachable: <error> - run clauderize doctor' into the session context.
**Consequences**: Silent death shrinks to 'the wrapper itself cannot spawn' (missing shell or wsl.exe - a documented boundary); every other failure becomes a visible, actionable breadcrumb; wrapper templates are tested per supported host.

### D5 — Stale-engine detection is proven by a failing demonstration, not assumed from code review

**Context**: 0.6.0 reached PyPI via the v0.6.0 tag push, so the 'publish 0.6.0' open thread is half-stale; D9's identity checks exist but have never been shown to fire on the stale-uvx topology they were built for.
**Decision**: Close the thread only with recorded evidence: a scratch repo wired uvx --from clauderizer==0.5.0 must make doctor fail its identity check loudly through that exact wiring, and uvx-by-name must resolve 0.6.0; the demonstration lands in HARDENING as regression evidence.
**Consequences**: The remaining work is precisely scoped (proof, not release); 'doctor catches it' becomes a tested claim instead of an intention; the pattern - prove the guard fires before closing its thread - carries to future guards.

## Open Items

- **O1 — `ACTIVE_LESSONS_WARN` as config**: the memory-gauge warn threshold is
  a constant; make it configurable. Carried from the 0.5.0/0.6.0 post-mortems
  (restated here 2026-06-09 by Phase 4 thread hygiene; not in any phase's
  scope — candidate for the next gameplan).
- **O2 — Project-lesson consolidation past ~20 entries**: docs/LESSONS.md has
  no consolidation pressure yet (currently 6 entries; the per-gameplan
  consolidate/promote flow exists, the cross-gameplan one does not). Carried
  from the 0.6.0 post-mortem (restated 2026-06-09 by Phase 4; revisit when
  the count approaches ~20).
- **O3 — Mechanize the release preflight (H-07's missing half)**: releasing is
  the one ritual the engine doesn't own — phase work gets cz_preflight
  re-observing reality at execution time, while the release steps live as
  README prose and a day-old Source-of-Truth capture. H-07 happened in that
  gap: a version was staged from a snapshot while a remote tag + Release
  already claimed it. Wanted: a `clauderize release-check` (or doctor
  extension) that, given the staged version, live-sweeps all four registries
  (local tags, `git ls-remote --tags`, GitHub Releases API, PyPI JSON — never
  uv's cache) plus origin/main sync state, and refuses on any existing claim.
  The publish.yml gate covers the CI leg; this covers the staging leg.
  (Added 2026-06-10 from the H-07 retrospective.)
- **O4 — 1.0 readiness gates (captured 2026-06-10, pre-0.8.0-tag)**: 1.0 is a
  stability promise, not a quality grade. Gates before declaring it:
  (a) the headline path — SessionStart digest in a real harness cold start —
  verified on current wiring (open: restart_validation_observation) and across
  the supported host matrix (windows-wsl + native); (b) two consecutive boring
  releases through the gated pipeline (0.8.0, then 0.9.x) with zero manual
  repair; (c) failure-discovery rate decays (H-04..H-07 arrived in ~48h of
  live use — 1.0 wants a quiet stretch, ideally on a second real project);
  (d) stability contracts written: MCP tool/op schema policy, config +
  procedure migration policy, release ritual mechanized (O3); (e) no dead
  flags: rituals.amendments gets its cascade machinery or is descoped; O1/O2
  closed or explicitly post-1.0; (f) classifier flips Alpha → Beta with a
  README that claims only verified behavior.

## Phase Breakdown

### Phase 0: Serialized tracked writes

**Goal**: Two concurrent writer processes on one repo can no longer lose appends
or double-allocate IDs: one advisory lock at the mutation choke point (D1), held
per mutation, surfaced clearly on contention — closes H-05.
**Depends on**: nothing (first phase).

| Task | Description | Effort |
|------|-------------|--------|
| 0.1 | `locking.py`: acquire/release `.clauderizer/write.lock` via O_EXCL with holder metadata (pid, host, timestamp) and stale takeover after a timeout (default ~30s); a clear retryable LockHeld error naming the holder | 1.5h |
| 0.2 | Acquire the lock inside the single mutation path so every mutations.* caller (MCP, shim, future ops CLI) serializes; read paths untouched (L-03); lock always released on exception | 1h |
| 0.3 | Tests: N concurrent *processes* each add_lesson on one repo → N distinct sequential numbers and N surviving entries; stale-lock takeover; LockHeld error shape; release-on-exception | 2h |
| 0.4 | Dogfood: resolve H-05 through the locked path itself, citing the contention test as evidence | 0.5h |

**Exit criteria**:
- [ ] Contention regression green: concurrent writer processes never lose an append or duplicate an ID
- [ ] A crashed holder blocks a later writer no longer than the stale timeout
- [ ] Full suite passes, baseline grows from 139; H-05 → resolved with evidence

### Phase 1: CLI write parity: clauderize ops

**Goal**: Every tracked write reachable without an MCP client: `clauderize ops <file|->` executes a batch of {op, args} against the same mutation/ritual surface the cz_* tools wrap, returning per-op JSON results - closes L-05 structurally and retires the shim pattern.
**Depends on**: 0.

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Ops registry: one name → (callable, schema) table shared by the MCP server's dispatch and the CLI, op names exactly the tool names | 1.5h |
| 1.2 | `clauderize ops <file.json\|->`: execute `[{op, args}, ...]`; per-op JSON results (ok, result/error) on stdout; non-zero exit if any op failed; writes acquire the Phase 0 lock | 2h |
| 1.3 | Parity test: every tools_list entry resolves in the ops registry with an identical schema; representative read + write ops return MCP-identical results | 1.5h |
| 1.4 | Docs: CLAUDE.md stanza + procedure name `clauderize ops` as the no-MCP fallback; shim guidance retired | 0.5h |
| 1.5 | Dogfood: with the MCP server never spawned, record a real lesson/output on this repo via ops alone | 0.5h |

**Exit criteria**:
- [ ] Enumeration parity green: 24/24 tool ops reachable via `ops` with identical schemas
- [ ] A tracked write recorded end-to-end on this repo in an MCP-less invocation
- [ ] Full suite passes; stanza names the fallback

### Phase 2: Wiring truth: session-host-of-record

**Goal**: Wiring is composed for, and verified from, the host that actually spawns sessions: config records the session host, init composes wsl.exe-shimmed console-script wiring for split-host setups and spawn-tests every command it writes, and doctor verifies host-aware or says 'unverifiable from this host' - closes H-04's residuals.
**Depends on**: Phase 1.

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | Config/profile: `[host] session_host` (e.g. `native`, `windows-wsl:ubuntu`) — detection heuristic plus an explicit init flag | 1.5h |
| 2.2 | init: host-aware wiring composition — wsl.exe shim with command/args split for .mcp.json, one command string for the hook, console-script targets; still correct for `native` | 2h |
| 2.3 | init: spawn-test every composed command (--help probe) before writing; refuse with loud guidance on failure (the H-04 regression) | 1h |
| 2.4 | doctor: launchability checks become host-of-record-aware — verify for the recorded session host, or report 'unverifiable from this host'; never a false green | 1.5h |
| 2.5 | Tests: composition matrix (native, windows-wsl) round-trips; no multi-word run-cmd can yield an invalid subcommand; doctor host messaging | 1.5h |

**Exit criteria**:
- [ ] `clauderize init` on this repo regenerates the currently hand-maintained wiring (equivalent or better) with zero manual edits — diff-verified
- [ ] doctor invoked from PowerShell through the shim certifies the wiring for THIS session host; H-04 → resolved
- [ ] Full suite passes

### Phase 3: Cold-start breadcrumb hook wrapper

**Goal**: A session whose engine cannot launch still learns why: init registers a thin host-native wrapper as the SessionStart command; the wrapper always spawns and on engine failure prints an engine-unreachable breadcrumb naming `clauderize doctor` - closes H-01's residue.
**Depends on**: 2.

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Wrapper templates per session host: `.clauderizer/hook.cmd` (Windows) / `hook.sh` (POSIX); wrapper invokes the engine hook and on any failure prints `[Clauderizer] engine unreachable: <error> — run clauderize doctor` | 2h |
| 3.2 | init registers the wrapper as the SessionStart command; doctor checks wrapper presence and freshness against the engine path | 1h |
| 3.3 | Tests: wrappers execute on their host shells; the failure path emits the breadcrumb verbatim; engine-path changes regenerate wrappers | 1.5h |
| 3.4 | Live demo: a scratch clone with the engine binary renamed cold-starts to the breadcrumb instead of silence; restore afterward | 0.5h |

**Exit criteria**:
- [ ] A cold session with a dead engine receives the breadcrumb in-session — demonstrated and recorded as H-01's closure evidence
- [ ] The remaining silent boundary (wrapper shell / wsl.exe itself missing) documented explicitly
- [ ] Full suite passes

### Phase 4: Stale-engine proof, amendment pointer, 0.7.0

**Goal**: Prove doctor's identity checks fire on a stale uvx wiring (pinned scratch repo, recorded evidence); make cz_add_amendment's cascade-report pointer conditional and heal A-001's dangling pointer; update stale open threads; release 0.7.0.
**Depends on**: 0, 1, 2, 3.

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Stale-uvx demo (D5): scratch repo wired `uvx --from clauderizer==0.5.0`; doctor through that exact wiring must FAIL identity loudly; capture output in HARDENING; verify uvx-by-name resolves 0.6.0 | 1.5h |
| 4.2 | cz_add_amendment: render the `Cascade report:` line only when rituals.amendments is enabled (or create the file); regression test; correct A-001's dangling pointer in the 0.6.0 gameplan | 1.5h |
| 4.3 | Thread hygiene: 0.6.0 post-mortem open threads updated with evidence (publish done, parity done, breadcrumb done); carry-forwards restated (ACTIVE_LESSONS_WARN, project-lesson consolidation past ~20) | 0.5h |
| 4.4 | Release 0.7.0: version bump, CHANGELOG, README (ops, host-of-record, wrapper), re-init installed assets, close out per Ending Protocol; tag only after a restart-validated cold start | 1.5h |

**Exit criteria**:
- [ ] Doctor demonstrably fails on the pinned-stale wiring (output captured); uvx-by-name resolves 0.6.0
- [ ] Amendment pointer conditional and tested; A-001's pointer no longer dangles
- [ ] `clauderize --version` → 0.7.0; CHANGELOG written; doctor all green; gameplan closed per Ending Protocol
