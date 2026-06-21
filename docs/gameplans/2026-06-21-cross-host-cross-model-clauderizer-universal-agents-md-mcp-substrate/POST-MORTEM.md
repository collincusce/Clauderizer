# Post-Mortem — Cross-host & cross-model Clauderizer

> Gameplan: `2026-06-21-cross-host-cross-model-clauderizer-universal-agents-md-mcp-substrate`
> Closed: 2026-06-21 · Shipped: **0.16.0** to PyPI · Suite **446 → 548**

## Summary

Generalized Clauderizer from a Claude-Code-(+kimi) tool into a **universal substrate** for
~11 agentic coding hosts, over the AGENTS.md + MCP surface, with Claude Code parity strictly
unchanged (INVARIANT-07). Fourteen phases (P0–P13): a capability audit and parity contract;
the model-agnostic injection substrate (session signal, host-neutral floor, MCP prompts,
tier-routing, server-side bootstrap); per-host wiring emitters; then `clauderize init --host`
to make it all reachable; and a battle-hardening series (integration-seam sweep, concurrency/
I-O/failure modes, security/trust, UX + doc truth-up + release). Verified the wiring contract
in CI for every auto-write host, consumption on **2 real hosts** (Cursor, VS Code/Copilot),
and a **cross-model** drive by Cursor's Composer 2.5 Fast. Released 0.16.0 via the zero-incident
ritual (four registries + 9-cell CI green before tag + OIDC publish + PyPI verified).

## What worked

- **The gameplan procedure as a forcing function.** Per-phase `cz_preflight` → work → handoff →
  cascade kept 14 phases coherent across a very long session; every phase closed on a green
  suite, and the cumulative handoff meant phase N+5 never re-litigated phase N.
- **Independent post-implementation review earned its place, repeatedly** (now L-34). It caught
  real defects the phase's own TDD missed: `merge_missing` dropping `host_target`, a doctor that
  false-failed non-claude repos, the hook dispatcher not threading native cross-host event names
  (windsurf `pre_user_prompt` → digest spam), and the path-safety asymmetry (H-11). The seam
  sweep (P10) and the security review (P12) were the highest-yield phases per unit effort.
- **The wiring-contract vs consumption-proof split (D-032).** Scoping the CI gate to "emitted
  config is well-formed, path-safe, launches the server" — and treating real-host consumption
  as irreducibly manual — kept the release honest. The CHANGELOG never claimed a real-host count
  beyond what was actually walked.
- **The CLI/ops fallback (L-05) proved load-bearing for cross-MODEL,** not just no-MCP sessions —
  a non-Claude model independently rediscovered and relied on `uvx … clauderize ops`.
- **Coverage-gated memory re-distill (L-26).** `docs/LESSONS.md` 21 → 18 with rank-1 ranker
  coverage proven before and after apply — compaction without losing retrievability.

## What didn't — and the root causes

- **Two self-inflicted incidents, both from one root cause:** inside `wsl.exe -d ubuntu bash -lc
  '…'` (the Bash tool's Git-Bash → WSL bridge), `$(…)`/`$VAR`/`$$` expand in the OUTER Windows
  shell, not WSL. So a destructive `uninstall` smoke whose `cd "$(mktemp -d)"` silently no-op'd
  ran against the real dogfood repo (recovered fully via git — `uninstall` is non-destructive by
  design), and a reviewer subagent left probe artifacts in the repo. Captured as **L-29/L-30**;
  the `case "$PWD"` guard then fired and prevented a repeat. The mechanism is now in persistent
  runtime memory.
- **`host_target` silently stripped from a real repo** (the most instructive bug). Root cause:
  `cz_create_gameplan` / the active-gameplan flip does `Config.load → to_toml`, and a
  pre-`host_target` engine (published 0.15.0, run via `uvx`) doesn't model the field, so the
  rewrite dropped it — reverting the repo to the claude-code default and making doctor report
  misleading drift. Surfaced by the cross-model drive. Fixed two ways (P13): doctor now detects
  it and names the right repair, and `Config` now **preserves unmodeled keys/sections** on
  round-trip so no config-write path can silently drop a field again.
- **Cross-model adherence gaps** (now L-35). Composer 2.5 Fast drove a full gameplan but made 0
  cz_* MCP calls (used built-ins + the CLI), and hand-edited tracked docs — and its plausible
  close-out summary claimed graph entities a `reindex` showed were never created (the
  verify-don't-trust lesson, in the wild).

## Procedure / product improvements shipped

- Config forward/cross-version field preservation; host-aware doctor with strip-detection;
  full-footprint reversible `uninstall`; `--list-hosts`; corrupt-config graceful degradation;
  op↔engine signature guard (O-08); path-safety on the committable surface (H-11) + symlink-safe
  uninstall (H-12).
- Promoted enduring lessons L-29 (destructive-op isolation), L-30/L-33 (subagent discipline),
  L-31 (release gate), L-32 (measurement/saturation), L-34 (cross-cutting seam / independent
  review), L-35 (cross-model adherence). Re-recorded the 3 lost P0 amendments (A-002..A-004).

## Open threads (carried forward, nothing blocking)

- **O-10** — Amp's real on-disk `settings.json` shape unverified live (the user did not exercise
  Amp). The flat `amp.mcpServers` key is internally consistent + P4-doc-verified; confirm against
  a real Amp install and fold any correction into `HOST_EMITTERS`.
- **H-13** (LOW, open) — engine file writes follow symlinks; add an `islink`/`O_NOFOLLOW` guard
  in a future hardening pass (needs a malicious working tree; written content is not
  attacker-controlled).
- **Candidate guardrail** — a doctor/repair pass that detects hand-edits / unmodeled-field loss,
  to steer non-Claude models away from raw editing (motivated by L-35).
- **Per-host consumption beyond Cursor + VS Code** remains a manual spot-check as more hosts are
  adopted (D-032 — never claimable in CI).
- `engine_stale` for a long-running session clears on a restart (a session-lifecycle fact, not a
  bug).
