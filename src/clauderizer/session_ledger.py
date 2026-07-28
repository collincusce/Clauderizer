"""Per-machine session evidence for heal-on-proof stranded-state detection (D-070).

An append-only, gitignored ``.clauderizer/sessions.jsonl``: when a phase
transitions to ``in_progress``, the writing process STAMPS one line of identity
evidence (pid, process start time, host, agent, transport). Later sessions can
then PROBE whether the claimant is still alive — turning "recorded in_progress"
from an assertion into a checkable claim.

Disposable per-machine evidence, never authority (D-067 / D-013): markdown
stays canonical, nothing here is ever auto-acted-on, and deleting the file
merely degrades detection to ``inconclusive``.

Heal-on-proof grading — only PROOF of death fires anything downstream:

  dead          same-host, mcp-transport stamp whose pid is gone
                (ProcessLookupError) or whose recorded /proc start time no
                longer matches the live process (PID reuse).
  alive         the pid answers signal-0 and, where measurable, its start time
                matches the stamp.
  inconclusive  everything unprovable: different host, cli/unknown transport
                (a CLI stamp's process legitimately exits immediately), no or
                corrupt stamp, unreadable /proc, non-posix platform.

POSIX gate (binding vetting condition, D-070): on non-posix platforms
``probe`` returns ``inconclusive`` WITHOUT any ``os.kill`` call — win32's
``os.kill`` delivers CTRL_C_EVENT/TerminateProcess, and a read path must never
be able to signal a live process. On POSIX, ``kill(pid, 0)`` performs only the
existence/permission check and delivers nothing.

The read side (``last_stamp``/``probe``) writes ZERO bytes anywhere — the
display-only contract is stranded.py's and is pinned by test.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

from .paths import RepoPaths

LEDGER = "sessions.jsonl"


def _proc_start_time(pid: int) -> str | None:
    """Linux ``/proc/<pid>/stat`` starttime (field 22), else ``None``.

    ``None`` is "unmeasurable here" (macOS, containers without /proc), never
    treated as a mismatch — no claim, not a fabricated one (D-070 epistemics).
    The comm field may contain spaces/parens, so fields count after the LAST
    ``)`` (field 3 onward); starttime is field 22 → index 19 there.
    """
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii", errors="replace")
        after = stat.rsplit(")", 1)[1].split()
        return after[19]
    except (OSError, IndexError, ValueError):
        return None


def _transport() -> str:
    """mcp | cli | unknown, from how this process was launched. Only ``mcp``
    stamps are probe-eligible: a long-lived server's death is evidence, while a
    ``clauderize ops`` CLI process exits by design the moment it returns."""
    name = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else ""
    if "clauderizer-mcp" in name:
        return "mcp"
    if name.startswith("clauderize"):
        return "cli"
    return "unknown"


def stamp(paths: RepoPaths, gameplan: str, phase: str,
          today: str | None = None) -> None:
    """Append this process's claim on ``(gameplan, phase)``. Best-effort and
    silent on any failure — identity bookkeeping must never fail a transition
    (the caller already holds the write lock)."""
    try:
        from .session import detect_session_agent

        pid = os.getpid()
        rec = {
            "kind": "session",
            "gameplan": gameplan,
            "phase": str(phase),
            "pid": pid,
            "start": _proc_start_time(pid),
            "host": socket.gethostname(),
            "agent": detect_session_agent(),
            "transport": _transport(),
            "at": today or "",
        }
        p = paths.clauderizer_dir / LEDGER
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    except Exception:
        pass


def last_stamp(paths: RepoPaths, gameplan: str, phase: str) -> dict | None:
    """The most recent stamp for ``(gameplan, phase)``, or ``None``. Tolerant of
    corrupt/partial lines (a torn append is "no evidence", never a crash)."""
    p = paths.clauderizer_dir / LEDGER
    if not p.exists():
        return None
    found: dict | None = None
    try:
        with open(p, encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if (isinstance(obj, dict) and obj.get("kind") == "session"
                        and obj.get("gameplan") == gameplan
                        and str(obj.get("phase")) == str(phase)):
                    found = obj
    except OSError:
        return None
    return found


def probe(entry: dict | None) -> str:
    """Grade a stamp: ``dead`` | ``alive`` | ``inconclusive`` (see module doc).

    Errs toward ``inconclusive``/``alive`` in every unprovable case — a wrong
    "dead" strands a healthy session, a wrong "alive" merely delays healing.
    """
    if not entry or entry.get("transport") != "mcp":
        return "inconclusive"
    if entry.get("host") != socket.gethostname():
        return "inconclusive"
    if os.name != "posix":
        return "inconclusive"       # never os.kill on win32 (CTRL_C_EVENT)
    pid = entry.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return "inconclusive"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "dead"
    except PermissionError:
        return "alive"              # exists, owned by another user
    except OSError:
        return "inconclusive"
    recorded = entry.get("start")
    if recorded:
        live = _proc_start_time(pid)
        if live is not None and live != recorded:
            return "dead"           # PID reused by a different process
    return "alive"
