# Post-mortem — multi-host-default-wiring

> Closed 2026-07-09 with Clauderizer **1.6.0** on PyPI.

## What worked

- Splitting **wiring set** (`enabled=["*"]`) from **session routing** (env detect)
  fixed the exclusive-`--host` UX without breaking INVARIANT-07 Claude hooks.
- Portable multi-host `.mcp.json` (`uvx --from "clauderizer[mcp]"`) + scoped
  Claude-only path for windows-wsl dogfood kept dual-entry honest.
- Grok field work (Hook→ctx=no, governance hooks, tier 4 + P7) composed cleanly
  into the multi-host default.
- Release ritual held: release-check exit 0 → tag after push → GitHub Release →
  Trusted Publishing success → PyPI 1.6.0.

## What didn't / friction

- Multi-host bare init initially overwrote session_host-composed wsl.exe MCP,
  breaking windows-wsl doctor/consumer-leg tests until scoped Claude-only tests
  and portable MCP probe rules were adjusted.
- Doctor path-safety for intentional dogfood shims must be **info**, not
  unverifiable exit-3, or green local Claude installs false-fail.
- README "What init drops in" lagged the multi-host tree until a final docs pass.

## Procedure improvements

- Present-tense host docs must be swept when init wiring taxonomy changes
  (README tree, features/init-cli, VISION, TRUST) — not only the "Works with"
  marketing section (L-21).
- When adding a host-target with Hook→ctx=no, never put it in `_HOOK_HOSTS`
  (suppresses P7). Document that as a hard rule next to the matrix row.

## Open threads

- O-05 (Grok gameplan): external ask for SessionStart stdout → model context
  remains open for future Tier-1 promotion.
- Website (clauderizer.com) refresh if not auto-synced from README/PyPI.
