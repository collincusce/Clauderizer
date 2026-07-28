"""Stranded-state detection — heal on proof, display only. (D-070, heal-on-proof)

Closes the gap :mod:`memory_lag` names in its own docstring as undetectable
from git alone: "a phase left marked in_progress long after it was really
finished is NOT detected, because git cannot distinguish 'still being worked
on' from 'done but unrecorded'". Git cannot — an OS-level liveness probe of
the process that CLAIMED the phase can. A phase is **stranded** when its
tracker row reads ``in_progress`` but the session that stamped that claim
(:mod:`clauderizer.session_ledger`) is provably dead on this same host.

DISPLAY-ONLY CONTRACT: the detect/read path writes ZERO bytes under ``docs/``
and ``.clauderizer/`` — ``sessions.jsonl`` is read here, never written, and no
finding is ever persisted. Detection surfaces a judgment menu; the AGENT
decides and every healing write goes through the blessed mutations
(``cz_transition_phase``). Pinned by test (test_stranded_state.py).

Heal on proof: ``alive`` and ``inconclusive`` grades heal nothing — only
provable death (same host, mcp transport, pid gone or start-time mismatch)
fires, never for this process itself, and parked states (blocked — including
PAUSED — and deferred) are never probed. Clauderizer lacks Fractal's
one-loop-per-node exclusivity, so anything short of proof stays silent
(binding vetting condition).

Advisory only (INVARIANT-05); read-only and exception-swallowed so a hook may
call it (INVARIANT-06) — the probe is a POSIX signal-0 check, no subprocess;
zero bytes in the digest when healthy (INVARIANT-08).
"""

from __future__ import annotations

import os

from .. import session_ledger
from ..paths import RepoPaths

# Only an ACTIVE claim is probed. Parked states assert "not being worked on"
# honestly already; probing them could only manufacture false urgency.
PROBED_STATES = frozenset({"in_progress"})


def detect(paths: RepoPaths, gid: str, target: dict | None,
           status: str | None) -> dict | None:
    """The stranded record for the gameplan's current phase, or ``None``.

    ``target``/``status`` are the digest's current-phase shape, exactly as
    :func:`memory_lag.detect` takes them. Returns
    ``{phase, name, pid, host, agent, started, grade}`` only on proof.
    """
    if not gid or not target or status not in PROBED_STATES:
        return None
    entry = session_ledger.last_stamp(paths, gid, str(target.get("number")))
    if not entry:
        return None                       # legacy repo / no stamp: no claim
    if entry.get("pid") == os.getpid():
        return None                       # never reconcile your own live session
    if session_ledger.probe(entry) != "dead":
        return None                       # alive or inconclusive heals nothing
    return {
        "phase": target.get("number"),
        "name": target.get("name"),
        "pid": entry.get("pid"),
        "host": entry.get("host"),
        "agent": entry.get("agent") or "unknown agent",
        "started": entry.get("at") or "date unknown",
        "grade": "dead",
    }


def describe(finding: dict) -> str:
    """The single judgment-menu wording every surface shares (L-55 seam) —
    digest, pre-flight and phase context can never word this differently."""
    return (
        f"phase {finding['phase']} \"{finding['name']}\" is recorded "
        f"in_progress, but the session that claimed it (pid {finding['pid']} on "
        f"{finding['host']}, {finding['agent']}, {finding['started']}) is dead — "
        f"stranded, not being worked on. Judgment menu: ADOPT it (continue the "
        f"work; re-stamp your claim with cz_transition_phase to in_progress — a "
        f"same-status transition is the blessed healing touch), or CLOSE it "
        f"honestly (cz_transition_phase to deferred with a reason; complete only "
        f"if its exit criteria are genuinely met). The engine never decides — "
        f"this is display, not enforcement."
    )
