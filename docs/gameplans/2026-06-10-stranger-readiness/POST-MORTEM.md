# Post-Mortem — 2026-06-10-stranger-readiness

> Closed: 2026-06-10, all five phases complete in one session. **B5
> satisfied — the beta scoreboard reads B1–B5 ✅, only B6 (the flip)
> remains.** Suite 261 → 264. The stranger docs shipped executable
> (UPGRADING walked live, TRUST 12/12 code-cited, TROUBLESHOOTING 9/9
> strings verified), the quickstart is fixed and permanently guarded
> against the published package, and the README is repositioned. Lesson
> promoted: L-13 (distribution claims need distribution execution).

## What worked

1. **The planning procedure validated the gameplan before it existed.**
   Step 2 ("capture real source-of-truth values — never invent them")
   turned up the broken front door — `uvx clauderize init` resolving
   nothing — during gameplan *creation*. The capture was the validation;
   Phase 0 started with its headline defect already in hand.
2. **One fresh-HOME walk found four defects in concentric layers** —
   spelling → PATH trap → ephemeral wiring → channel noise — and each fix
   landed at its own layer (docs, docs, resolution logic, the wired command
   itself). The deepest two were invisible from every existing test: the
   wiring defect only manifests after `uv cache clean`, and the noise
   defect only on a cold cache, riding the wrapper's deliberate
   stderr-rerouting into the identity line probes parse.
3. **The local-wheel trick proved an unreleased fix on the real path.**
   `uvx --from <locally built wheel> clauderize init` runs the fixed code
   in a genuine cache-ephemeral environment — the digest survived
   `uv cache clean` by re-resolving, pre-release, no simulation.
4. **Self-arming CI assertions resolve the guard-vs-unreleased-fix
   tension.** quickstart.yml asserts cache-clean survival only when the
   resolved version exceeds 0.9.0 — no false red today, no human TODO to
   arm it later; the flip release activates it automatically.
5. **Doc-as-test held across all four docs.** UPGRADING's commands were
   executed verbatim in live walks (both doctor nudges fired with their
   exact messages; uninstall preserved a decoy MCP server, hand-written
   CLAUDE.md text, and docs/ while leaving zero residue); TRUST and
   TROUBLESHOOTING ship only grep-verified claims; quickstart.yml greps
   the README for the exact command it runs.
6. **Docs-only phases flow fast**: five phases closed in one session, the
   only CI waits at the boundaries (phase 0's two runs, phase 4's
   final-text runs).

## What didn't (root causes)

1. **The front door was broken since the README existed.** Root cause is
   L-12's exact mechanism on a different surface: the author's environment
   (editable venv) never executes the published install path, so
   `uvx clauderize init` was never once run as written until this
   gameplan. Now promoted as L-13 and permanently guarded by quickstart.yml.
2. **The README's release section contradicted RELEASING.md** — written
   before the ritual existed, never reconciled (G7 drift *between two docs
   in the same repo*). Caught only because D3 forced a deliberate pass.
   Improvement #3 below.
3. **The ephemeral-wiring defect shipped in 0.9.0** despite that release
   passing every gate — because no gate exercised the uvx-resident init
   path. The beta gates were OS-shaped and repo-shaped but not
   install-mode-shaped; B5 closed that class.

## Friction log (host/tooling, with workarounds)

1. **The PowerShell→wsl.exe quote chain claimed another victim** (an
   inline for-loop verification script degenerated into nonsense output).
   The rule stands absolute: WSL shell logic goes in a script file via
   `Write`, never inline — even for "trivial" loops.
2. **Computer crashed mid-close-out.** Recovery was trivial by design:
   every tracked write had already landed via blessed tools, the resume
   digest said exactly where things stood, and git status named the three
   uncommitted files. The close-out resumed at the post-mortem with
   nothing lost — cross-session durability working as built.

## Procedure improvements (concrete)

1. **L-13 promoted**: walk the published artifact from a fresh
   environment; pin the walk as CI executing the doc's exact text;
   self-arm assertions for unreleased fixes.
2. **Self-arming assertions** are now the house pattern for guarding fixes
   that ship later than their guard.
3. **Release-time doc-sync candidates for GP-C**: the bare-IO meta-test
   (no `read_text`/`write_text` without `encoding=` repo-wide) and a
   TRUST.md/README release-section sync check — G7 drift between sibling
   docs should fail a check, not wait for a deliberate pass.

## Carried forward (gameplan C: beta-flip, B6)

Scope refined in the outputs registry (`b5_consolidated_and_gpc_scope`):
the 0.10.0 flip release ships the ephemeral-wiring fix + `-q` wiring and
ARMS quickstart.yml's cache-clean assertion; classifier
`pyproject.toml:15` → `4 - Beta`; version by fresh four-registry sweep
(L-08); burn-down candidates (bare-IO meta-test, MCP-staleness nudge,
doc-sync check); post-flip verification (uvx --refresh, quickstart watch,
README maturity section update to beta). Carried residual: G6's literal
native-harness cold start, closable opportunistically.

## Final state

B1–B5 ✅ with dated artifacts in RELEASING.md's evidence table. Suite 264;
quickstart and the 9-cell matrix green on the final text (runs 27317115908,
27317115901); four executable stranger docs; README repositioned (flagged
for the user's review as the product's public face); the findings tracker
still all-resolved. Beta is one gameplan — essentially one release — away.
