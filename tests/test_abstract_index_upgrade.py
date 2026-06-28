"""Phase 6 of abstract-index-fast-retrieval: the upgrade path (D3).

init and reindex BUILD/refresh the abstract index idempotently; doctor DETECTS a
missing or schema-stale cache and advises reindex, read-only (never builds it —
INVARIANT-06; the runtime self-heals).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from clauderizer import cli
from clauderizer import paths as P
from clauderizer.graph import abstract_index as ai
from clauderizer.scaffold.init import init


def test_init_builds_abstract_index_and_gitignores(empty_python_repo):
    init(empty_python_repo, size="standard")
    paths = P.resolve(empty_python_repo)
    assert paths.abstract_index_file.exists()
    cache = json.loads(paths.abstract_index_file.read_text(encoding="utf-8"))
    assert cache["schema_version"] == ai.SCHEMA_VERSION
    assert ".clauderizer/abstract_index.json" in (empty_python_repo / ".gitignore").read_text(
        encoding="utf-8")
    assert ai.cache_status(paths) is None  # freshly built -> no drift


def test_reindex_builds_then_second_run_zero_diff(empty_python_repo, monkeypatch):
    init(empty_python_repo, size="standard")
    paths = P.resolve(empty_python_repo)
    paths.abstract_index_file.unlink()  # simulate a pre-upgrade repo (no cache)
    assert ai.cache_status(paths) is not None  # detected as missing

    monkeypatch.chdir(empty_python_repo)
    assert cli.cmd_reindex(argparse.Namespace()) == 0
    first = paths.abstract_index_file.read_text(encoding="utf-8")
    assert ai.cache_status(paths) is None

    # second-run-zero-diff: reindex is idempotent (byte-identical)
    assert cli.cmd_reindex(argparse.Namespace()) == 0
    assert paths.abstract_index_file.read_text(encoding="utf-8") == first


def test_cache_status_detects_missing_and_stale_without_writing(empty_python_repo):
    init(empty_python_repo, size="standard")
    paths = P.resolve(empty_python_repo)

    # missing -> flagged, and the detector does NOT create it (read-only)
    paths.abstract_index_file.unlink()
    reason = ai.cache_status(paths)
    assert reason and "missing" in reason
    assert not paths.abstract_index_file.exists()

    # schema-stale -> flagged
    ai.write_cache({"schema_version": 0, "corpus_mtime": 0.0, "entries": {}},
                   paths.abstract_index_file)
    reason = ai.cache_status(paths)
    assert reason and "schema" in reason

    # rebuilt -> fresh again
    ai.write_cache(ai.build(paths), paths.abstract_index_file)
    assert ai.cache_status(paths) is None


def test_doctor_flags_abstract_index_and_never_builds_it(empty_python_repo, monkeypatch, capsys):
    init(empty_python_repo, size="standard")
    paths = P.resolve(empty_python_repo)
    paths.abstract_index_file.unlink()
    monkeypatch.chdir(empty_python_repo)

    rc = cli.cmd_doctor(argparse.Namespace())
    out = capsys.readouterr().out
    assert "abstract index" in out                 # the check is surfaced
    assert "reindex" in out                         # with actionable advice
    assert not paths.abstract_index_file.exists()   # doctor is read-only — never built it
    assert rc != 0                                  # a missing cache is flagged (drift)
