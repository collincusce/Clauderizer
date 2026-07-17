# Post-Mortem — kimi-desktop-daimon-host-mcp-autowrite

**Closed:** 2026-07-17 · **Shipped in:** Clauderizer 1.9.0 · **Decision:** D-053 ·
**Correction:** C-01 · **Lesson:** L-58 · **Baseline:** 823 → **837 passed, 5 skipped** ·
**cz_audit at close:** 0 findings

## Goal

A user found, live, that the **Kimi Work desktop app** (daimon runtime) is a distinct
host that reads MCP only from its per-user runtime-home `mcp.json` — never project
configs — and has no hooks, so a correctly-init'd repo gave desktop sessions **zero
tools**. Make it a first-class **auto-write** host, UX-first, all platforms.

## Outcome

New `kimi-desktop` host: `clauderize init` detects the daimon runtime home
(Windows/macOS/Linux + the repo-in-WSL/app-on-Windows case) and auto-registers the
`clauderizer` server there — the **single deliberate exception** to D-031's
global-config→guide-only rule (D-053), justified purely by UX. Kept narrow:
detected-only, non-destructive + atomic, **repo-agnostic** command, and an env
opt-out. doctor reports it and warns loudly; uninstall removes it.

## What worked

- **Injectable-everything paid off twice.** Building every path/command function to
  take an injected home/platform/environ/which meant the platform matrix and the WSL
  case were unit-testable against temp dirs — and it was the seam that let the
  autouse test-guard slot in cleanly after the dogfood found the hazard.
- **The product-owner call was the right frame.** Recording D-053 as *the one*
  deliberate D-031 exception (with mitigations) kept the constitution intact — every
  other global-config host is still guide-only; this one is documented as special.

## What didn't (root causes) — the dogfood earned its keep

- **The design shipped a repo-specific command into a per-user file.** Phase 0
  designed a `wsl.exe … cd <repo> && uvx` wrapper for the WSL case. But the daimon
  config is **one file for all repos**, so pinning it to a repo was wrong — and a live
  `clauderize doctor`/`init` smoke against the *real* installed app revealed the true
  damage: the test suite's `init()` calls had been **overwriting the user's real
  config** with a pointer to a since-deleted pytest tmp dir. Root cause: an init step
  that writes an absolute per-user path hits real machine state, and a per-user config
  can't encode a repo. Fixed both: repo-agnostic command (the user's own verified
  shape) + an env opt-out honored by the detector + an autouse conftest guard, proven
  by asserting the real file was byte-unchanged across the full run. C-01 / L-58.
- **Only caught because the dev machine had the app.** A CI-only project would have
  shipped the repo-specific wrapper. The lesson: dogfood host integrations against the
  real host, and treat any real-per-user-path write as a test hazard from the start.

## Procedure improvements

- None to `GAMEPLAN-PROCEDURE.md`; L-58 captures the reusable rule (per-user config →
  repo-agnostic command; absolute-per-user writes are an L-29 test hazard).

## Open threads

- **macOS/Linux daimon paths are best-effort** (Windows confirmed live). The candidate
  probes (`~/Library/Application Support/…`, `~/.config/…`) need confirmation from a
  real mac/Linux desktop install; detection is detected-only so a wrong guess simply
  no-ops.
- **AGENTS.md read-status on the desktop host is unknown** — MCP is treated as the only
  lane regardless, which is the safe assumption.
- **The out-of-scope shell-broken case** (no MCP *and* no working CLI shell → memory
  read-only) remains a good future `doctor` "no reachable lane" check.
- **Release:** ship 1.9.0 (branch → main → tag `v1.9.0` → CI → GitHub Release → PyPI).
