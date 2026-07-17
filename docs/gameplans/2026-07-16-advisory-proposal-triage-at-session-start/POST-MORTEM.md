# Post-Mortem — advisory-proposal-triage-at-session-start

**Closed:** 2026-07-16 · **Shipped in:** Clauderizer 1.8.0 · **Decision:** D-052 ·
**Baseline:** 807 → **821 passed, 5 skipped** · **cz_audit at close:** 0 findings

## Goal

Fix a real UX confusion (the user's own): `clauderize upgrade` dumped every advisory
proposal to stdout, persisted nothing, and once a corpus was version-current the
digest stopped surfacing them. Make the proposals **triageable** and **surfaced at
session start**, terse at upgrade.

## Outcome

Persistent triage (**handle / dismiss / defer**): stable content-derived proposal ids
+ a per-user gitignored ledger (`.clauderizer/proposals.local.toml`); `cz_dismiss_proposal`
/ `cz_defer_proposal`; a one-line digest nudge (pending count only, riding the single
digest); a terse `clauderize upgrade`; and a `clauderizer-modernize` skill that walks
the agent through them ask-first. The engine still never invents project content — the
skill *proposes*, the user *decides* (INVARIANT-05).

## What worked

- **The invariant map made the design fall out cleanly.** Naming up front that the
  hook only *surfaces* (INVARIANT-04/06) and the agent *triages* resolved the "should
  session start prompt me?" tension without breaking the never-block rule — the design
  wrote itself once that line was drawn.
- **Stable ids gave "dismiss until it materially changes" for free.** Hashing the
  identifying parts means a re-worded proposal stays dismissed but a genuinely new one
  (extra gate) re-surfaces — no expiry logic needed. Proven both directions (L-25).
- **`cheap=True` kept the hook honest.** The digest count reuses `modernize.report`
  minus its one expensive detector (the abstract-index near-dup scan), wrapped
  best-effort so a failure just means no nudge — the hook never breaks or blocks.
- **The golden digest snapshot held** (`test_back_compat_focus`): the new line only
  fires when `pending>0`, and the sample repo has no proposals, so the frozen digest
  stayed byte-identical (L-41 — make the legacy case the default).

## What didn't (root causes)

- **Nothing failed in-flight** — `cz_audit` closed at 0 findings. But that is *because*
  the discipline was followed continuously (committed each phase, cascaded, kept the
  version single-sourced), not because the work was trivial. The gate catches the
  sloppy case; a clean run sailing through is the intended shape.

## Dogfood of 1.7.0 (blind, as asked)

- **`cz_audit` ran exactly as shipped** and returned 0 mechanical findings (release:
  clean — single-sourced 1.8.0; git: clean; graph: no pending cascades/open items).
  The 4 judgment checks were then affirmed by hand:
  1. *clean-environment* — verified in a fresh venv every phase (821 fresh).
  2. *consumer re-audit* — traced every consumer of the changed entities: `cz_modernize`,
     `status_bundle`, `cmd_upgrade`, the tool surface, the skill, `init` gitignore, and
     `clauderize ops` (smoke-tested). Uninstall needs no change (the ledger is a
     gitignored per-user cache, like `index.json`).
  3. *claim honesty* — every shipped claim (tools, skill, ledger, digest line) is backed
     by a test; the skill *instructs* handle/dismiss/defer, it doesn't claim to auto-do.
  4. *shipped-artifact reality* — all asserted by tests.
- **The close flow felt right as a first-time user**: the skill's self-audit step is
  concrete and actionable, and a well-run gameplan clears it in seconds.
- **One honest friction surfaced**: the running MCP server predates a tool added *this
  session*, so `cz_audit` wasn't callable over MCP — I ran it via `clauderize ops`. That
  is inherent (an MCP server loads its tool set at launch), but it means "added a cz_*
  tool mid-session → use the CLI or start a fresh session." Worth a docs note.

## Procedure improvements

- None to `GAMEPLAN-PROCEDURE.md` this round — triage is a tooling/UX layer on the
  existing two-tier upgrade (D-042), which the procedure already describes; the
  methodology didn't change, so the procedure version stayed at 1.7.0.

## Open threads

- **Hook latency of the digest count.** The cheap report still walks open gameplans +
  the onboarding scan on every status/session-start. It's best-effort and skips the
  expensive scan, but its cost on a very large corpus is unmeasured — a future change
  could cache the count or gate it behind a cheaper pre-check.
- **`defer` granularity.** Defer is a fixed-day snooze (default 7). "Remind me next
  session" would be more intuitive than a date, but sessions aren't cheaply identifiable
  from a stateless CLI; revisit if users find the day-snooze unintuitive.
- **Release.** 1.8.0 stacks on 1.7.0 (now live on PyPI). Ship 1.8.0 the same way when
  ready (branch → main → tag `v1.8.0` → CI green → GitHub Release → PyPI).
