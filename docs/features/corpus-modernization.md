---
id: feat.corpus-modernization
type: feature
version: 1.1.0
status: completed
depends_on:
  - subsys.scaffold@^0.8.0
  - subsys.mcp-server@^0.9.0
  - subsys.rituals@^0.7.0
  - subsys.modernize
last_verified: 2026-07-30
introduced_by: D-042
documented_in: docs/gameplans/2026-07-01-engine-1-4-0-general-modernization/GAMEPLAN.md
---

# Corpus Modernization

When the engine moves ahead of a repo's corpus, the new version's improvements
should reach the repo without a hand migration — but "automatically" cannot mean
the same thing for a scaffold file and for a decision log. So `clauderize
upgrade` / `cz_modernize` works in two strictly separated tiers, and the line
between them is **ownership, not risk** (D-042):

- **Mechanical — applied for you.** Engine-owned, git-diffable, reversible with
  `git checkout`: the config's `procedure_version` stamp and config migrations,
  missing per-kind gate example files, the `.clauderizer/kinds/` overlay
  directory, per-machine paths absent from `.gitignore`, doc modules the size's
  manifest gained since this repo was inited, and a refresh of the engine-owned
  `GAMEPLAN-PROCEDURE.md` copy.
- **Memory — proposed, never applied.** Everything recording a judgment the
  project made surfaces only as an advisory proposal naming the ordinary
  recording tool that would act on it (INVARIANT-05). `DECISIONS.md`,
  `INVARIANTS.md`, `LESSONS.md`, `HARDENING.md` and gameplan directories are
  never edited by a version bump.

The recurring failure this feature exists to prevent is a fix that reaches only
*fresh* installs — every install in the world has already run `init`. Two
mechanical actions are here specifically because their fix would otherwise reach
zero existing repos: `ensure_gitignore_current` (D-067) and, since 2.0.0,
`ensure_modules_current` — measured on a live 1.13.0 → 2.0.0 walk where the
refreshed stanza and the fleet skill referenced `docs/ENFORCEMENT.md` and
`docs/GLOSSARY.md` that an upgraded repo never received. Each writes only when
absent, so no user content is ever clobbered, and each is idempotent.

Detection is read-only, cheap enough for the status digest to call on every
session, and stateless: `report()` re-derives everything and writes nothing, so
there is no accumulated state to disagree with the corpus. Proposal triage
(dismiss/defer, with content-derived ids so a materially changed proposal
re-surfaces) is layered on top by `subsys.proposals`. The digest carries **at
most one** modernization line (D-027, INVARIANT-08).

The counterpart check lives in `clauderize doctor`: `engine-referenced docs
present` fails loudly when the engine's own wiring names a doc the repo does not
have — the D-069 detector for the class above, because 2.0's occurrence of it
shipped with doctor printing a green "corpus modernized" line over exactly that
breakage.
