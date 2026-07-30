---
id: subsys.state-stamp
type: subsystem
version: 0.1.0
status: active
depends_on:
  - subsys.paths
  - subsys.config
  - subsys.revision
last_verified: 2026-07-27
---

# State Stamp

The per-call `cz_state` notice — INVARIANT-10's category (D-072): figures-only,
change-triggered live state attached to tool results at the ops dispatch seam,
so an agent re-anchors on real numbers at every structured read and sees its
own writes move them within one batch. Not status injection: INVARIANT-08's
once-per-session tiers are untouched.

**`armed()`** — the silent-by-default gate: true only when the
`CLAUDERIZER_STATE_STAMP` environment variable is `1` (per-process and
ephemeral, never a config flag) until D-064 matrix evidence graduates the
default.

**`compute_stamp(paths, config)`** — the live figure set recomputed from
canonical markdown per call: gameplan, phase `N/T`, phase_status, blockers,
open_items, exit_criteria `checked/total`, pending_cascades, revision. Every
key sits in **`FIGURE_KEYS`**, the whitelist a ratchet test pins — growing it
is a forced judgment. The exit-criteria figure counts RAW checkboxes in the
phase block (byte-bounded — it never recomputes approval artifact hashes).
Returns `None` on any failure: the stamp never invents and never breaks an op.

**`emit(paths, config)`** — the change trigger: compares against this
process's last emission (in-memory, session-scoped) and returns `None` when
the figures are byte-equal, so an unchanged repo attaches nothing.

Attachment lives in `ops._stamped` (one seam for MCP, `run_op`, and direct
REGISTRY callers); `cz_status`/`cz_next_phase_context` are excluded as strict
supersets (D-027). Isolation is pinned in both directions by
`tests/test_state_stamp.py`: a stamp exception never alters an op result, and
an op exception is never masked by stamping.
