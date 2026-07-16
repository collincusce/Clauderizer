# Architecture

Subsystems, capabilities, and components. Tracked entities live in
`docs/subsystems/` and `docs/features/` with frontmatter that declares the
Project DAG; this doc is the prose overview.

## Subsystems

_(Describe each subsystem. Create tracked entity docs with `cz_upsert_entity`.)_

## Capabilities

### Discipline gates (D-015 / D-016 / D-018 / D-019)

Four always-on, advisory, judgment-based gates (no config flags; INVARIANT-05)
that surface findings in the tool result for the agent to rule on — modeled on
`cz_cascade` ("the engine finds and reports; it does not decide"):

- **Clarify** — structured open items (`O-NN`): `cz_add_open_item` /
  `cz_resolve_open_item`, surfaced by `cz_status` and at phase completion.
- **Exit criteria** — machine-checkable `- [ ]` criteria: `cz_set_exit_criteria`
  / `cz_check_exit_criterion`; unchecked ones surface when a phase completes,
  with test-ish criteria auto-linked to the baseline test count.
- **Analyze** — `cz_analyze` and the `cz_add_decision` enrichment surface the
  existing decisions/invariants most relevant (lexical overlap; `analyze.py`) to
  a new decision for contradiction/supersession judgment, **plus an `adjacent`
  set** (D-018): one-hop project-graph neighbors of what the text touches —
  entities named in the text, or `introduced_by` a surfaced decision — that
  nothing has connected to it yet. Structural adjacency, no embeddings; the
  gap-finder complement to contradiction-judgment.
- **Self-critique** — `cz_critique` (D-019): a reference-free rubric over a
  target (a phase, the gameplan, or a handoff) across **Coverage / Coherence /
  Grounding**, composed from the signals above plus lessons-without-provenance,
  for the agent to grade. STORM's reference-free LLM-judge rubric, adapted to
  surface-don't-decide.

Clarify, exit-criteria, and analyze surface through the shared
`result["advisories"]` shape on `cz_transition_phase` plus their dedicated tools;
`cz_critique` is run on demand. None ever blocks a write.

### Provenance / citations (D-017)

`cz_add_lesson` and `cz_add_decision` accept an optional `evidence` that cites
where the entry came from (commit, `file:line`, phase, benchmark, doc). Lessons
carry it inline (`*(evidence: …)*`) so it survives every handoff rollup;
decisions render an **Evidence** field. Additive and backward-compatible.

### Memory quality — the gain-gate features (0.15.0)

The *empirical-memory-gains* initiative landed five features only after each proved
a measured gain against a deterministic + agent-eval harness (`tests/benchmarks/`,
the gain-gate — D-026); two further candidates (bitemporal valid-time, an
always-injected steering doc) were honestly parked/dropped when they could not beat
a simpler baseline. All of the below surface advisorily — none blocks a write
(INVARIANT-05):

- **Focused injected memory** — the cumulative handoff carries the top-k project
  lessons (and top-k phase-relevant **invariants**) ranked to the phase plus a
  pointer to canonical `docs/LESSONS.md` / `docs/INVARIANTS.md`, instead of dumping
  all. Relevance-focus + pointer-to-canonical, never truncation (reconciles D-022);
  measured −55% handoff tokens at equal agent-eval accuracy.
- **DAG integrity validation** (`graph/validate.py`) — deterministic dangling-edge +
  cycle (iterative Tarjan SCC) detection over the Project DAG, surfaced through the
  status drift channel. Fills a gap `query.pin_violations` left open (it skips edges
  whose target is unknown, so dangling `depends_on` edges went silently undetected).
- **Edge-suggester** (`analyze.suggest_edges`) — surfaces plausibly-*missing*
  `depends_on` edges from distinctive-token overlap (the structural complement of the
  D-018 existing-edge walk), agent-confirmed, with a `not_related_to` rejected-pair
  memory. Precision-gated so it never adds noise.
- **Decision supersession lifecycle** — `cz_add_decision(supersedes=…)` writes a
  bidirectional **Superseded by** back-ref, a **Status** (active/superseded/
  deprecated), and dates; `analyze` then demotes a superseded decision below its
  replacement via a stable secondary sort key (the lexical score is untouched).
  Append-only — the superseded entry is annotated, never deleted.

The harness itself (LongMemEval 5-ability taxonomy + 3-stage ablation, stdlib-only)
is the reusable asset future memory-feature work pre-registers its hypothesis
against (see `docs/LESSONS.md` L-26/L-27/L-28 and the gameplan post-mortem).

### Concurrent, multi-axis gameplans (1.2.0)

A project can run more than one gameplan at once — a feature build, a standing
maintenance loop, a creative campaign — each its own axis of work. The engine keeps
a single **focus** pointer (the default target for status, handoffs, preflight) and
a **portfolio** view across every open gameplan:

- **Focus & portfolio** — `cz_focus` switches the focused gameplan; `cz_gameplans`
  lists the whole portfolio (each card carries its kind, lifecycle, current/next
  phase, blockers, and pending cascades). The legacy single-gameplan path is just
  the one-axis case: it resolves to the identity default, so existing projects behave
  exactly as before.
- **Gameplan kinds** — every gameplan has a *kind* (`driven` — a finite phase DAG
  with a terminal post-mortem; `loop` — a standing iterative maintenance gameplan;
  `campaign` — a creative campaign), defined as data and extensible via a
  `.clauderizer/kinds/` overlay. A kind carries a display-only lexicon (a campaign's
  phases read as "stages", its outputs as "assets") over canonical on-disk headings,
  so every parser keeps working while digests and handoffs speak the kind's
  vocabulary.
- **Per-kind preflight** — a kind can declare its own preflight gates, wired to real
  shell commands in `.clauderizer/preflight.<kind>.toml`. A declared-but-unwired QA
  gate warns ("declared but did not run") rather than reading a false green.
- **Cross-gameplan dependencies** — `cz_consumes` records that one gameplan relies on
  a tracked entity another axis owns; transitioning or cascading that entity then
  fans a pending cross-reference into the consuming gameplan, even when a different
  axis holds focus.

### Fast retrieval — the abstract index (1.3.0)

A compact, addressable record per corpus entry (id, title, a one-line abstract, an
anchor, a distinctive-token set, a content hash) kept in a **disposable** cache that
is always rebuilt from canonical markdown (INVARIANT-01), so a consumer can find and
read exactly the entry it needs instead of loading a whole corpus file:

- **`cz_get`** — fetch one entry's full body by id (a decision, invariant, finding,
  or lesson). The read path may refresh the disposable cache but never mutates
  canonical markdown, so it stays a read.
- **Abstracts on `cz_analyze`** — each ranked hit now carries its one-line abstract,
  so the agent can often judge relevance straight from the result without a follow-up
  fetch. The abstract is a pointer to canonical markdown, never an authority (D-013).
- **Write-time near-duplicate advisory** — `cz_add_lesson` checks the new lesson's
  distinctive-token overlap against the existing corpus and, above a length-normalized
  threshold, nudges "consider consolidating" — advisory only, never a block. The same
  single canonical tokenizer and near-duplicate threshold back this advisory, the
  abstract index, relevance ranking, and the corpus-health redundancy metric, so the
  whole engine shares one definition of "near-duplicate" (D-041).

### Scoped memory, approvals, deliverables, conditions & modernization (1.4.0)

Four additive capabilities over the same canonical structure, plus the upgrade
path that delivers them to existing repos:

- **Scoped memory** — an invariant may carry a `**Scope**:` line binding it to one
  gameplan and an `**Audience**:` label for one working role; lessons may carry an
  audience tag. Reads *filter* (the analyze gate and the handoff's governing
  invariants skip other gameplans' scoped rules; `cz_next_phase_context(audience=…)`
  returns one role's view), the canonical files and the written handoff always carry
  everything, and curation never proposes consolidating across scopes or audiences.
  The write-time near-duplicate advisory covers invariants too, through the same
  single tokenizer and threshold.
- **Approval criteria** — `APPROVAL: <artifact-path> — <description>` exit criteria
  plus `cz_approve_gate`, which records a sign-off as the artifact's content hash.
  Satisfaction is computed at read time: an edited artifact makes the approval read
  stale in check-off, phase completion, and pre-flight until re-approved.
- **Deliverables** — a kind may define a deliverable lifecycle (`[lifecycle]` in its
  TOML); each deliverable is a tracked entity with a `gameplan` field, rendered as a
  board by `cz_gameplans gameplan_id=…` with a one-line digest rollup. A deliverable
  is an execution unit (a film, a deck), never an individual rendered file.
- **Standing conditions** — `.clauderizer/conditions.<gameplan-id>.toml` declares
  shell probes (exit 0 = met) evaluated only when status is explicitly asked for;
  a met condition surfaces "iteration proposed" and nothing runs by itself. The
  session-start hook never evaluates probes.
- **Corpus modernization** — the config carries a procedure-version stamp;
  `clauderize upgrade` / `cz_modernize` applies the mechanical tier (stamp,
  migrations, example files, the procedure-doc refresh) and surfaces memory-shaped
  gaps as advisory proposals only. Detection in the digest is a version-string
  compare — read-only and hook-safe.

### Host targeting & the injection-parity ladder

**`enabled_hosts` + `host_target`** are the third host axis (D-028 / D-046), orthogonal
to `session_host` (where commands run) and `host_profile` (the repo's language).
`[host] enabled = ["*"]` (default) means bare `init` wires **every** project-level
agent; `[host] target` is a session preference for display. Runtime injection routing
uses env-detected session agent (D-047). The multi-host MCP command is
machine-independent (`uvx --from "clauderizer[mcp]" clauderizer-mcp`); registrations
are auto-merged into each host's config (or a guide for TOML/global hosts).

Because hosts vary in what they can auto-load, status reaches the agent by the **best
reachable tier** (delivered at most once per session):

- **Tier 1 — hook (automatic):** the lifecycle hook injects the status digest at
  session start (Claude Code, Copilot, Codex, Gemini CLI, Windsurf, Cline, Amp).
  Grok Build TUI has hooks but **Hook→ctx=no** (passive stdout ignored) — not Tier-1.
  kimi (Kimi Code CLI) has injecting hooks but Clauderizer can't auto-wire them
  (guide-only TOML), so its automatic path is the P7 bootstrap until they're pasted (D-050).
- **Tier 3 — prompt:** a user-invoked `/cz-status` slash command (Cursor, Copilot,
  Continue, Gemini, Zed).
- **Tier 4 — floor (always present):** the instructions file (`AGENTS.md`, or a native
  `.continue/rules/` / `GEMINI.md`) tells the agent to call `cz_status` first.
- **Server-side bootstrap:** an automatic fallback for hook-less hosts — the MCP server
  attaches a status note to the first tool call's result (covers Continue, Zed, and
  Cursor when its hooks are governance-only).

The full per-host capability matrix and the decisions behind it live in
`docs/CROSS-HOST.md`.
