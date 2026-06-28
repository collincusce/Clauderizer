"""Behavioral read-only gate (D1, #3).

The per-op ``assert REGISTRY[x].writes is False`` + ``fn.__name__ == x`` tests were
tautologies: they assert module-load constants and pass regardless of what the op
does at runtime. Registration + name parity is already the single test_ops.py gate
(REGISTRY == TOOL_NAMES + the AST signature-drift guard). What was NOT proven was
the *behavior* the ``writes`` flag claims — that the op leaves canonical state
untouched. This test exercises it: run each declared-read-only op against a seeded
repo and assert every tracked file is byte-identical afterward (the
test_hook_dispatch read-only-snapshot pattern). Only the gitignored disposable
cache / lock may change (INVARIANT-01)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import ops


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


# A READ may legitimately (re)build these — disposable caches, the write lock,
# python bytecode — so they are excluded from the "tracked file" snapshot. Anything
# else changing means the op was not actually read-only.
_DISPOSABLE = {"index.json", "abstract_index.json", "telemetry.jsonl", "write.lock"}


def _snapshot(root: Path) -> dict:
    snap = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.name in _DISPOSABLE or p.suffix == ".pyc":
            continue
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        snap[str(p.relative_to(root))] = p.read_bytes()
    return snap


# Declared writes=False ops that take no required args (cz_get needs an id, run
# separately). These include the five whose tautological tests this replaces:
# cz_lesson_health, cz_curate, cz_loop_step, cz_discover_skills (+ cz_get).
_READ_OPS_NO_ARGS = [
    "cz_status", "cz_corpus_health", "cz_lesson_health", "cz_curate",
    "cz_loop_step", "cz_discover_skills", "cz_gameplans",
]


def test_declared_read_only_ops_mutate_no_tracked_files(temp_repo):
    with _chdir(temp_repo):
        before = _snapshot(temp_repo)
        for name in _READ_OPS_NO_ARGS:
            spec = ops.REGISTRY[name]
            assert spec.writes is False, f"{name} is not declared read-only"
            result = spec.fn()
            assert result.get("ok", True) is not False, f"{name} errored: {result}"
        # cz_get needs an id; the fixture ships D-001.
        got = ops.cz_get("D-001")
        assert got["ok"] and got["id"] == "D-001"
        after = _snapshot(temp_repo)

    assert before == after, (
        "a declared-read-only op mutated a tracked file — the writes=False flag is a "
        "lie at runtime (changed: "
        f"{sorted(set(before) ^ set(after)) or [k for k in before if before[k] != after.get(k)]})"
    )
