"""The advisory write lock (H-05, agent-autonomy D1).

The load-bearing test is the multi-process contention run: N real writer
processes race ``add_lesson`` on one repo and must produce N distinct
sequential numbers and N surviving entries. The rest pin the lock's contract:
stale takeover bounded by the timeout, the retryable ``LockHeld`` shape,
release-on-exception, and per-process reentrancy.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time

import pytest

from clauderizer import locking, paths as P
from clauderizer import mutations as M
from clauderizer.markdown import sections

GID = "2026-05-01-bootstrap"

N_WRITERS = 8

# Children block on a GO sentinel so all writers collide inside the same
# fraction of a second instead of being serialized by interpreter startup.
CHILD_SCRIPT = """\
import pathlib, sys, time

from clauderizer import locking, mutations, paths

# CI hardening (does NOT relax what this test checks). On a slow, contended
# runner (observed: windows-latest) a writer that has finished can briefly fail
# to unlink its own lock file -- on Windows os.unlink raises a sharing violation
# while another waiter is mid-read of the same file -- leaving the lock orphaned.
# Waiters then recover it only via stale takeover at ~stale_timeout (30s). So the
# per-child ACQUIRE budget must exceed the stale window with room to spare, or a
# waiter gives up at the exact moment takeover becomes possible (seen as repeated
# "waited Ns" LockHeld; the default 10s never reaches the 30s takeover at all).
# Widen ONLY the acquire budget, far above the 30s stale window; stale_timeout
# stays at the engine default so a live holder is never wrongly taken over. The
# H-05 contract (none lost, ids sequential) is unchanged -- only the wall-clock
# budget. add_lesson locks with no explicit kwargs, so it reads this global; the
# engine defaults shipped in src/ are untouched.
locking.DEFAULT_ACQUIRE_TIMEOUT = 120.0

repo = pathlib.Path(sys.argv[1])
idx = sys.argv[2]
go = repo / "GO"
deadline = time.time() + 20
while not go.exists():
    if time.time() > deadline:
        sys.exit(3)
    time.sleep(0.005)
r = mutations.add_lesson(
    paths.resolve(repo),
    gameplan_id="2026-05-01-bootstrap",
    text="concurrent lesson from child " + idx,
    category="Process",
)
print(r["number"])
"""


def _write_foreign_lock(lock_path, *, pid=999999, age=0.0):
    """A lock file owned by nobody alive — pid is foreign, ts is now - age."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps({
            "pid": pid,
            "host": "elsewhere",
            "since": "2026-01-01T00:00:00+00:00",
            "ts": time.time() - age,
            "nonce": "f" * 32,
        }),
        encoding="utf-8",
    )


def test_concurrent_writer_processes_lose_nothing(temp_repo, tmp_path):
    """H-05 regression: N racing writer processes -> N sequential ids, N entries."""
    script = tmp_path / "child_add_lesson.py"
    script.write_text(CHILD_SCRIPT, encoding="utf-8")
    procs = [
        subprocess.Popen(
            [sys.executable, str(script), str(temp_repo), str(i)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for i in range(N_WRITERS)
    ]
    (temp_repo / "GO").write_text("", encoding="utf-8")
    # Above the child acquire budget (120s) so the parent never reaps a child
    # that is legitimately waiting out a stale-takeover cycle.
    results = [p.communicate(timeout=240) for p in procs]
    failures = [(p.returncode, out, err) for p, (out, err) in zip(procs, results)
                if p.returncode != 0]
    assert not failures, f"writer children failed: {failures}"

    # N distinct, strictly sequential ids — no duplicate allocation.
    numbers = sorted(int(out.strip()) for out, _ in results)
    assert numbers == list(range(numbers[0], numbers[0] + N_WRITERS))

    # Every append survived — no lost update.
    idx = temp_repo / "docs" / "gameplans" / GID / "CHAT-HANDOFF-INDEX.md"
    text = idx.read_text(encoding="utf-8")
    for i in range(N_WRITERS):
        assert f"concurrent lesson from child {i}" in text

    # And the lessons section as a whole has no duplicated numbers.
    body = sections.get_section(text, "Accumulated Lessons")
    all_nums = [int(m.group(1)) for m in re.finditer(r"^\s*\*\*(\d+)\.\*\*", body, re.M)]
    assert len(all_nums) == len(set(all_nums))


def test_stale_lock_taken_over(tmp_path):
    lock = tmp_path / ".clauderizer" / "write.lock"
    _write_foreign_lock(lock, age=3600.0)
    t0 = time.monotonic()
    with locking.write_lock(lock, acquire_timeout=5.0, stale_timeout=30.0):
        holder = locking.read_holder(lock)
        assert holder["pid"] == os.getpid()  # the stale holder was replaced
    assert time.monotonic() - t0 < 2.0  # takeover, not a timeout wait
    assert not lock.exists()


def test_crashed_holder_blocks_at_most_stale_timeout(tmp_path):
    """Exit criterion: a crashed holder delays a writer no longer than stale_timeout."""
    lock = tmp_path / ".clauderizer" / "write.lock"
    # Start the clock BEFORE creating the lock. The staleness clock is the lock's
    # own `ts` (stamped inside _write_foreign_lock); takeover fires at ts +
    # stale_timeout. Measuring from *after* creation let a slow write under load
    # sit between ts and t0 and shrink `waited` below the lower bound (observed
    # 0.20s < 0.4s under full-suite load). With t0 <= ts, `waited` can only
    # over-estimate the true stale wait, never under-estimate it.
    t0 = time.monotonic()
    _write_foreign_lock(lock, age=0.0)  # fresh-looking, but its process is gone
    with locking.write_lock(lock, acquire_timeout=10.0, stale_timeout=0.6):
        pass
    waited = time.monotonic() - t0
    assert 0.4 <= waited < 5.0


def test_lock_held_error_shape(tmp_path):
    lock = tmp_path / ".clauderizer" / "write.lock"
    _write_foreign_lock(lock, pid=999999, age=0.0)
    with pytest.raises(locking.LockHeld) as ei:
        with locking.write_lock(lock, acquire_timeout=0.3, stale_timeout=60.0):
            pass
    e = ei.value
    assert e.retryable is True
    assert e.holder["pid"] == 999999
    assert e.lock_path == lock
    assert e.waited >= 0.3
    msg = str(e)
    assert "999999" in msg and "elsewhere" in msg and "retry" in msg.lower()
    assert lock.exists()  # a live holder's lock is never disturbed


def test_lock_released_on_exception(tmp_path):
    lock = tmp_path / ".clauderizer" / "write.lock"
    with pytest.raises(RuntimeError):
        with locking.write_lock(lock):
            assert lock.exists()
            raise RuntimeError("boom")
    assert not lock.exists()
    with locking.write_lock(lock, acquire_timeout=0.5):  # immediately reacquirable
        pass


def test_reentrant_within_a_thread(tmp_path):
    lock = tmp_path / ".clauderizer" / "write.lock"
    with locking.write_lock(lock):
        with locking.write_lock(lock):  # composed mutations take the lock once
            assert lock.exists()
        assert lock.exists()  # inner exit keeps the outer hold
    assert not lock.exists()


def test_threads_of_one_process_serialize(tmp_path):
    lock = tmp_path / ".clauderizer" / "write.lock"
    order = []
    entered = threading.Event()

    def worker():
        with locking.write_lock(lock):
            entered.set()
            time.sleep(0.3)
            order.append("worker-out")

    t = threading.Thread(target=worker)
    t.start()
    assert entered.wait(5.0)
    with locking.write_lock(lock, acquire_timeout=5.0):
        order.append("main-in")
    t.join()
    assert order == ["worker-out", "main-in"]


def test_mutation_surfaces_lock_held(temp_repo, monkeypatch):
    """A fresh foreign lock makes a mutation fail fast with the holder named."""
    paths = P.resolve(temp_repo)
    _write_foreign_lock(paths.write_lock_file, pid=424242, age=0.0)
    monkeypatch.setattr(locking, "DEFAULT_ACQUIRE_TIMEOUT", 0.2)
    with pytest.raises(locking.LockHeld) as ei:
        M.add_lesson(paths, gameplan_id=GID, text="blocked write")
    assert ei.value.holder["pid"] == 424242


def test_mutation_leaves_no_lock_behind(temp_repo):
    paths = P.resolve(temp_repo)
    r = M.add_lesson(paths, gameplan_id=GID, text="locked path works")
    assert r["ok"]
    assert not paths.write_lock_file.exists()
