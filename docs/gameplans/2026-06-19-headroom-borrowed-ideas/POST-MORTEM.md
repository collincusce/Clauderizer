# Post-Mortem — headroom-borrowed-ideas (2026-06-19)

## Goal

Empirically test three ideas adapted from the Headroom project
(chopratejas/headroom) against Clauderizer's identity — keep what works, discard
what doesn't — without compromising the stdlib-only, deterministic, no-ML core.

## Verdicts

| Idea | Headroom analog | Verdict | Why |
|------|-----------------|---------|-----|
| #1 Prefix-stabilize the SessionStart digest | CacheAligner | **DISCARD** (D-020) | Proxy rose 65→786 chars, but the digest is ~222 tok, rendered once/session; stable-first buries actionable state. Negligible, unobservable gain for a readability cost. |
| #2a Relevance-ranked lesson **pointer** in the handoff | IntelligentContext | **KEEP** (D-021) | Surfaces top-k relevant lessons above the unchanged list; reorders/drops nothing. 7 tests. `subsys.rituals` 0.7.0. |
| #2b Truncate the cumulative lessons tail | (budget cap) | **DISCARD** (D-022) | Reintroduces incomplete-propagation for marginal savings; `cz_consolidate_lessons` is the safe size lever. |
| #3 Failure-miner (`cz_mine_failures`) | `headroom learn` | **KEEP** (D-023) | ~80% precision on real transcripts; 2/2 on this session's dogfood; propose-only. 10 tests. `subsys.mcp-server` 0.5.0. |

## What shipped

- The handoff surfaces a **"Most Relevant Lessons for This Phase"** pointer block
  (`analyze.rank_relevant`, no ML), additive and propagation-safe.
- **`cz_mine_failures`** — a deterministic, propose-only transcript miner, wired
  into the shared ops registry (reachable via MCP and `clauderize ops`).
- 345 tests (was 305 baseline), 4 skipped — including two post-close hardening
  passes (C-01: +17 robustness tests; C-02: +6 after a second adversarial
  verification fixed 3 miner crash vectors + 1 precision miss). `subsys.rituals`
  0.7.0, `subsys.mcp-server` 0.5.0; cascade walked + resolved.

## What worked

- **Falsifiable-hypothesis framing with machine-checkable metrics (D1)** made the
  two discards clean and evidence-based rather than matters of taste.
- **Dogfooding**: the miner caught *this* session's own git/`gh` fumbles (2/2) and
  rediscovered real, previously hand-captured lessons (H-08's `wsl.exe` shim).
- **The analyze gate earned its keep at planning time** — it surfaced D-009, forcing
  idea #2 to be reorder-*not-drop* before a line of code was written.

## What we learned

- **Measure before shipping**: idea #1 "worked" by its proxy yet failed on
  cost-benefit. Without the harness it would have shipped as a readability regression.
- **`is_error` is unreliable for shell failures** in Claude Code transcripts —
  content-signature detection is required for recall.
- **Schema-drift tolerance must wrap the whole pipeline, not just `json.loads`** —
  a second adversarial pass found the file *decode* (non-UTF-8 bytes) and
  *downstream shape* errors (unhashable id, non-str text) escaped the parse
  try/except; tolerance has to extend past JSON validity to shape validity (C-02).
- **Wholesale Headroom adoption remains a NO-GO** (dependency weight, D-014/L-14).
  The value was in borrowing *concepts* and implementing them the deterministic,
  stdlib-only way — converging on Clauderizer's identity, not Headroom's stack.

## Follow-ups (non-blocking)

- Detector C (explicit user corrections) had 0 recall on this corpus; revisit cue
  tuning if real corrections show up in future transcripts.
- `_default_transcripts_dir` cannot resolve the WSL-from-Windows slug; callers pass
  the dir or set `$CLAUDERIZER_TRANSCRIPTS_DIR`.
- Optional: a `clauderize mine` CLI alias for `cz_mine_failures`.
- `_experiments/` under this gameplan holds the measurement + mining harnesses as
  provenance (not engine code, not run in CI).
