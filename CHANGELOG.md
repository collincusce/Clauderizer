# Changelog

All notable changes to Clauderizer are documented here.

## [1.5.3] — 2026-07-02

Field patch — three gameplan-machinery bugs found while authoring a multi-gameplan portfolio through `clauderize ops` on a hand-written corpus.

- **No more double-dated ids (fix).** `cz_create_gameplan` prefixes names with today's date; a name that already starts with an ISO date ("2026-07-02-x") produced "2026-07-02-2026-07-02-x". A pre-dated name is now used as-is — which also lets you pin a date. Every id remains dated, standing loop gameplans included; undated ids aren't supported.
- **A typo can no longer mint a shadow gameplan (fix).** `cz_add_phase` with an unknown `gameplan_id` silently scaffolded a bare `GAMEPLAN.md` the portfolio then tracked. All gameplan-scoped writes (`cz_add_phase`, `cz_add_lesson`, `cz_add_open_item`, `cz_set_exit_criteria`, `cz_add_correction`, `cz_add_amendment`, `cz_transition_phase`) now hard-error on an unknown id and list the known gameplans; creation stays exclusively `cz_create_gameplan`'s job.
- **Decorated phase statuses parse; misses explain themselves (fix).** Hand-written tracker rows like "🟡 READY — kickoff" or "⬜ GATED (deps)" made phases invisible. Status words now match on word boundaries with synonyms (DONE/COMPLETED → complete, GATED/WAITING/PAUSED → blocked, PENDING/TODO → not started), tracker rows need only three columns (`| number | name | status |` — dates are written only when the row has those columns), and a failed transition now reports what the trackers actually contain plus the accepted vocabulary instead of a bare "not found".

## [1.5.2] — 2026-07-02

Field patch — four bugs from the first native-Windows (pipx) installation, all reported by an agent dogfooding a real project the same day.

- **Windows console crash (fix).** On cp1252 consoles, printing the CLI's ✓/✗/⚙/⚠ glyphs raised `UnicodeEncodeError` — including inside error handlers, so commands died mid-report. `clauderize` and `clauderizer-hook` now switch their output streams to degrade unencodable characters (`?`) instead of crashing; genuinely UTF-8 consoles are untouched, and the MCP server's protocol channel is deliberately left alone. `PYTHONIOENCODING=utf-8` is no longer needed.
- **Inline frontmatter lists (fix).** Hand-written `depends_on: []` (or `[a, b]`) parsed as a raw string, and consumers iterating it saw its *characters* — phantom dependencies named `[` and `]` in the graph. Inline flow lists now parse as real lists and round-trip.
- **Heading-title tolerance (fix).** Appending a decision into a hand-written document whose heading carried a suffix ("Decisions (newest first)") created a duplicate `## Decisions` section at end-of-file. Section lookup now matches exact titles first, then case-insensitive, then a title-prefix with a word boundary — so entries land inside the section you already have. (Ordering within the section still appends; a newest-first insertion preference is a possible future option, deliberately out of scope here.)
- **`--run-cmd` help (fix).** The text now says what it is: a launcher *prefix* for the engine's commands (like `uvx --from clauderizer`), not a path to a single binary.

## [1.5.1] — 2026-07-02

Docs patch — no behavior change. The README gains **"Speak the language — words that do things"**: the operative vocabulary (gameplan, phase, handoff, ritual, cascade, pre-flight, decision, invariant, lesson, approve, standing condition, onboard, upgrade, append-only, …) with what each word means here and what saying it makes happen. These words are handles bound to specific tools; speaking them steers an agent onto the rails. Cut as a release because PyPI bakes the README per version — this puts the vocabulary on the package page.

## [1.5.0] — 2026-07-01

Onboarding — a repo that already has real documentation now gets a path from "placeholder scaffolds next to my actual specs" to seeded memory. (Version lines, kept straight: this is **engine 1.5.0**, and it **carries procedure 1.6.0** — the methodology document's own, separate version.)

- **`cz_onboard`** — a read-only bundle: which Clauderizer docs are still scaffold placeholders (structure-based detection that survives template wording changes; the append-only logs are never targets), which existing files look like specs (README, root design/spec docs, `docs/*.md` the engine doesn't own — paths and sizes only, capped), and a prompt describing how to seed: rewrite the placeholder prose docs directly, record subsystems/features with `cz_upsert_entity`, record decisions and rules already in force with `cz_add_decision`/`cz_add_invariant` citing the source file. The engine detects and prompts; it never seeds anything itself.
- **`clauderizer-onboard` skill** — ships with the other skills at `init`; walks the agent through the read-and-seed flow with distill-don't-transcribe judgment notes.
- **Surfaced on both delivery paths** — `clauderize init` prints one advisory when unseeded docs and spec candidates coexist, and already-initialized repos learn about onboarding from `clauderize upgrade` (a new advisory proposal), per the modernization contract: mechanical things apply, memory things are proposed.

New tool: `cz_onboard` (surface 44 → 45).

## [1.4.1] — 2026-07-01

Wording patch — no behavior change. The engine's **package version** (1.4.x) and the **procedure version** it carries (1.5.x, the methodology document's own line) near-collided numerically in 1.4.0, and the modernization messages phrased the comparison as "corpus procedure 1.4.0 vs engine 1.5.0" — which reads like a version skew or a phantom 1.5.0 release. The status digest, `clauderize doctor`, the modernize report, and the tool description now say the engine **carries** a procedure version and spell out that it is a separate line from the package version. Caught by the project's own maintainer within the hour of 1.4.0 — exactly the confusion decision D4 predicted.

## [1.4.0] — 2026-07-01

General modernization — the release where **upgrading the engine delivers its improvements to your repo**, plus four additive memory/gameplan capabilities distilled from the heaviest multi-campaign deployment. Everything is opt-in by shape: a repo that uses none of it behaves exactly as 1.3.1 (procedure 1.4.0 → 1.5.0, MINOR).

- **`clauderize upgrade` — corpus modernization.** The config now carries the procedure version the repo was last brought up to (stamped by `init`). When a newer engine meets an older corpus, the status digest and `clauderize doctor` say so in one line, and `clauderize upgrade` closes the gap in two tiers: **mechanical updates apply for you** (the config stamp and migrations, missing per-kind gate example files, the engine-owned `GAMEPLAN-PROCEDURE.md` refresh — all visible in `git diff`), while **memory-shaped improvements are only proposed** (unwired QA gates, near-duplicate invariants that look scope-taggable, campaigns without deliverable entities, loops without standing conditions) — your decisions, invariants, and lessons are never auto-edited. This also makes 1.3.1's `preflight.<kind>.toml.example` real: the hint referenced an example file that nothing actually scaffolded; `upgrade` now writes it.
- **Scoped memory.** `cz_add_invariant` accepts a scope (project-wide, or one gameplan's — a campaign's brand rules stop leaking into every other gameplan's context) and an audience label; `cz_add_lesson` accepts an audience. Reads filter — `cz_analyze` and the handoff's governing-invariants list skip other gameplans' scoped rules, and `cz_next_phase_context(audience=...)` returns one working role's view — but the canonical files and the written handoff always carry everything. The write-time near-duplicate advisory now covers invariants too (same single tokenizer and threshold), and curation never proposes consolidating across scopes or audiences.
- **Approval criteria — sign-offs bound to content.** An exit criterion of the form `APPROVAL: <artifact-path> — <description>` plus the new `cz_approve_gate` records a human approval as the artifact's content hash. Every later read recomputes it: edit the artifact and the approval reads as stale — in check-off, phase completion, and pre-flight — until re-approved. A hand-ticked box never counts. Surfaced everywhere, enforced nowhere.
- **Deliverables for campaign-style gameplans.** A kind may define a deliverable lifecycle (the campaign kind ships `concept → spec-approved → produced → assembled → qa → shipped`); each deliverable — a film, a short, a deck, never an individual rendered file — is a tracked entity with a `gameplan` field. `cz_gameplans gameplan_id=...` renders the deliverables board; the digest adds at most a one-line rollup ("Deliverables: 3/6 shipped").
- **Standing conditions.** A loop or campaign gameplan may declare threshold probes in `.clauderizer/conditions.<gameplan-id>.toml` (exit 0 = met). They run only when status is explicitly asked for — never on a timer, never from the session-start hook — and a met condition surfaces one line: "iteration proposed". The engine proposes; you decide.
- **Cross-gameplan consumes, pinned.** The handoff's "Consumes" section now shows each consumed entity's version alongside its status, and the whole chain — declare, render, cross-axis change, pending cross-ref on the portfolio card — is covered by an end-to-end test.

New tools: `cz_approve_gate`, `cz_modernize` (surface 42 → 44). New CLI subcommand: `clauderize upgrade`.

## [1.3.1] — 2026-06-28

Integrity patch — coherence, test, and documentation hardening from a read-only audit at 1.3.0. No new features and no user-facing behavior regression; the tool surface stays 42.

- **One canonical tokenizer (fix).** The corpus-health redundancy metric (behind `cz_corpus_health` / `cz_curate` / `cz_lesson_health` / `cz_loop_step`) had its own divergent token splitter at threshold 0.6, while the write-time near-duplicate advisory used the canonical tokenizer at 0.40 — two different definitions of "near-duplicate lesson". They are now single-sourced: one tokenizer (`analyze._tokens`) and one threshold (0.40), shared with the abstract index and relevance ranking. A guard test prevents a third fork from reappearing. Advisory output only (INVARIANT-05); it now reports an honest count on a consistent basis rather than a divergent one.
- **Coherence fixes.** The `L-NN` lesson-line grammar is single-sourced (the handoff ranker and telemetry now parse through the one shared parser); `analyze.suggest_edges` gained a size guard so its O(n²) pair scan can't tax the hot prompt-submit hook on a large entity graph; `cz_get` documents that it never mutates canonical markdown (only the disposable cache).
- **No false-green campaign QA.** A campaign preflight gate that is declared but unwired now warns ("declared but did not run") and lowers the verdict to "pass with warnings" instead of silently reading green; an example `.clauderizer/preflight.campaign.toml.example` ships.
- **Test integrity.** Replaced tautological "is-it-read-only" assertions (which checked a registry flag, not behavior) with a behavioral gate that runs each read-only op and proves it mutates no tracked file; the MCP discoverability test now asserts the full tool surface; added tests for the SessionStart digest's advertised tool list and the per-kind preflight real-subprocess path; scrubbed a machine-specific path (and username) from a test.
- **Docs.** `ARCHITECTURE.md` and `VISION.md` now describe the 1.2.0 (concurrent, multi-axis gameplans) and 1.3.0 (abstract index) feature sets; `docs/subsystems/mcp-server.md` version refreshed.

## [1.3.0] — 2026-06-28

Fast retrieval — a deterministic **abstract index** over the memory corpus, so an agent reads exactly the entry it needs instead of loading whole files.

Memory is markdown and stays that way: this adds a disposable, rebuilt-from-markdown index that makes retrieval cheap without embeddings or any new runtime dependency (INVARIANT-01 — markdown is canonical; the index is a derived cache).

- **`cz_get(id)` — addressable single-entry fetch.** Resolve one decision (`D-NNN`), invariant (`INVARIANT-NN`), finding (`H-NN`), or lesson (`L-NN`) by id — its full body read from canonical markdown on demand — instead of loading a whole corpus file. Read-only.
- **Abstracts on `cz_analyze`.** Each ranked hit now carries a one-line `abstract` (a pointer, not the body), so the agent can often answer without a follow-up fetch. A pre-registered cost experiment on this repo's real corpus measured a **48.3% mean payload-token reduction** per lookup at equal answer accuracy — deterministic, no live LLM.
- **Write-time near-duplicate-lesson advisory.** `cz_add_lesson` surfaces existing project lessons the new one strongly overlaps (length-normalized Jaccard) and nudges consolidation instead of appending — advisory only, never blocks (INVARIANT-05); the corpus stays append-only (INVARIANT-03).
- **Upgrade path.** `clauderize init` and `clauderize reindex` build/refresh the gitignored abstract index idempotently; `clauderize doctor` detects a missing or schema-stale cache and advises `reindex` (read-only — the runtime self-heals on first use).

New tool: `cz_get` (surface 41 → 42).

## [1.2.0] — 2026-06-27

Concurrent multi-axis gameplans — run several long-lived gameplans in one repo at once.

A repo is no longer limited to a single active gameplan. You can drive a **code** gameplan
and a **marketing campaign** (or any number of axes) in parallel, each advanced in its own
sessions, without losing the others. Fully back-compatible: a single-gameplan repo behaves
exactly as before (proven by a byte-identical golden snapshot of the status digest).

- **Focus + portfolio.** One gameplan is the *focus* — the default target for status,
  do-phase, handoff, and preflight. Switch it with `cz_focus` / `clauderize focus <id>`; see
  every open gameplan with `cz_gameplans` / `clauderize gameplans`. The status digest grows a
  portfolio block automatically once a second gameplan is open. The set of open gameplans is
  derived from each gameplan's phase table, not stored; only the one focus pointer persists
  (the config migrates `[active_gameplan]` → `[focus]`, with read-fallback for old repos).
- **Kinds as data.** Every gameplan has a **kind** — `driven` (code), `loop` (maintenance),
  `campaign` (creative), or a custom kind in `.clauderizer/kinds/<name>.toml`. A kind sets the
  vocabulary, the first phase, and the preflight checks. The vocabulary is display-only: a
  campaign reads in *stages* and *assets* in digests and handoffs while the on-disk structure
  stays identical, so every parser and tool is unchanged.
- **Per-kind preflight.** A campaign's preflight runs its own QA gates (virality, brand-lint,
  duration, …) — generic shell commands wired in `.clauderizer/preflight.<kind>.toml` — instead
  of tests/build. Clauderizer ships the run-named-gates mechanism; you supply the checks. An
  unwired gate skips with a hint.
- **Cross-gameplan dependencies.** Declare that one axis consumes an artifact another produces
  with `cz_consumes`; changing that artifact then cascades **across** gameplans — the consuming
  axis gets a pending cross-ref its own cascade check catches. Memory scoping is explicit:
  project invariants/ADRs are shared, a gameplan's decisions/lessons are local, and consumed
  artifacts surface in the handoff's "Consumes" section.

New tools: `cz_focus`, `cz_gameplans`, `cz_consumes` (surface 38 → 41). New CLI verbs:
`clauderize focus`, `clauderize gameplans`. Procedure version 1.3.0 → 1.4.0. Also includes the
H-17 preflight fix (detect the project venv so the test command resolves under uvx/pipx).

## [1.1.1] — 2026-06-25

Documentation only — no change to engine behavior.

**A README section on updating.** The `uvx --refresh` update path — refresh the engine, then
re-run `init` to refresh the wiring — was documented only in UPGRADING.md; the README now
spells it out inline, so the most common question ("how do I get the latest version?") is
answered where people first look. PyPI bakes the README into each release, so this patch is
what carries the new section onto the project page.

## [1.1.0] — 2026-06-24

A new capability for the self-critique gate — and the first behavior feature since 1.0.0.

**`cz_critique` now checks for two self-judgment biases.** The self-critique gate already
graded a target against Coverage, Coherence, and Grounding. Because the thing being
critiqued is always your own work, it now also surfaces two failure modes a self-judge is
prone to (drawn from the CALM judge-bias study):

- **Self-enhancement** — an open item closed with a hollow note ("done", "looks good") that
  cites nothing concrete, or a "ready to ship / no gaps remain" claim made while real gaps
  are still open.
- **Authority** — a lesson whose evidence leans on an unverifiable citation (a paper, a URL,
  a bare "verified") instead of provenance that resolves in the repo (a commit, a path, a
  test count).

Both are advisory, like the rest of the gate: the engine surfaces the candidates and you
decide. Each check is guarded so it stays quiet on sound work — a citation that also points
at a commit, or a terse note that cites a file, is not flagged. No new dependency; the checks
are plain deterministic text rules. Validated up front against a labeled fixture of 32
critiques with adversarial near-misses: the new checks catch every planted bias the old
rubric scored clean, with no false flags on the sound ones.

## [1.0.5] — 2026-06-23

Documentation readability and a hardening completion. No change to tool behavior.

**Cleaner docs and tool descriptions.** The human-facing docs (TRUST, TROUBLESHOOTING, the gameplan
procedure) and the `cz_*` tool descriptions carried internal cross-reference codes — decision,
finding, and lesson IDs — that meant nothing to a reader; leftover working-memory shorthand. They
are rewritten in plain prose with no loss of meaning; code references, format examples, and the
ID-scheme definitions stay. A stale "hardening findings H-01..H-09 resolved" line that would have
become wrong if updated is now stated as the tracker's standing discipline rather than a drifting
count.

**Harden — no engine write follows a symlink (H-13).** A pre-planted symlink in a hostile cloned
working tree could have redirected an engine-owned write (`.mcp.json`, a per-host config like
`.cursor/mcp.json`, the `.claude/settings.json` hooks, the hook wrapper, `.gitignore`, or a tracked
doc) to a path outside the repo. Every engine write now refuses a symlinked target instead of
following it — the link is never followed or deleted; you review and remove it. (The deeper
symlinked-parent-directory case is tracked as H-16 for a future containment pass.)

**Cleaner `release-check` and CLI output.** The release-check verdicts and CLI messages no longer
print internal finding codes in their explanations.

## [1.0.4] — 2026-06-23

Follow-up polish from the stranger-readiness dogfood — the rough edges left after 1.0.3's
critical fixes. Nothing breaking; everything additive.

**Discover the CLI's operations.** `clauderize ops --list` now prints every operation — what
it does, whether it writes, and its required arguments — and `clauderize ops --schema <op>`
shows one operation's full arguments. Previously you had to know the operation names by heart,
and the error for an unknown one pointed at a dead reference. The list is read from the same
registry the MCP tools use, so the command line and the agent tools can't drift apart.

**`uvx clauderizer …` works now.** The package is named `clauderizer` but the command was only
`clauderize`, so the obvious first thing a newcomer typed failed. There is now a `clauderizer`
command alias too; `clauderize` remains the canonical name.

**Clearer cascade resolution.** When you resolve a cascade, the result now says exactly what is
left to close it — a verdict for each dependent, plus a one-line summary of the edits — instead
of silently staying "pending". And a manual cascade for a change that a status transition
already cascaded no longer writes a duplicate review report; it reuses the open one.

**Preflight tells you when its test gate is asleep.** If a project was set up before it had any
code, its language profile is "generic" and the test/build checks quietly skip. Preflight now
notices when the project looks like a real language (say a `pyproject.toml` has since appeared)
and points you at re-detecting it, instead of staying a silent no-op.

**Retire an entity without deleting it.** Transition a subsystem or feature to `retired` (or
`obsolete`) with `cz_transition_status`: it stays in the graph for history but drops out of
active relevance surfacing — the supported alternative to hand-deleting a tracked file.

**Smaller fixes.** The MCP server reports Clauderizer's own version in its handshake (not the
underlying SDK's); amendment fields passed as lists render as a readable list instead of a raw
`['…']`; and a stale "cascade pending" note no longer lingers on amendments.

## [1.0.3] — 2026-06-23

**Fix — zero-install MCP server (H-14).** `clauderize init` wired the MCP server as
`uvx -q --from clauderizer clauderizer-mcp`, but `mcp` is an optional extra, so the
zero-install (uvx/pipx) path never installed it: the server printed the missing-package
notice and refused to serve, leaving a fresh Claude Code session with the SessionStart hook
but **no `cz_*` MCP tools**. The uvx fallback now requests the extra for the server command
only (`--from clauderizer[mcp]`); the hook and CLI stay extra-free. Surfaced by a
pet/standard/saas stranger-readiness dogfood — invisible in dev setups that already have
`mcp` installed.

**Fix — `doctor` no longer false-greens a broken MCP wiring (H-15).** The "MCP server
launchable" verdict probes `--version`, which answers without importing the `mcp` SDK, so it
stayed green even when the wired command could never serve. `clauderize doctor` now also
statically flags a `--from clauderizer` MCP wiring missing the `[mcp]` extra.

## [1.0.2] — 2026-06-22

**License.** Relicensed from **MIT** to the **Apache License 2.0** — the same permissive terms,
plus an explicit patent grant and a trademark clause. Replaces `LICENSE` with the full Apache 2.0
text, adds a `NOTICE`, and updates the `pyproject` license field + OSI classifier and the README.
No code changes; copyright remains "Clauderizer contributors".

## [1.0.1] — 2026-06-22

**Docs.** Corrects the README's maturity section, which still read "beta, with receipts" after
the 1.0 flip — now "1.0, stable" against the G1–G7 gates; drops a stale "Pre-1.0" line in
SECURITY.md. PyPI renders the long-description per version, so the README fix ships as a patch.
No engine changes.

## [1.0.0] — 2026-06-22

**1.0 — stable.** Promotes `1.0.0rc1` to the first stable release; no engine changes from the
rc. All 1.0 readiness gates (G1–G7, `docs/RELEASING.md`) hold — G6's cold-start was re-validated
fresh on the reference host: in a new session both the SessionStart hook **and** the MCP
transport fired cold, `cz_discover_skills` ran end-to-end, and the live `cz_status` matched the
injected digest. Classifier flips `4 - Beta → 5 - Production/Stable`. Ships with a human-first
README (hero, animated demo, before/after, how-it-works).

## [1.0.0rc1] — 2026-06-22

**First 1.0 release candidate.** Exercises the G1–G7 readiness gates
(`docs/RELEASING.md`) in the wild before the final 1.0.0; the classifier stays
`Development Status :: 4 - Beta` until 1.0.0 closes the G6 cold-start residual.
Suite 573 → 601.

**Project skill-awareness.** A project now tracks the Agent Skills available in its
environment as first-class, surfaced memory, mirroring the lesson lifecycle. Read-only
discovery proposes, the agent confirms, and the skills relevant to a phase ride into its
handoff focused by relevance. Propose-confirm, never auto-mutation (INVARIANT-05); the
auto-PR idea (open a PR when a public skill is found) was explicitly dropped (D3).

### Added
- **`docs/SKILLS.md`** — a compact, append-only project skill inventory (lazy-created from
  template, like LESSONS.md). `markdown/skill_state.py` is the one grammar (states
  active | obsolete | superseded).
- **`cz_register_skill`** / **`cz_obsolete_skill`** — register a skill (`S-NN`, idempotent on
  name) / mark one obsolete in place (append-only).
- **`cz_discover_skills`** — read-only: scans the local skill directories, parses each
  `SKILL.md`'s name + description, and proposes the unregistered ones (like `cz_curate`).
- **Relevance surfacing** — the handoff carries a "Skills for This Phase" block ranked by
  the existing lexical analyzer (top-k, or nothing when none overlap — focused, not a dump);
  the status gauge reports an active-skill count.

Tool surface 35 → 38. Also corrects the README MCP-surface list, which had drifted to 31
(missing the 0.17.0 read-only loop ops).

## [0.17.0] — 2026-06-21

**The empirical self-improvement loop.** Adds the telemetry substrate + curator that let
Clauderizer's memory improve itself under its own constitution — autonomous in cadence,
supervised in mutation (propose-confirm, never auto-mutation; INVARIANT-05). Deterministic,
stdlib-only, no ML (D-018). Suite 548 → 573.

### Added
- **Memory telemetry** (`.clauderizer/telemetry.jsonl`, append-only): which lessons/invariants
  a handoff surfaced (`cz_write_handoff`) and each phase's outcome + exit-criteria checked/total
  (`cz_transition_phase`). Never written from a hook (INVARIANT-06).
- **`cz_corpus_health`** — active-lesson count, lexical-redundancy estimate, never-surfaced
  count, pass-rate (read-only).
- **`cz_lesson_health`** — per-lesson utility (recent-success fraction), failure-risk, recency,
  and an advisory signal (read-only).
- **`cz_curate`** — proposes consolidate/obsolete/flag/promote with evidence + the blessed cz_*
  op to apply each (propose-only, like `cz_mine_failures`).
- **`cz_loop_step`** — one loop-gameplan iteration: convergence metric + proposals + a
  `converged` flag + a spawn-driven-gameplan escape hatch.
- **Loop gameplans** (`cz_create_gameplan(kind="loop")`) — a first-class standing, iterative
  maintenance type; `GAMEPLAN-PROCEDURE.md` → v1.3.0.
- **Empirical-gated promotion** (recurrence + correlation) + **typed edge suggestions**
  (redundant/related) + a **preemptive-risk cascade** for shaky upstream entities.

Tool surface 31 → 35. All new analysis ops are read-only and advisory (INVARIANT-05).

## [0.16.0] — 2026-06-21

**Universal host support — the cross-host & cross-model substrate.** Generalizes Clauderizer
beyond Claude Code + kimi to ~11 agentic coding hosts via the AGENTS.md + MCP substrate,
without regressing Claude Code parity (INVARIANT-07). Design + verified capability matrix in
`docs/CROSS-HOST.md`. Still `Development Status :: 4 - Beta`. Suite 446 → 548.

### Added
- **Host-target axis & injection ladder.** New `host_target` config axis (D-028) and the
  injection-parity ladder (Tier-1 hook → Tier-3 MCP prompt → Tier-4 AGENTS.md floor; Tier-2
  retired, D-034). In-memory at-most-once delivery signal (INVARIANT-08) + write-first
  self-correction; `session.best_tier()`.
- **Host-neutral floor.** The shared stanza no longer assumes a SessionStart hook; it tells
  hook-less hosts to call `cz_status` first (P2).
- **MCP prompts.** `cz-status` / `cz-next-phase` surface as slash commands on prompt-capable
  hosts (Cursor, Copilot, Continue, Gemini, Zed).
- **Per-host wiring emitters** (`hosttargets.py`): non-destructive, portable (uvx) MCP
  registration for Cursor/Copilot/Continue/Zed/Gemini/Cline/Amp; native-instructions floor
  for Continue & Gemini; hook setup guides for hook-capable hosts; guide-only for TOML/global
  (Codex/Windsurf/kimi). Wiring-contract verification + path-safety audit (D-032).
- **Server-side session bootstrap** (P7): the MCP server attaches a compact status note to
  the first non-status tool result on a hook-less host, in a separate `clauderizer_status`
  field (never corrupting the tool's own result, D-027), deduped via the P1 signal.
- **`clauderize init --host <name>` + `--list-hosts`** (P8): finally wires the emitters
  through the user-facing command — sets `host_target`, branches init (claude-code
  byte-identical per INVARIANT-07; other hosts get their MCP config + AGENTS.md floor +
  hook/MCP setup guides), cheap auto-detection, a friendly error listing valid hosts.
  `clauderize uninstall` now reverses the **full footprint** (MCP keys + hooks + marker
  stanzas + skills + `.clauderizer/`), `--host` scopes to one; `docs/` always preserved.
- **doctor is host-aware** — verifies the CONFIGURED host's wiring, not just Claude Code, and
  names the right repair (`init --host <name>`) when `host_target` was stripped.

### Hardened (P9–P13)
- The dogfood `.mcp.json`/`.claude/settings.json` and any machine-specific committable wiring
  are gitignored, not leaked (O-06, H-11); cross-host hook event names (windsurf
  `pre_user_prompt`, amp `agent.start`, …) routed correctly; a corrupt `config.toml` degrades
  to a clean `ConfigError` instead of crashing the CLI; an op↔engine signature guard (O-08);
  uninstall is symlink-safe (H-12). Independent seam + security reviews.
- **Config round-trip preserves unmodeled fields.** `Config.load`/`to_toml` capture and
  re-emit any keys/sections the engine doesn't model, so a config rewrite (init, the
  active-gameplan flip, or an older engine) never silently drops a field — closing the
  `host_target`-strip class found in real-host testing.

### Verified
- **Wiring contract** (every auto-write host's emitted config is well-formed, path-safe, and
  launches `clauderizer-mcp`) — in CI for all auto-write hosts.
- **Real-host consumption** — confirmed on **2 real hosts**: Cursor (Remote-WSL; the prompts
  surface as slash commands) and VS Code / Copilot, both reading the clauderize-emitted config.
- **Cross-model** — Cursor's Composer 2.5 Fast (a non-Claude model) drove a full gameplan
  end-to-end; adherence findings recorded — it leaned on the `clauderize ops` CLI fallback
  (validating L-05) and also hand-edited tracked docs, which drove the doctor + config
  preservation fixes above. Per-host consumption beyond these two remains a manual spot-check.
- Dropped from scope: Roo Code (repo archived 2026-05-15), Aider (no native MCP client yet).

## [0.15.0] — 2026-06-21

**Empirical memory gains (Beta 2).** A gain-gated initiative: every feature was proven
against a deterministic + agent-eval harness or parked. Test suite 400 → 446; no
breaking changes; still `Development Status :: 4 - Beta`.

### Added
- **Focused handoff lessons.** The cumulative handoff now carries the top-k project
  lessons most relevant to the phase (ranked, front-loaded) plus a pointer to the
  canonical full set in `docs/LESSONS.md`, instead of dumping all of them. Measured:
  handoff **−55% tokens at equal agent-eval accuracy** (focused 5/6 = full 5/6),
  ranker recall@5 = 100%. Relevance-focus + pointer-to-canonical, never truncation.
- **DAG integrity validation** (`graph/validate.py`) — deterministic dangling-edge +
  cycle (iterative Tarjan SCC) detection over the project DAG, surfaced advisorily via
  the status drift channel. Closes a gap where `pin_violations` skipped unknown targets,
  so dangling `depends_on` edges went silently undetected. 100% detection, 0 false
  positives on the fixture battery.
- **Edge-suggester.** `cz_analyze` now surfaces plausibly-*missing* `depends_on` edges
  from distinctive-token overlap (the structural complement of the D-018 existing-edge
  walk), agent-confirmed, with a markdown-canonical rejected-pair memory
  (`not_related_to` frontmatter). Precision 0.75 on a labeled fixture; advisory only.
- **Decision supersession lifecycle.** `cz_add_decision(supersedes=…)` now writes a
  bidirectional **Superseded by** back-ref, a **Status** field
  (active/superseded/deprecated), and dates; `analyze` demotes superseded decisions
  below their replacement via a secondary sort key (lexical score untouched). Stale-fact
  contradiction rate **1.0 → 0.0**. Append-only (annotated, never deleted).
- **Focused governing-invariant surfacing.** The handoff now surfaces the top-k
  phase-relevant invariants (the must-hold rules), focused — never an always-all dump.
- **Memory-eval harness** (`tests/benchmarks/`) — deterministic metrics (recall@k,
  nDCG, MRR, contradiction, abstention, token estimate, DAG validity) plus a
  focused-vs-full agent-eval; the gain-gate the above were measured against.

### Changed
- **`docs/LESSONS.md` re-distilled.** Nine overlapping project lessons consolidated into
  four syntheses (`L-22`–`L-25`), gated on a coverage proof (every original concept
  still retrievable in the ranker top-k): **21 → 16 active**, rollup −20%, append-only
  (sources marked obsolete, never deleted).

## [0.14.2] — 2026-06-20

**Windows lock robustness (H-10).** `locking._release_file` now retries the unlink
before falling back to stale takeover, so a finished writer can't orphan its own
lock when Windows raises a sharing violation while another process is mid-read of
the lock file. Previously the orphaned lock left a second writer waiting up to
~30s for stale takeover and surfacing a spurious (retryable) `LockHeld`. POSIX is
unaffected (unlink succeeds on open files). This fixes the flaky
`test_concurrent_writer_processes_lose_nothing` on Windows CI cells at the source;
a deterministic regression test (`test_release_retries_unlink_past_transient_oserror`)
pins the retry. No API or behavior change on the happy path.

## [0.14.1] — 2026-06-20

**Documentation accuracy pass.** No behavior change — the engine is identical to
0.14.0 apart from one docstring. This release ships the corrected README (the PyPI
long-description) and a repo-wide docs overhaul.

### Fixed (drift)
- **README MCP surface** now lists all **31 tools** (was 24): the discipline-gate
  and analysis tools added in 0.11.0–0.13.0 (`cz_add_open_item` /
  `cz_resolve_open_item`, `cz_set_exit_criteria` / `cz_check_exit_criterion`,
  `cz_analyze`, `cz_critique`, `cz_mine_failures`) were missing. `standard`
  pre-flight corrected to **8 checks** (`handoff_presence`); `release-check` added
  to the CLI reference.
- **The 0.14.0 lifecycle additions** (the `UserPromptSubmit` hook, the `AGENTS.md`
  stanza, `.clauderizer/kimi-setup.md`) are now reflected in the stranger docs —
  `docs/TRUST.md` (what init writes / what executes), `SECURITY.md`, and, most
  consequentially, `docs/UPGRADING.md`, whose uninstall script now removes the
  `UserPromptSubmit` hook and the `AGENTS.md` stanza instead of leaving them behind.
- `docs/ARCHITECTURE.md` gate provenance (adds D-018); the `preflight.py` docstring
  no longer hardcodes "7-check".

### Added (docs)
- **All seven `docs/subsystems/*.md`** bodies written (graph, markdown-core,
  mcp-server, mutations, profiles, rituals, scaffold) — previously stubs that
  `ARCHITECTURE.md` delegates prose to — plus `docs/VISION.md`,
  `docs/features/init-cli.md`, and a real `docs/TESTING.md` (baseline 403 tests).
- **L-21** (project lesson): reference docs drift together on a hook-taxonomy or
  tool-surface change — sweep the README MCP surface and TRUST/UPGRADING/SECURITY
  together; append-only history records the old counts on purpose.

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
