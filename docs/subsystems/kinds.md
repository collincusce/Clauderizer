---
id: subsys.kinds
type: subsystem
version: 0.2.0
status: completed
depends_on:
last_verified: 2026-07-01
---

# Kinds

A **kind** is a gameplan's *type and skin*: the vocabulary it reads in, the phase
template it starts from, and which preflight checks it runs. It is the second
data-driven axis, **orthogonal to the host `profile`** (which is the language —
how to run tests/build). Both are pure data: adding a kind is a new
`kinds/<name>.toml`, never an engine change — exactly how adding a language is a
new `profile`.

The two axes compose: a `campaign` kind on a `python` host resolves its preflight
from the kind (QA gates), not from pytest.

## The kind shape

A kind is parsed into the `Kind` dataclass (`kinds/__init__.py`) from a TOML file:

```toml
name = "campaign"

[template]
first_phase = "Concept"        # the first phase cz_create_gameplan names

[lexicon]                       # DISPLAY-ONLY relabels (see below)
phase = "stage"
decision = "creative decision"
output = "asset"
preflight = "QA"
gameplan = "campaign"

[preflight]
checks = ["clean_tree", "virality", "brand_lint", "duration"]
```

`Kind.label(term)` maps a canonical term to the kind's word, returning the term
unchanged when the kind doesn't relabel it (so `driven` is a pure pass-through).

## Shipped kinds

Three files ship in `src/clauderizer/kinds/`:

- **`driven.toml`** — the default: a finite phase DAG with a terminal post-mortem.
  Identity lexicon and an empty preflight list (defers to `config.preflight_checks`),
  so a driven gameplan behaves **exactly** as before kinds existed.
- **`loop.toml`** — a standing, iterative maintenance gameplan (see
  `GAMEPLAN-PROCEDURE.md` "Loop Gameplans"); relabels phase → *iteration*.
- **`campaign.toml`** — a creative campaign expressed as a gameplan; relabels
  phase → *stage*, output → *asset*, etc., and ships generic QA gate names.

## The lexicon is display-only

The lexicon relabels only **transient surfaces** — the `cz_status` summary, the
portfolio card phase word, and the generated handoff headings. The on-disk section
headings (`## Phase Breakdown`, `### Phase N`) and the op names stay canonical, so
every parser and test is untouched and the DAG/data model is identical across
kinds. A campaign's digest reads "Stage 2/5" while the file still says "Phase 2".
The handoff relabel is safe because those headings live inside the regenerated
`clauderizer:handoff` marker block, never parsed back.

## Per-kind / per-gameplan preflight

Preflight resolves its check **list** from the focus gameplan's kind: a non-empty
`kind.preflight_checks` wins (a campaign's gates), otherwise `config.preflight_checks`
(so driven is unchanged). Every check that isn't a built-in **structural** check
(`branch_base`, `clean_tree`, `deps_spotcheck`, `branch_creation`,
`cascade_hygiene`, `handoff_presence`) is a **command gate**: a named shell command
that passes/fails by exit code. Its command resolves from
`.clauderizer/preflight.<kind>.toml` (`[gates]` table) first, then the host profile
for the canonical `tests`/`build` gates. An unwired gate skips with a hint. The
engine ships the run-named-gates mechanism; the user wires the QA logic.

## Per-project override

`kinds.load_all(extra_dir)` overlays `.clauderizer/kinds/<name>.toml` on the
packaged kinds: a file with a packaged name **overrides** it; a new name **adds** a
custom kind. A malformed overlay file is skipped, never fatal — the same
fail-soft contract as the profile lock.

## DAG position

**Scaffold reads a kind** — `cz_create_gameplan` validates the kind and templates
the first phase from it, stamping `> Kind:` into `GAMEPLAN.md`. **Status & handoff
read a kind** — they relabel display strings via the lexicon. **Preflight reads a
kind** — it resolves the check list and gate commands per the focus kind. The kind
name itself is parsed back from the `> Kind:` header by `status_bundle.gameplan_kind`
(default `driven` when absent, so legacy gameplans need no rewrite).
