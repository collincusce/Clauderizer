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

### Host targeting & the injection-parity ladder

**`host_target`** is a third host axis, orthogonal to `session_host` (where commands
run) and `host_profile` (the repo's language): the `[host] target` line in
`.clauderizer/config.toml` (default `claude-code`) selects which agent `init` wires.
The MCP command it emits is machine-independent (`uvx --from clauderizer
clauderizer-mcp`); the registration is written into that host's own config file —
auto-merged for hosts with a JSON config, emitted as a `.clauderizer/<host>-setup.md`
guide for TOML/global hosts.

Because hosts vary in what they can auto-load, status reaches the agent by the **best
reachable tier** (delivered at most once per session):

- **Tier 1 — hook (automatic):** the lifecycle hook injects the status digest at
  session start (Claude Code, kimi, Copilot, Codex, Gemini CLI, Windsurf, Cline, Amp).
- **Tier 3 — prompt:** a user-invoked `/cz-status` slash command (Cursor, Copilot,
  Continue, Gemini, Zed).
- **Tier 4 — floor (always present):** the instructions file (`AGENTS.md`, or a native
  `.continue/rules/` / `GEMINI.md`) tells the agent to call `cz_status` first.
- **Server-side bootstrap:** an automatic fallback for hook-less hosts — the MCP server
  attaches a status note to the first tool call's result (covers Continue, Zed, and
  Cursor when its hooks are governance-only).

The full per-host capability matrix and the decisions behind it live in
`docs/CROSS-HOST.md`.
