"""Advisory inter-process write lock for tracked mutations (H-05, gameplan D1).

Every tracked doc mutation is read-modify-write markdown, and one MCP server
per session means a second window or subagent races appends and ID allocation
(H-05). This module serializes writers through ``.clauderizer/write.lock``:

- **Acquire** is an ``O_CREAT | O_EXCL`` create with holder metadata (pid,
  host, timestamps, a one-shot nonce) written inside — portable, no daemon,
  no platform-specific ``fcntl`` dependence.
- **Stale takeover**: a holder older than ``stale_timeout`` (default ~30s;
  mutations run in milliseconds) is presumed crashed. Takeover renames the
  stale file to a unique trash name — rename is atomic, so exactly one
  contender wins and nobody can double-``unlink`` a rival's fresh lock.
  After every create, the writer re-reads its own nonce; if a racing
  takeover stole the slot in the microseconds between judge and rename,
  the loser simply rejoins the queue instead of proceeding unlocked.
- **Contention** past ``acquire_timeout`` surfaces as :class:`LockHeld`,
  a clear, retryable error naming the holder.
- **Reentrant per thread**: mutations compose other mutations
  (``consolidate_lessons`` -> ``add_lesson``), so the lock counts depth per
  lock path and the file is created/removed only at the outermost level.
  Threads of one process serialize on the same per-path ``RLock``.

Read paths never touch this module (L-03): a context fetch must not block —
or be blocked by — a writer.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Resolved at call time (not bound at import), so tests and embedders can
# retune via the module attributes.
DEFAULT_ACQUIRE_TIMEOUT = 10.0
DEFAULT_STALE_TIMEOUT = 30.0
_POLL_INTERVAL = 0.05
# Release-time unlink can lose a race with a concurrent reader on Windows (see
# _release_file); retry it for about this long before falling back to takeover.
_RELEASE_UNLINK_ATTEMPTS = 40  # ~2s at _POLL_INTERVAL


class LockHeld(Exception):
    """The write lock is held by a live writer. Retry shortly.

    Attributes: ``lock_path``, ``holder`` (the metadata dict found in the
    lock file, or ``None`` if unreadable), ``waited`` (seconds spent
    waiting), ``retryable`` (always ``True`` — contention is transient).
    """

    retryable = True

    def __init__(self, lock_path: Path, holder: dict | None, waited: float):
        self.lock_path = lock_path
        self.holder = holder or {}
        self.waited = waited
        pid = self.holder.get("pid", "unknown")
        host = self.holder.get("host", "unknown host")
        since = self.holder.get("since", "unknown time")
        same = " (another thread in this process)" if pid == os.getpid() else ""
        super().__init__(
            f"write lock {lock_path} is held by pid {pid} on {host}{same} "
            f"since {since}; waited {waited:.1f}s. This is retryable — retry "
            f"shortly; a crashed holder is taken over automatically after "
            f"~{DEFAULT_STALE_TIMEOUT:.0f}s."
        )


class _PathState:
    """Per-process bookkeeping for one lock path: reentrancy + thread safety."""

    __slots__ = ("rlock", "depth", "nonce")

    def __init__(self) -> None:
        self.rlock = threading.RLock()
        self.depth = 0
        self.nonce: str | None = None


_states: dict[str, _PathState] = {}
_states_guard = threading.Lock()


def _state_for(lock_path: Path) -> _PathState:
    key = str(lock_path)
    with _states_guard:
        state = _states.get(key)
        if state is None:
            state = _states[key] = _PathState()
        return state


def read_holder(lock_path: Path) -> dict | None:
    """The holder metadata currently in the lock file, or ``None``.

    ``None`` covers both "no lock" and "unreadable/partial content" — a
    writer mid-create is judged by file mtime instead (see :func:`_age`).
    """
    try:
        return json.loads(Path(lock_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _age(lock_path: Path, holder: dict | None) -> float | None:
    """Seconds since the holder stamped the lock; ``None`` if it vanished."""
    ts = (holder or {}).get("ts")
    if isinstance(ts, (int, float)):
        return time.time() - ts
    try:
        return time.time() - os.stat(lock_path).st_mtime
    except OSError:
        return None


def _try_takeover(lock_path: Path, stale_timeout: float) -> bool:
    """Atomically remove the lock if (still) stale; ``True`` if removed."""
    holder = read_holder(lock_path)
    age = _age(lock_path, holder)
    if age is None or age < stale_timeout:
        return False
    trash = lock_path.with_name(
        f"{lock_path.name}.stale-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    )
    try:
        os.rename(lock_path, trash)
    except OSError:
        return False  # a rival takeover (or the holder's release) got there first
    try:
        os.unlink(trash)
    except OSError:
        pass
    return True


def _acquire_file(lock_path: Path, *, deadline: float, stale_timeout: float,
                  started: float) -> str:
    nonce = uuid.uuid4().hex
    payload = json.dumps(
        {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "since": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ts": time.time(),
            "nonce": nonce,
        }
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError) as exc:
            # POSIX raises FileExistsError for an O_EXCL create on an existing path;
            # Windows raises PermissionError (EACCES) for the same contention (another
            # process holds / is mid-creating the lock). A PermissionError with NO lock
            # file present is a genuine ACL failure (e.g. a read-only dir) — surface it.
            if isinstance(exc, PermissionError) and not lock_path.exists():
                raise
            if _try_takeover(lock_path, stale_timeout):
                continue
            if time.monotonic() >= deadline:
                raise LockHeld(lock_path, read_holder(lock_path),
                               time.monotonic() - started)
            time.sleep(_POLL_INTERVAL)
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
        except OSError:
            try:
                os.unlink(lock_path)
            except OSError:
                pass
            raise
        if (read_holder(lock_path) or {}).get("nonce") == nonce:
            return nonce
        # A racing stale-takeover misjudged our fresh lock and stole the
        # slot; we never held it, so rejoin the queue.
        if time.monotonic() >= deadline:
            raise LockHeld(lock_path, read_holder(lock_path),
                           time.monotonic() - started)
        time.sleep(_POLL_INTERVAL)


def _release_file(lock_path: Path, nonce: str | None) -> None:
    # On Windows os.unlink raises a sharing violation (PermissionError, an
    # OSError) if another process has the file open — and waiters poll
    # read_holder, holding it open for an instant on each poll. Swallowing that
    # error would orphan our lock and force every waiter onto the slow
    # ~stale_timeout takeover path (H-10). Retry briefly so the unlink lands in
    # a gap between reads. POSIX unlinks open files fine, so it returns on the
    # first attempt there. The nonce guard is re-checked each pass: if a stale
    # takeover claimed the slot mid-retry, the lock is no longer ours to remove.
    for _ in range(_RELEASE_UNLINK_ATTEMPTS):
        holder = read_holder(lock_path)
        if holder is not None and holder.get("nonce") != nonce:
            return  # taken over as stale while we held it — now somebody else's
        try:
            os.unlink(lock_path)
            return
        except FileNotFoundError:
            return  # already gone — a takeover removed it, or a prior pass won
        except OSError:
            time.sleep(_POLL_INTERVAL)
    # Exhausted (pathological): leave it for stale takeover — the existing net.


@contextmanager
def write_lock(lock_path: Path, *, acquire_timeout: float | None = None,
               stale_timeout: float | None = None):
    """Hold the advisory write lock at ``lock_path`` for one mutation.

    Blocks up to ``acquire_timeout`` total (polling, with stale takeover),
    then raises :class:`LockHeld`. Always releases on exception. Reentrant
    within a thread; threads of one process serialize on the same lock.
    """
    if acquire_timeout is None:
        acquire_timeout = DEFAULT_ACQUIRE_TIMEOUT
    if stale_timeout is None:
        stale_timeout = DEFAULT_STALE_TIMEOUT
    lock_path = Path(lock_path)
    state = _state_for(lock_path)
    started = time.monotonic()
    deadline = started + acquire_timeout
    if not state.rlock.acquire(timeout=acquire_timeout):
        raise LockHeld(lock_path, read_holder(lock_path),
                       time.monotonic() - started)
    try:
        if state.depth == 0:
            state.nonce = _acquire_file(
                lock_path, deadline=deadline,
                stale_timeout=stale_timeout, started=started,
            )
        state.depth += 1
        try:
            yield
        finally:
            state.depth -= 1
            if state.depth == 0:
                _release_file(lock_path, state.nonce)
                state.nonce = None
    finally:
        state.rlock.release()
