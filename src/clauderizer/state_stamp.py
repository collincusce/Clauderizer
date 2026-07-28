"""The per-call live-state stamp — INVARIANT-10's category (D-072, D-070 P2).

``cz_state`` is a figures-only, change-triggered notice attached to tool
results at the single dispatch seam (ops registry), so an agent re-anchors on
live figures at every structured read and sees its own writes move the numbers
within one batch. It is NOT status injection: INVARIANT-08's tiers are
untouched, and INVARIANT-10 defines this category's five bounds, all of which
live here —

  figures only     every emitted key sits in :data:`FIGURE_KEYS`; the whitelist
                   is ratcheted by test (adding a key is a forced judgment).
  change-triggered :func:`emit` compares against the last emission held in
                   process memory and returns ``None`` when nothing moved —
                   an in-memory, session-scoped signal, never persisted.
  advisory only    nothing reads the stamp to gate, cap, or block.
  byte-bounded     the exit-criteria figure counts raw checkboxes in the phase
                   block; it never recomputes approval artifact hashes.
  silent default   :func:`armed` gates on the ``CLAUDERIZER_STATE_STAMP``
                   environment variable (per-process, ephemeral — not a config
                   flag) until D-064 matrix evidence graduates the default.

A stamp failure of any kind yields ``None`` and leaves the op result exactly
as it was — pinned in both directions by test.
"""

from __future__ import annotations

import os
import re

from .config import Config
from .paths import RepoPaths

ARM_ENV = "CLAUDERIZER_STATE_STAMP"

#: The complete legal key set of a cz_state stamp (INVARIANT-10 bound 1).
FIGURE_KEYS = frozenset({
    "gameplan", "phase", "phase_status", "blockers", "open_items",
    "exit_criteria", "pending_cascades", "revision",
})

#: Last emitted stamp for this process (server session). In-memory only.
_last: dict | None = None


def armed() -> bool:
    return os.environ.get(ARM_ENV) == "1"


def _reset() -> None:
    """Test hook: forget the last emission."""
    global _last
    _last = None


def _raw_exit_criteria(gameplan_dir, phase: str) -> str | None:
    """``checked/total`` counted from RAW checkboxes in the phase's GAMEPLAN.md
    block — byte-bounded by design (INVARIANT-10 bound 4): no approval-state
    recompute, no artifact hashing, one file read."""
    gp = gameplan_dir / "GAMEPLAN.md"
    if not gp.exists():
        return None
    text = gp.read_text(encoding="utf-8")
    m = re.search(rf"^###\s+Phase\s+{re.escape(str(phase))}\b.*?(?=^###\s|\Z)",
                  text, re.M | re.S)
    if not m:
        return None
    boxes = re.findall(r"^\s*-\s*\[( |x|X)\]", m.group(0), re.M)
    if not boxes:
        return None
    checked = sum(1 for b in boxes if b in "xX")
    return f"{checked}/{len(boxes)}"


def compute_stamp(paths: RepoPaths, config: Config) -> dict | None:
    """The live figure set, recomputed from canonical markdown per call.
    ``None`` on any failure — the stamp never invents and never breaks an op."""
    try:
        from . import revision
        from .rituals import _tables, status_bundle

        stamp: dict = {}
        rev = revision.read(paths.clauderizer_dir)
        if rev:
            stamp["revision"] = {"epoch": rev.get("epoch"),
                                 "revision": rev.get("revision")}
        gid = config.active_gameplan
        stamp["gameplan"] = gid or None
        if gid:
            gdir = paths.gameplan_dir(gid)
            rows = []
            for name in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
                p = gdir / name
                if p.exists():
                    rows = _tables.parse_phase_table(p.read_text(encoding="utf-8"))
                    if rows:
                        break
            cur = next((r for r in rows if r.status == "in_progress"), None)
            nxt = next((r for r in rows if r.status in ("ready", "not_started")), None)
            target = cur or nxt
            if target and rows:
                stamp["phase"] = f"{target.number}/{len(rows)}"
                stamp["phase_status"] = target.status
                crit = _raw_exit_criteria(gdir, target.number)
                if crit is not None:
                    stamp["exit_criteria"] = crit
            stamp["blockers"] = sum(1 for r in rows if r.status == "blocked")
            stamp["open_items"] = len(status_bundle.unresolved_open_items(gdir))
            stamp["pending_cascades"] = len(
                status_bundle.pending_cascades(gdir / "_cascade-reports"))
        assert set(stamp) <= FIGURE_KEYS
        return stamp
    except Exception:
        return None


def emit(paths: RepoPaths, config: Config) -> dict | None:
    """The change-triggered emission (INVARIANT-10 bound 2): the stamp, or
    ``None`` when the figure set is byte-equal to this session's last one."""
    global _last
    stamp = compute_stamp(paths, config)
    if stamp is None or stamp == _last:
        return None
    _last = dict(stamp)
    return stamp
