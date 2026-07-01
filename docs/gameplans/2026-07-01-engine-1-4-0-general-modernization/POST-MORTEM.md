# Post-Mortem — 2026-07-01-engine-1-4-0-general-modernization

> Written at close, 2026-07-01. Engine 1.3.1 → 1.4.0; procedure 1.4.0 → 1.5.0; suite 716 → 755; tool surface 42 → 44.

## What this gameplan set out to do

Implement the adopted core of the marketing-studio feature brief (2026-07-01 analysis) — scoped memory, hash-bound approval gates, deliverable-matrix campaigns, standing conditions — plus the user's overarching requirement: **upgrading the engine must deliver its improvements to existing corpora automatically in the general sense** (mechanically where safe, advisorily where memory is involved). Ship as 1.4.0.

## What happened

Ten phases, all complete, in one continuous same-day arc. Every feature landed additive: untagged/unconfigured repos behave byte-identically to 1.3.1 (golden-pinned; the golden now models a modernized corpus, with the legacy modernization line pinned separately). The centerpiece — `clauderize upgrade` / `cz_modernize` over a `procedure_version` stamp — was proven live on the two real corpora the same day it was built.

## What went right

- **The recon-first rhythm.** A single thorough code-recon subagent up front (file:line anchors for all six touch areas) meant nearly every phase's edits landed on the first try; the suite was green on first run for phases 2, 4, and 5.
- **Dogfood found real engine work.** Running the pass against marketing-studio exposed **overlay shadowing** (a pre-lifecycle `.clauderizer/kinds/campaign.toml` pins the kind's old capability set) — unknowable from fixtures — and produced the `stale_kind_overlay` detector the same hour. It also *measured* the near-dup threshold question (O-02): the same-length duplicated invariant fired at Jaccard 0.467; the subset-shaped pairs are structurally invisible to symmetric Jaccard → O-04 (overlap coefficient) filed with evidence instead of a guess.
- **Computed reopening beat written reopening.** Approval staleness as a parse-time computation (hash mismatch → reported unsatisfied) needed no auto-write at all — the cleanest advisory-gate posture, and it made preflight/transition surfacing free.
- **Corrections as designed.** Three plan-vs-reality divergences were recorded (C-01: write-side audience filtering refused on propagation grounds; C-02: consumes surfacing already existed since 1.2.0; C-03: the studio's same-day gate wiring + overlay masking), each with the criteria re-authored on the record rather than quietly waved through.

## What bit

- **wsl.exe quoting (the L-29 family's bigger sibling).** Command substitution, pipes in grep patterns, parentheses in commit messages, and credential-helper strings all got shredded crossing PowerShell → wsl.exe → bash. The durable fix was a session helper script in `.git/` (never committed) with named modes — zero quoting incidents after it. Recorded as gameplan lesson #1.
- **1.3.1 shipped a claim, not a file.** The preflight hint (and changelog) referenced `.clauderizer/preflight.<kind>.toml.example`, but nothing ever scaffolded it. Found while building the feature whose job is closing exactly such gaps; `upgrade` now writes it. Recorded as gameplan lesson #2: a changelog claim about a shipped artifact needs a test that the artifact ships.
- **The parenthesis sanitizer.** `cz_approve_gate`'s note sanitizer replaced `)` but not `(` — caught by its own test on first run. Cheap, but a reminder that markers with delimiter characters need both sides handled.

## Numbers

- Phases: 10/10 complete. Corrections: 3. Open items: O-01 (pre-existing suggested-edge triage), O-03 (marketing-studio reply + usage fixes, post-ship), O-04 (overlap-coefficient companion signal) remain open, deliberately.
- Suite: 716 → 755 (+39 across test_scoped_memory, test_approval_gates, test_deliverable_matrix, test_standing_conditions, test_modernize).
- Surface: 42 → 44 (`cz_approve_gate`, `cz_modernize`); CLI parity live-verified; new subcommand `clauderize upgrade`.
- Live dogfood: 2 corpora upgraded; marketing-studio's portfolio byte-identical before/after; 2 honest residual proposals there (the real INVARIANT-03/08 duplication at Jaccard 0.467, and the stale kind overlay with the exact lifecycle TOML to paste).

## Ship record

release-check exit 0 → PR #18 → 9-cell CI green before any tag → squash-merge `2ecc9c53afe7a36cc5fff60dce1f2d2fe37508a6` → tag `v1.4.0` on the full SHA → GitHub Release (latest, non-prerelease) → OIDC publish run 28549676626 green with attestations → PyPI `info.version = 1.4.0` → `uvx --refresh` resolves 1.4.0.
