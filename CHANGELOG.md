# Changelog

All notable changes to Clauderizer are documented here.

## [0.14.0] — 2026-06-19

**kimi-code lifecycle integration** (gameplan 2026-06-19-kimi-lifecycle-integration):
Clauderizer's durable memory now surfaces at more lifecycle points than cold start,
and `init` can target AGENTS.md-aware hosts (kimi-code, Codex) — adapting the hook
taxonomy that kimi-code and Claude Code share. Everything new is read-only and
exits 0 (INVARIANT-06), with no enable/disable flag (INVARIANT-05); the core stays
stdlib-only.

### Added — an event-dispatching hook (D-025)

- **`clauderizer-hook` now dispatches on `hook_event_name` (read from stdin)** to
  read-only handlers, falling back to the SessionStart digest on empty/garbage/non-
  object stdin — the exact shape the hardened no-arg digest probe sends, so the
  H-08/H-09 legs are untouched. `--version`/`--help` still answer the identity probe
  before any stdin or repo read. New handlers:
  - **UserPromptSubmit** runs the analyze gate (D-016/D-018) against the prompt and
    surfaces the most relevant recorded decisions/invariants + one-hop graph gaps —
    a pointer into canonical memory (D-013), silent when nothing is relevant.
  - **PreCompact** reminds the agent to record anything discovered-but-unsaved before
    context is summarized; **PostCompact** re-injects the digest so the workflow
    survives compaction (the kimi path — Claude Code instead re-fires SessionStart
    with `source=compact`, D1).
  - **SessionStart** is now source-aware (frames a post-compaction / post-clear
    re-entry). `sessionstart.py` became a back-compat shim; the entry point now
    targets `clauderizer.hook.dispatch:main`.

### Added — Claude Code wiring of the new events

- **`clauderize init` registers `UserPromptSubmit`** alongside `SessionStart` (same
  wrapper command), idempotently, preserving foreign hooks per event and migrating
  the pre-0.14 SessionStart-only shape. PreCompact/PostCompact are deliberately not
  registered on Claude Code — it drops their stdout (D1).

### Added — AGENTS.md stanza + a non-destructive kimi host target (D2)

- **`init` injects the same Clauderizer stanza into `AGENTS.md`** (one source, so it
  cannot drift from `CLAUDE.md`), so kimi-code (`KIMI_AGENTS_MD`) and other
  AGENTS.md-aware harnesses get the memory pointer. Clauderizer's skills already work
  in kimi-code, which reads `.claude/skills/`.
- **`init` emits `.clauderizer/kimi-setup.md`** — a non-destructive guide with
  `[[hooks]]` entries for all four events (kimi-code injects every hook's stdout) and
  MCP-registration guidance. It never edits the global `~/.kimi/config.toml`.
  `subsys.scaffold` 0.6.0 → 0.7.0.

### Notes

- New project decision **D-025** and **INVARIANT-06** (every hook handler is read-only
  and exits 0, generalizing INVARIANT-04 to all events). kimi-code's MCP-server TOML
  schema is undocumented upstream (tracked as gameplan open item O-01), so the kimi
  MCP step is guided rather than auto-wired.

## [0.13.0] — 2026-06-19

**Headroom-borrowed ideas** (gameplan 2026-06-19-headroom-borrowed-ideas): three
ideas adapted from the Headroom project (chopratejas/headroom) were each tested
as a falsifiable hypothesis with a machine-checkable keep/discard metric — two
kept, two discarded. The core stays stdlib-only, deterministic, no ML (D-014/D-018).

### Added — relevance-ranked lesson pointers in the handoff (idea #2a, D-021)

- **The handoff now surfaces a "Most Relevant Lessons for This Phase" block** —
  the top-k lessons ranked by the existing keyword + entity-id ranker
  (`analyze.rank_relevant`, no ML) against the current phase's breakdown, placed
  ABOVE the unchanged cumulative list and only when active lessons exceed k (=5).
  It reorders nothing and drops nothing — a pointer into canonical memory (D-013),
  so every lesson still propagates (D-009 + the incomplete-propagation
  anti-pattern). `subsys.rituals` 0.6.0 → 0.7.0.

### Added — `cz_mine_failures`, a failure-miner (idea #3, D-023)

- **`cz_mine_failures`** scans Claude Code session transcripts (JSONL) for
  failure→fix patterns — a tool error then a same-tool success, a pytest
  fail→pass, or a short explicit user correction — and PROPOSES draft
  `cz_add_correction` / `cz_add_lesson` entries for the agent to confirm.
  Read-only, deterministic, stdlib-only; invoked, never auto-firing, no
  enable/disable flag (D-015/INVARIANT-05). `is_error` is unreliable for shell
  failures, so errors are detected by content signatures; benign search-tool
  errors and tool-protocol hiccups are denied to protect precision (~80% on a
  labeled sample of real transcripts). `subsys.mcp-server` 0.4.1 → 0.5.0.

### Evaluated and discarded (with evidence)

- **Prefix-stabilizing the SessionStart digest** (idea #1, à la Headroom
  CacheAligner) — DISCARD (D-020). The reorder lifts the stable-prefix proxy
  65→786 chars, but the digest is only ~888 chars (~222 tok), is rendered once per
  session, and stable-first ordering buries the actionable state — a negligible,
  unobservable gain for a real readability cost.
- **Truncating the cumulative lessons tail** (idea #2b) — DISCARD (D-022).
  Reintroduces incomplete-propagation for marginal savings; `cz_consolidate_lessons`
  is the safe size lever.

### Hardened (post-close verification)

- A second, independent adversarial pass on the miner fixed three crash vectors
  reachable via `cz_mine_failures` on real transcripts — non-UTF-8 bytes
  (`UnicodeDecodeError`), an unhashable `tool_use_id`, and a non-str `text` block
  (`TypeError`) — by extending tolerance past JSON validity to *shape* validity
  (`open(..., errors="replace")`, `isinstance` guards, a per-file net in
  `mine_dir`). Also one precision fix: `[1-9]\d* failed` (not `\d+`), so a clean
  "0 failed" run is no longer mined as a failure — 3 fewer false positives on the
  real corpus (C-01, C-02).
- **New `handoff_presence` preflight check** — `cz_preflight` now blocks when the
  phase table implies a handoff should exist (phase 0, or any phase whose
  predecessor is COMPLETE) but the file is absent on disk — so a gameplan can no
  longer close with dangling handoff links undetected. The failure message spells
  out the recovery: reply `regenerate` to rebuild each from the graph via
  `cz_write_handoff` (lossless — a handoff is derived state), or waive once.
  Configurable: list it in `preflight_advisory` to downgrade to a warning for
  intentionally single-session gameplans. Suite → 352 passed, 4 skipped.

## [0.12.0] — 2026-06-18

**STORM-inspired curation** (D-017): methods from Stanford OVAL's STORM/Co-STORM,
imported as deterministic engine-surfacing + skill guidance — never as runtime
dependencies (the core stays stdlib-only; the agent reasons, the engine surfaces).

### Added — the analyze-gate gap-finder (D-018)

- **`cz_analyze` now surfaces an `adjacent` set** — Co-STORM's "moderator" move.
  After ranking the most-relevant decisions/invariants (contradiction-judgment),
  it walks the project graph ONE hop from what the text touches — entities named
  in the text, plus entities `introduced_by` a surfaced decision (the only
  structural link from a flat-doc ADR into the graph) — and surfaces the
  neighbors nothing has connected to the text yet: gaps, not contradictions.
  Structural, not semantic — no embeddings, no new dependency (the complement to
  D-013's optional semantic recall); empty when nothing in the graph relates (an
  honest negative). Reaches the agent through both the MCP tool and
  `clauderize ops`; the prompt now invites gap-judgment alongside
  contradiction/supersession-judgment.

### Added — provenance on lessons and decisions (STORM citations)

- **`cz_add_lesson` and `cz_add_decision` accept an optional `evidence`** citing
  the concrete provenance behind the entry (commit, `file:line`, phase,
  benchmark, doc). Lessons render it inline as `*(evidence: …)*` — placed so the
  lesson-state grammar never misreads it — so it rides into every handoff rollup;
  decisions render an **Evidence** field. Additive and backward-compatible
  (omitted ⇒ byte-identical output to today); the MCP tool schema auto-derives
  the new param from the function signature.

### Added — the self-critique gate (D-019)

- **`cz_critique`** — a reference-free, advisory rubric over a target (a phase,
  the gameplan, or a handoff). It composes the deterministic signals the engine
  already computes into three dimensions — **Coverage** (unresolved open items,
  unchecked exit criteria, incomplete phases), **Coherence** (graph drift, pending
  cascades), **Grounding** (lessons lacking provenance) — and surfaces them with a
  grading prompt for the agent. STORM grades drafts with a reference-free
  LLM-judge rubric; adapted to the surface-don't-decide law, the engine assembles
  the gaps and the agent grades — it never scores or blocks (INVARIANT-05). Stdlib
  only, no embeddings; reachable via MCP and `clauderize ops`.

### Changed — perspective-guided planning (skill)

- **The `clauderizer-new-gameplan` skill** now interrogates a goal from multiple
  named perspectives (security, performance, ops/release, testing, cost,
  failure-modes, prerequisite-chains) before phases are drafted — STORM's
  perspective-guided question asking — run as a cheap fan-out (a faster model per
  lens, the strong model for synthesis), with findings routed into decisions,
  phases, and tracked open items, and the goal vetted via `cz_analyze`'s
  gap-finder. It now also derives lenses from related graph entities
  (`cz_graph_query`), not only the fixed list; and the close-gameplan
  (post-mortem) and do-phase (handoff) skills gained an outline-before-synthesize
  step for long-form writing.

Suite 289 → 304. Still deferred, each tracked as an open item: the Co-STORM
hierarchical lesson "mind map" (changes the lesson data model), the
consecutive-same-intent staleness counter (noise risk), and the mind-map's
deterministic graph cleanup (singleton-collapse may be unsafe on a retention
graph) — see the `storm-self-critique-gate` gameplan (O-01/O-02).

## [0.11.0] — 2026-06-18

Three spec-kit-inspired **discipline gates** — clarify, exit-criteria, analyze —
land as five new tools (24 → 29), all advisory, judgment-based, and config-free.
Borrowed from GitHub's spec-kit and adapted to Clauderizer's grain (the engine
surfaces, the agent rules — never a hard block).

### Added — discipline gates (D-015 / D-016 / INVARIANT-05)

Three gates that surface findings in the tool result for the agent to rule on —
they never hard-block a mutation/phase transition and add no config flags. The
model is `cz_cascade`'s: the engine finds and reports; it does not decide.

- **Clarify gate** — `cz_add_open_item` / `cz_resolve_open_item`: auto-numbered
  `O-NN` open items in a gameplan's "Open Items"; `cz_status` reports the
  unresolved ones, and `cz_transition_phase`→complete surfaces those relevant to
  the phase (tagged to it, or untagged).
- **Exit-criteria gate** — `cz_set_exit_criteria` / `cz_check_exit_criterion`:
  a phase's `- [ ]` exit criteria become machine-checkable; completing a phase
  surfaces the unchecked ones, with test-ish criteria auto-linked to the measured
  baseline test count (scaffold placeholders are ignored).
- **Analyze gate** — `cz_analyze` surfaces the existing decisions/invariants most
  relevant (lexical: keyword + entity-id overlap — no new dependency) to a piece of
  text, for the agent to judge contradiction/supersession; `cz_add_decision` now
  enriches its result with related/possibly-superseded entries.
- Tool surface **24 → 29**; every gate tool is reachable via both MCP and
  `clauderize ops` (registry parity enforced). Suite 270 → 289.

## [0.10.0] — 2026-06-10

**Beta.** `Development Status :: 4 - Beta` — the flip itself is beta gate B6
(D-012), shipped via the release ritual with B1–B5 already satisfied by dated
artifacts (`docs/RELEASING.md` carries the evidence table). This release
bundles the **alpha-to-beta-evidence**, **stranger-readiness**, and
**beta-flip burn-down** work: the suite runs — and passes — on machines and
repos that are not the author's; a stranger can adopt, upgrade, trust, debug,
and remove Clauderizer from the published docs alone; and the codebase now
carries structural guards for the failure classes that earned the gates.
Suite 255 → 270.

### Added (beta-flip burn-down)
- **The bare-IO tripwire** (`tests/test_io_discipline.py`): no text-mode
  `read_text`/`write_text`/`open` without `encoding=` anywhere in src or
  tests — it caught three stragglers on its first sweep. Same class:
  subprocess output decoding pinned to utf-8 in preflight's runner and
  release-check's git wrapper (win32 locale decode could mojibake or raise).
- **Engine-staleness nudge**: `cz_status` from a long-lived MCP server now
  warns when the engine source on disk is newer than the running process —
  "restart the session, or use `clauderize ops` (fresh process) for writes."
- **release-check: "README names the ritual"** — a README whose release
  section never mentions `clauderize release-check` fails staging (the
  G7-drift-between-sibling-docs tripwire).

### Fixed (stranger-readiness)
- **The quickstart command** — `uvx clauderize init` resolved no such
  package (uvx derives the package from the command name); every occurrence
  is now `uvx --from clauderizer clauderize init`, and the README carries a
  zero-install note for bare `clauderize` commands.
- **init no longer wires uvx ephemeral-cache paths.** Run via `uvx`, init
  used to register console scripts from uv's cache — `uv cache clean` then
  killed the MCP registration and every digest until a re-init. Resolution
  now refuses cache-resident paths (`_under_uv_cache`) and wires the durable
  absolutized `uvx -q --from clauderizer …` form, which survives cache
  cleans by re-resolving on demand. The `-q` matters on its own: cold-cache
  uv progress noise used to ride the hook wrapper's stderr-rerouting into
  session context — in front of the `--version` identity line probes parse.

### Added (stranger-readiness)
- **The stranger docs**, all executable rather than aspirational:
  `docs/UPGRADING.md` (upgrades are two moves; the five-step uninstall keeps
  `docs/` — walked live, both doctor nudges verified verbatim),
  `docs/TRUST.md` (what init writes, what executes when, the cloned-repo
  scenario, supply chain — every claim cites grep-verified code),
  `SECURITY.md`, and `docs/TROUBLESHOOTING.md` (the "no digest" ladder, the
  breadcrumb decoder, doctor's exit contract — every quoted string verified
  against src).
- **`quickstart.yml`** — the README's exact install path executed against
  the PUBLISHED package on a clean runner, every push plus weekly, with a
  doc-drift grep and a self-arming cache-clean assertion.
- **README repositioned**: "Git-native working memory for coding agents",
  the adoption wedge, a "Maturity: alpha, with receipts" section linking the
  public beta gates, absolute doc links, and a maintainers' release section
  that now follows the ritual it used to contradict.

---

Earlier in the same arc (**alpha-to-beta-evidence**, B1–B4):

### Fixed
- **win32, found by executing the platform instead of monkeypatching it**:
  `init` resolves win32 console scripts (`clauderizer-*.exe`) beside the
  interpreter; the generated wrappers are written with **byte-exact
  newlines** (text-mode IO corrupted `hook.cmd` to `\r\r\n` and broke init
  idempotency on win32; `hook.sh` written from a win32 host now stays `\n` —
  the distro's sh chokes on `\r`); doctor's wrapper-freshness compare reads
  bytes (universal-newline normalization made a healthy win32 wrapper read
  permanently stale); doctor resolves distro-spelled wrapper registrations
  (`/home/…` or `/C:/…`) to the repo-local file instead of failing the
  presence check.
- **Unborn-branch diagnosis** (found by the node-profile live loop): a fresh
  `git init` with zero commits — the first state a brand-new adopter runs
  preflight in — no longer reads as "not a git repo"; branch checks now
  discriminate via `rev-parse --is-inside-work-tree` and report an honest
  "no commits yet (unborn branch)" skip.

### Added
- **CI proves the OS matrix (B2)**: tests run on ubuntu, macos, AND windows
  runners × py3.11–3.13, with the native win32 cmd wrapper EXECUTED on real
  Windows (live tests: digest passthrough, dead-engine breadcrumb,
  unreachable-repo breadcrumb, hostile-cwd `cd /d` anchor).
- **`.gitattributes` (`eol=lf`)** — newlines are content (L-01); autocrlf
  runners no longer rewrite fixtures.
- **Beta gates B1–B6** in `docs/RELEASING.md` (D-012) with a dated evidence
  table; B1–B4 satisfied.

### Infrastructure
- Both workflows bumped off deprecated Node-20 actions (checkout@v5,
  setup-uv@v6, upload/download-artifact@v5).

## [0.9.0] — 2026-06-10

The **harness-truth-and-release-ritual** work: every claim the system makes
about its own wiring is now backed by a leg something actually traversed, and
the release ritual is a checked command instead of a remembered procedure.
Closes H-08 and H-09 — the findings tracker is all-resolved through H-09.
Suite 215 → 255.

### Fixed
- **H-08 — the SessionStart digest survives the Windows harness.** The
  registered command uses //-led paths (shape C, D2): `wsl.exe -d <distro>
  //bin/sh //<repo>/.clauderizer/hook.sh`. Git Bash's MSYS2 conversion skips
  //-led arguments as UNC-form, Linux collapses // to /, and the shape carries
  zero quote surface so cmd.exe and PowerShell pass it verbatim (evidence
  artifact: `scripts/wiring_matrix.ps1`, hostile-cwd by default; shape A
  `sh -c 'exec …'` is the documented fallback). Restart-validated in-band:
  the first real cold start after the rewire delivered the digest (transcript
  `hook_success` attachment — shape C verbatim, exit 0, 388ms).
- **H-09 — the digest no longer depends on the executor's working directory.**
  The generated wrapper anchors itself (`cd '<repo>'`) before delegating and
  reports an unreachable repo as a stdout breadcrumb instead of silence
  (cmd.exe structurally cannot hold a UNC cwd; any harness may spawn hooks
  from a fixed directory).

### Added
- **Doctor traverses the consumer leg (D-010).** For windows-wsl hosts the
  SessionStart verdict now spawns the registered command STRING through the
  harness's executor (Git Bash, when reachable) from a non-repo cwd, with
  paired probes — `--version` for engine identity (it answers before repo
  discovery, so it is anchor-blind) plus the no-arg digest for the H-09
  anchor — and names the traversed leg in its claim. Executor unreachable →
  honest "unverifiable" (exit 3), never green. The old direct-argv probe
  stayed green through the entire H-08 outage; a live regression test pins
  that exact false green.
- **`clauderize release-check` (O3/D-011)** — push-then-release ordering
  (origin/<branch> == HEAD via ls-remote) and the four version registries
  (local tags, remote tags, GitHub Releases, PyPI queried directly — never
  uvx cache) checked as a command (exit 0/2/3), plus the publish.yml
  tag==source gate marker. Every skew shape that double-claimed 0.7.0/0.8.0
  is individually proven to fire in tests.
- **`docs/RELEASING.md`** — the mechanical release ritual (release-check exit
  0 as the hard precondition) and the seven 1.0 readiness gates (G1–G7).
- **`[memory]` config (O1/O2)** — `active_lessons_warn` (default 12) and
  `project_lessons_warn` (default 20): the memory-bloat nudges move from
  hardcoded constants to config; the status digest's gauge reads them.
- **init's registered-hook spawn-test is the hostile-cwd digest probe** — an
  un-anchored wrapper can no longer register (it would be silent exactly the
  way the real executor chain made it).

## [0.8.0] — 2026-06-10

The **agent-autonomy** release: the recording machinery now works — and fails —
out loud, from any host, under any concurrency, with or without MCP. Every
change closes a named finding from the 0.6.0 live tests (H-05, L-05, H-04,
H-01 residue, the stale-uvx thread).

### Added
- **Advisory write lock** (`.clauderizer/write.lock`) — every tracked write
  serializes at the mutation choke point: O_EXCL acquire with holder metadata,
  stale takeover (~30s), clear retryable `LockHeld` error naming the holder.
  N concurrent writer *processes* now yield N sequential IDs and N surviving
  appends (closes H-05). Reads stay lock-free.
- **`clauderize ops <file.json|->`** — CLI write parity: a JSON batch of
  `[{op, args}, ...]` executes against the same registry the MCP server
  dispatches; op names and schemas are exactly the `cz_*` tool names. Every
  tracked write is now reachable without an MCP client (closes L-05); the
  ad-hoc shim patterns are retired.
- **Session host of record** — config records which host spawns sessions
  (`native` | `windows-wsl:<distro>`); init composes host-appropriate wiring
  (wsl.exe shim, command/args split) and **spawn-tests every command before
  writing** (refuses the H-04 `clauderize clauderizer-mcp` mis-composition
  with nothing written); doctor verifies launchability *for the recorded
  host* or honestly reports "unverifiable from this host" (exit 3 — never a
  false green). Closes H-04.
- **Cold-start breadcrumb wrapper** — init registers a thin always-spawns
  wrapper (`.clauderizer/hook.sh`, `hook.cmd` on native win32) as the
  SessionStart command; any engine failure becomes a stdout breadcrumb
  (`[Clauderizer] engine unreachable: … — run clauderize doctor`) instead of
  silence (closes H-01's residue). Doctor checks wrapper presence and
  freshness against the engine path.
- **Wiring identity verification (D5)** — doctor's round-trip launch checks
  now require the wiring to *identify its engine*: the probed `--version`
  output must claim the same version as the engine answering doctor.
  Catches pinned-stale wiring that launches fine (a `uvx --from
  clauderizer[mcp]==0.5.0` pin passes every exit-code probe — demonstrated
  live, recorded as H-06) and a dead engine behind the always-exit-0 hook
  wrapper (whose breadcrumb previously read as a green hook verdict).

### Fixed
- **`cz_add_amendment` dangling cascade pointer** — amendment entries cited
  `_cascade-reports/<date>-A-NNN.md`, a per-amendment filename no code path
  creates under any setting. The `Cascade report` line now renders only when
  the `amendments` ritual is enabled, and as an honest pending pointer
  (cascade reports are per-entity files). A-001 in the 0.6.0 gameplan healed
  to cite the per-entity report that actually holds its cascade evidence.
  Procedure 1.2.0 → 1.2.1 documents the conditional line.

### Infrastructure
- **publish.yml refuses tag/version skew (H-07)** — the release workflow now
  fails fast when the Release tag and the tagged tree's `pyproject.toml`
  version disagree, instead of building the wrong artifacts and dying as a
  PyPI duplicate that nothing on the Releases page surfaces.

### Known issues
- **H-08 (open)** — on Windows-harness hosts the SessionStart digest never
  reaches session context: the harness executes hook commands through Git
  Bash, whose MSYS2 path conversion rewrites the shim's `/bin/sh` argument
  to a nonexistent `C:/Program Files/Git/usr/bin/sh` (exit 127 below the
  wrapper, so no breadcrumb either). Engine, wrapper, and doctor are green
  when invoked directly; the wiring fix (an MSYS-conversion-immune command
  shape) is scheduled for the next gameplan. See `docs/HARDENING.md` H-08.

## [0.7.0] — 2026-06-09 *(version retired — never published)*

A v0.7.0 GitHub Release was cut from a commit whose source still declared
0.6.0; its PyPI publish failed as a duplicate, so no installable 0.7.0
exists anywhere (H-07). The work intended for this number ships as 0.8.0;
the workflow gate above makes that failure shape impossible to repeat
silently.

## [0.6.0] — 2026-06-09

Closes the **engine-robustness cluster** from the two prior post-mortems plus
the cold-start findings H-01..H-03. The through-line is *structure over
substrings*: every defect came from the engine writing or reading markdown by
line/substring heuristics — tables appended as paragraphs, IDs counted in
prose, lesson state inferred from anywhere-in-line markers.

### Added
- **`cz_add_output`** — blessed write for the PHASE-STATUS **Outputs Registry**
  (per-phase fenced blocks; same-key upserts rewrite in place). The registry
  had sat at its scaffold placeholder through two closed gameplans for want of
  this write.
- **`cz_add_phase_summary`** — blessed write for the index's **Per-Phase
  Completion Summaries** (one block per phase; re-recording replaces it).
- **Tracker header write-backs** — `cz_transition_phase` / `cz_add_phase` now
  refresh `> Status:` / `> Last updated:` on both trackers and GAMEPLAN.md's
  `Status` (Planning → Executing → Complete) from the live phase table. Both
  closed gameplans had read "Phase 0 ready" since the day they finished.
- **`doctor` engine-identity checks** — installed dist-info must match the
  running source `__version__` (caught live: an editable install reporting
  0.3.0 under 0.5.0 source), and when the repo *is* the clauderizer source,
  the running engine must match the repo's pyproject version (stale uvx/pipx
  cache while dogfooding).
- **CLI fallback breadcrumb** — the CLAUDE.md stanza now says what to do when
  the `cz_*` tools are absent: `clauderize doctor` / `clauderize status`
  (a cold session previously couldn't tell broken wiring from no Clauderizer).

### Changed
- **Anchored ID numbering** — `next_numbered_id` counts only entry anchors
  (`### <ID> —` headings, `**<ID>.**` bold entries). Scaffold placeholder
  prose and cross-references no longer shift sequences (one gameplan's
  decisions had numbered D3..D9, skipping D6, because template prose and a
  citation of another gameplan's D6 were counted).
- **Structural table writes** — tracker phase rows go through a table-aware
  writer (`markdown/tables.py`) that rebuilds the block contiguously on every
  blessed touch; trackers fractured by the old paragraph-append healed in
  place, no migration script. Rendered markdown is valid for humans again,
  not just for the engine's own tolerant parser.
- **Collision-proof cascade reports** — filenames carry a zero-padded `-NN`
  sequence per date+entity (never timestamps), so same-day cascades of one
  entity coexist instead of silently overwriting; `pending_cascades` orders
  chronologically (legacy unsuffixed names rank as sequence 0).
- **Lesson state is a grammar, not a substring** — one parser
  (`markdown/lesson_state.py`) reads the trailing `(obsolete …)` /
  `(promoted …)` markers (or legacy `~~strikethrough~~`); the gauge, handoff
  roll-ups, and obsolete/promote/consolidate all share it. A lesson whose
  *text* mentions "(obsolete" counts as active everywhere.
- **Preflight runs profile commands in the engine's own environment** — the
  running interpreter's bin dir leads PATH, so a venv-installed engine finds
  its own pytest/ruff without shell activation (`pytest: not found` observed
  live on a venv-wired engine).
- A completed gameplan's digest says `(handoff n/a: gameplan complete)`
  instead of silently dropping the promised size estimate.

## [0.5.0] — 2026-06-09

Closes review finding 5 (**context economics**): cumulative memory grew
monotonically — handoffs carried every lesson forever, lessons died with their
gameplan at close, and nothing measured the bundle. Per ADR D-009 the answer is
consolidation *pressure*, never caps: three blessed writes plus visibility, with
the audit trail intact.

### Added
- **`cz_consolidate_lessons`** — synthesize N overlapping lessons into one; each
  source is marked `(obsolete: consolidated into #N)` and every future handoff
  carries one line instead of many. All sources validated before anything is
  written.
- **`cz_promote_lesson`** — promote an enduring lesson into a compact,
  on-demand `docs/LESSONS.md` as an `L-NN` entry with provenance; the source is
  marked `(promoted <date>: L-NN)` and stops rolling up individually. Handoffs
  gain a "Project Lessons (distilled)" section that rides **across gameplans** —
  lessons finally outlive the gameplan that learned them.
- **Memory gauge** — `cz_status` / the SessionStart digest report
  `Memory: N active lessons, M project (~K tok handoff)` and nudge toward
  consolidate/promote/obsolete past `ACTIVE_LESSONS_WARN` (12, a documented
  constant). Bloat is a visible state, not a silent failure mode.
- `cz_obsolete_lesson` accepts `L-NN` ids, so the project list is curated with
  the same rules (its `number` parameter is now a string).
- Close-gameplan skill: a lesson-curation step (consolidate, then promote
  deliberately — not in bulk); do-phase nudges consolidation when the list
  repeats itself.

## [0.4.0] — 2026-06-09

Closes the **discipline seams** from the 2026-06-09 external review: the places
where the workflow still depended on agents hand-editing tracked docs because
the blessed write was missing, destructive, or never ran.

### Added
- **`cz_resolve_cascade`** — record per-dependent verdicts + the Updates
  applied/deferred sections on a cascade report. Previously, clearing the
  `cascade_hygiene` preflight check *required* a forbidden hand-edit — the rules
  banned the only way to make progress. Defaults to the latest pending report;
  partial resolution keeps it pending (`status_bundle.pending_cascades` is now
  the public, shared predicate).
- **`cz_obsolete_lesson`** — mark an accumulated lesson `(obsolete <date>: <reason>)`
  through a tool. The line stays in the log (append-only memory); handoff roll-ups
  stop carrying it, so cumulative handoffs can shrink without a hand-edit.
- **Baseline write-back** — a green `cz_preflight` run that measures a test count
  now refreshes the active gameplan's "Current baseline test count" line
  (anti-pattern #7, stale references, applied to the system itself: this repo's
  own hook said "0 tests" while 84 passed).
- **Completed-gameplan status** — a gameplan whose phases are all complete now
  reports "all N phase(s) COMPLETE" with close-out guidance instead of the
  confusing "no in-progress or ready phase found".
- **`doctor`: lock-file check** — flags a `profile.lock.toml` that doesn't parse
  (whose overrides were being silently ignored).

### Changed
- **Marker-protected handoffs (D-008)** — `cz_write_handoff` owns only a
  `<!-- clauderizer:handoff -->` marker block; regeneration replaces the block and
  preserves everything outside it byte-for-byte. Fresh handoffs add an agent-owned
  "Phase Notes" scaffold; legacy generated skeletons are migrated wholesale;
  unrecognized files are preserved verbatim below the block. `cz_next_phase_context`
  returns the merged view, so a context fetch includes on-disk enrichment.
- Skills no longer instruct hand-edits anywhere: cascade/do-phase route through
  `cz_resolve_cascade`, record routes risks through `cz_add_finding`.

### Fixed
- **`Profile.to_lock_toml` emitted invalid TOML** for profiles whose baseline
  regex contains backslashes (e.g. python's `(\d+) passed`) — and since
  `load_for_repo` falls back silently on parse errors, every python-profile lock
  written by `init` was being ignored in its entirety. Lock values are now
  TOML-escaped, with a round-trip regression test across all packaged profiles.

## [0.3.0] — 2026-06-05

Fixes the **state-mutation surface** — the gaps a second dogfooding session found
where structured state drifted because the blessed write was missing or destructive.

### Added
- **`cz_transition_phase`** — phases finally get a lifecycle write
  (not_started/ready/in_progress/complete/blocked/failed, with aliases + auto-dated
  Started/Completed). Without it, `cz_status` froze at "Phase 0" on finished work
  because nothing could advance a phase. The single highest-leverage fix.
- **`cz_resolve_finding`** — update a finding's status + dated resolution note in
  `HARDENING.md`, satisfying its own "mark resolved, never delete" policy through a
  blessed path instead of a forbidden hand-edit.
- **Drift hint** — `cz_status` / the SessionStart digest now flag entities still
  `planned` while phases are complete ("⚠ Drift: … cz_transition_status to reconcile").
  Conservative: fires only when there's completed work *and* untouched entities.
- **`init --workflow {code,docs,audit}`** + `preflight_advisory` config — makes
  `clean_tree` (and, for audits, `tests`) advisory rather than fatal, so a
  deliverable-accumulating workflow stops failing preflight on every resume.

### Fixed
- `init` resolves the engine command from the **running interpreter's bin dir**
  (`sys.executable`) before falling back to PATH/uvx — reliable for venv/WSL even
  when the bin dir isn't on PATH.
- `init` **no longer clobbers `profile.lock.toml`** on re-run — per-project command
  overrides (read back by `detect.load_for_repo`) are preserved. Delete the lock to
  re-derive it.

## [0.2.1] — 2026-06-05

### Fixed
- Require **Python ≥ 3.11**. The engine uses the stdlib `tomllib`, which only
  exists from 3.11, so 0.2.0 crashed on import under 3.10 despite advertising
  `>=3.10`. Corrected `requires-python`, classifiers, and the CI matrix. (Keeps
  the zero-runtime-dependency promise rather than pulling in a `tomli` backport.)

## [0.2.0] — 2026-06-05

First release published to PyPI.

### Packaging
- Fixed the wheel build: removed a `force-include` table that collided with
  `packages`, which broke `uv build` / `python -m build`. The `templates/`,
  `profiles/`, and `skills/` data dirs are bundled via `packages` and verified
  present in the wheel.
- Core install is dependency-free; the MCP server is the `clauderizer[mcp]` extra.

### Added
- `cz_add_finding` / `mutations.add_finding` (alias `add_risk`) — record structured
  security/audit findings into the append-only `HARDENING.md` tracker.
- `doctor` now probes that the MCP server **and** SessionStart hook commands are
  actually executable, not just registered — a green check on a non-launchable
  setup is worse than no check.
- `detect.load_for_repo()` overlays a project-local `profile.lock.toml`, so
  per-project test/build/lint/typecheck overrides take effect (the lock was
  previously write-only).

### Changed
- `init` wiring now prefers installed console scripts (venv/pipx) and only falls
  back to `uvx`, fixing the Windows→WSL / venv drop-in path.
- Re-running `init` with a changed invocation now **replaces** the SessionStart
  hook instead of appending a duplicate.
- `cz_next_phase_context` is side-effect-free: it assembles the handoff in memory
  (`handoff.assemble(..., write=False)`) and returns it as `handoff_md`; only
  `cz_write_handoff` persists a file.
- The first real entry in a doc section now replaces the scaffold `_(…)_`
  placeholder instead of stacking beneath it.

### Fixed
- SessionStart hook errors print to stdout (visible in session context) instead
  of stderr, where silent failure was the dangerous kind.

## [0.1.0] — 2026-05-30

Initial release. A drop-in, MCP-native successor to the markdown "gameplan
system": same conceptual model (gameplan → phase → task, a long-lived Project
DAG, post-hoc cascade, cumulative handoffs, append-only memory), delivered as an
active system instead of a procedure followed by hand.

### Added

- **Markdown core** — zero-dependency frontmatter parser, section/marker editing,
  and a single idempotent mutation path (`markdown/writer.py`).
- **Project DAG** — graph index (cached to a disposable `index.json`), dependent/
  dependency queries, and semver pin-violation detection.
- **Cascade** — post-hoc forward walk that writes a judgment-based report
  (dependents marked "needs review"). Replaces the never-built `bin/cascade`.
- **Rituals as operations** — `preflight` (the 7 checks run for real against host
  profile commands), cumulative `handoff` assembly, and the `status` digest.
- **Structured mutations** — decisions, invariants, lessons, corrections,
  gameplans, phases, amendments, entities, and status transitions (auto-cascade).
- **MCP server** — 15 self-describing tools + resources over stdio (optional
  `mcp` extra).
- **Configurability** — `pet` / `standard` / `saas` size dial and host-language
  profiles (Node, Python, Go, Ruby, generic) as pure data.
- **Drop-in** — `clauderize init` (idempotent), `status`, `doctor`, `reindex`,
  `mcp`; a SessionStart hook for automatic cold-start; six Claude Code skills.
- Test suite: 57 tests covering markdown round-trips, the graph, cascade,
  rituals, mutations, init idempotency, profiles, and the live MCP tools.
