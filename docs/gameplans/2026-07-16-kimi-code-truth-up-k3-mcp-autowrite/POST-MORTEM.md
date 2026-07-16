# Post-Mortem — kimi-code-truth-up-k3-mcp-autowrite

**Closed:** 2026-07-16 · **Shipped:** Clauderizer 1.7.0 · **Decision:** D-049 ·
**Correction:** C-01 · **Lesson:** L-49 · **Baseline:** 793 → **797 passed, 5 skipped**

## Goal (as stated)

Make Clauderizer support the just-launched **Kimi K3** model out of the box, with
session-start and MCP.

## Outcome

Kimi K3 is a *model*, not a host — it is served by the **Kimi Code CLI**, which
Clauderizer wires as the `kimi` host. The host's MCP is now **auto-written** to the
project-level `.kimi-code/mcp.json` (`mcpServers`, non-destructive, Cursor-identical),
so a bare `clauderize init` gives Kimi K3 users the `clauderizer` server with zero
manual steps. Session-start hooks stay a guide (TOML), now single-sourced and pointed
at the correct `~/.kimi-code/config.toml`, with the skills-exposure gap documented.

## What worked

- **Phase 0 caught a wrong premise before any code changed.** The plan assumed one
  host that renamed `.kimi` → `.kimi-code`. Verifying the contract against upstream
  docs revealed two distinct products (legacy Kimi CLI vs successor Kimi Code CLI).
  The verification-first phase paid for itself — a code-first approach would have
  "fixed" a path that was actually correct for the legacy tool.
- **The change turned out small despite the premise correction.** Repointing the
  `kimi` emitter to `.kimi-code/mcp.json` was exactly the Phase 1–3 structure already
  drafted; only the rationale and the skills/AGENTS.md notes changed. The user's
  "repoint kimi" decision kept the host surface at one id.
- **Table-derived machinery generalized for free.** `detect_host_target`,
  `wiring_contract_sweep`, and `path_safety_audit` all derive from `HOST_EMITTERS`, so
  flipping `auto_write` made kimi a first-class citizen across all of them with no
  per-function edits — only the golden guide-only test needed updating.
- **Single-sourcing removed real drift.** Two kimi guides (`kimi-setup.md` from the
  claude leg and a guide-only `kimi-mcp-setup.md`) collapsed into one
  `hosttargets.kimi_setup_guide()`, emitted by the per-host wiring.

## What didn't (root causes)

- **Initial diagnosis conflated two products.** The opening analysis called the
  `~/.kimi/config.toml` path "stale." Root cause: two Moonshot CLIs share the "kimi"
  brand and diverged (`kimi-cli` pip/`~/.kimi/` vs `kimi-code` npm/`.kimi-code/`).
  Caught in Phase 0, recorded as C-01, promoted as L-49. Cost was one round-trip of
  user clarification — cheap because it happened during verification, not execution.
- **Upstream docs were internally inconsistent.** `moonshotai.github.io/kimi-cli`
  and `www.kimi.com/code` disagree on config paths; only cross-reading both plus the
  GitHub repos disambiguated predecessor from successor. A single doc source would
  have cemented the wrong premise.

## Procedure improvements

- **L-49** now encodes the trap: confirm one-product-moved vs two-distinct-products
  before repointing host paths, and check whether a successor drops conventions
  (Kimi Code CLI does not read `.claude/skills`).
- Host "truth-up" gameplans should keep a dedicated **contract-verification phase 0**
  whose exit criteria include *product identity*, not just config schema — this one
  earned its place.

## Follow-up review ("go max, check your work")

A post-close adversarial pass — real CLI end-to-end runs plus a read of the adjacent
injection subsystem — found three issues the phase tests missed, all now fixed:

1. **Uninstall orphaned the guide.** `uninstall --host kimi` removed the MCP
   registration but left `.clauderizer/kimi-setup.md` behind — the remover only knew
   the `<host>-{hook,mcp}-setup.md` convention, and kimi's guide is bespoke-named.
   Fixed + regression test (`test_uninstall_kimi_removes_mcp_and_setup_guide`).
2. **Honesty regression on AGENTS.md.** The repoint inherited a guide line asserting
   the AGENTS.md floor loads on kimi — but Kimi Code CLI's AGENTS.md read-status is
   unverified (conflicting upstream signals). Reworded to lean on the **P7 server
   bootstrap** as the reliable automatic orientation; CROSS-HOST matrix marked
   AGENTS.md `unverified`.
3. **`_HOOK_HOSTS` classification was dishonest (D-050).** kimi was listed as a
   status-delivering hook host, but Clauderizer can't auto-wire its hooks (guide-only
   TOML). Removed it — the bootstrap is its automatic path. Behaviorally inert (a real
   kimi session resolves to `unknown` and already gets the bootstrap), but it makes
   `best_tier`/`delivers_status_via_hook` honest and closes a dark-session footgun.

Root cause across all three: the repoint changed *which product* the `kimi` host
targets, and a successor can differ from its predecessor in more than paths (no
auto-wired hook, uncertain AGENTS.md) — the same shape as L-49. Lesson reinforced:
after repointing a host, re-audit every consumer that branched on the old host's
assumed capabilities (uninstall naming, injection tier, floor delivery), not just the
MCP path. Suite 797 → **798 passed, 5 skipped**.

## Open threads

- **AGENTS.md read-status on Kimi Code CLI is likely-but-unconfirmed.** The
  `kimi-code` repo ships an `AGENTS.md`, so the floor almost certainly loads, but this
  was not verified against a running install. Confirm at the next real Kimi Code CLI
  integration test (the standing "consumption proof is manual" residual, O-02 class).
- **Skills parity is documented, not automated.** Per user decision, the guide tells
  users to expose Clauderizer skills to `.kimi-code/skills`/`.agents/skills`; a future
  gameplan could auto-emit them for true zero-touch parity.
- **Legacy Kimi CLI** (`~/.kimi/`) is now unwired (the `kimi` id points at the
  successor). If any users remain on the pip tool, they lose auto-wiring; acceptable
  given it is the superseded product, but worth a note if it resurfaces.
