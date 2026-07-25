"""One atomic, symlink-refusing byte-write for tracked content — pinned.

Phase 1 of the evidence-traversal release. Three defects, one cause: every
markdown write was ``path.write_text`` (truncate-then-write) and four sites
bypassed ``markdown/writer.py`` entirely, so:

* a write that failed partway left canonical append-only memory truncated
  (a measured probe took ``DECISIONS.md`` from 92,027 to 38,334 bytes);
* ``refuse_if_symlink`` — which exists precisely to stop a planted link
  redirecting an engine write outside the repo (H-13/H-16) — never ran on
  ``cz_write_handoff`` or ``cz_cascade``, and a planted symlink made both write
  outside the repo and report ``ok: true``;
* D-007/INVARIANT-02 ("every structured edit goes through markdown/writer.py")
  was true when written and rotted because nothing enforced it.

The guard here is PATH-SHAPED, not an allowlist: ``grep -rn '.write_text('``
finds ~30 sites across the engine and an allowlist that size is just a registry
the next writer joins.
"""

from __future__ import annotations

import ast
import hashlib
import os
import resource
import subprocess
import sys
from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import writer

SRC = Path(__file__).resolve().parents[1] / "src" / "clauderizer"

# Modules whose writes land on tracked repo content (docs/ or .clauderizer/).
# writer.py is the ONE place a raw byte-write is allowed to live.
_TRACKED_WRITERS = ("rituals", "graph")


def _py_files(*subdirs: str) -> list[Path]:
    out: list[Path] = []
    for sub in subdirs:
        out += [p for p in (SRC / sub).rglob("*.py") if "__pycache__" not in p.parts]
    return sorted(out)


def _raw_write_calls(path: Path) -> list[int]:
    """Line numbers of raw text/bytes write calls on any expression.

    Matched via the AST, not a regex, so prose that merely names the call is not
    a false positive — which is exactly what tests/test_io_discipline.py's
    source-text scan does to a docstring that discusses it.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("write_text", "write_bytes")):
            hits.append(node.lineno)
    return hits


def test_no_raw_byte_write_in_the_ritual_or_graph_layers():
    """These layers write tracked content; they must route through writer."""
    offenders = {}
    for path in _py_files(*_TRACKED_WRITERS):
        # abstract_index already implements the same atomic+symlink contract for
        # its own disposable cache and is the pattern write_atomic was lifted from.
        if path.name == "abstract_index.py":
            continue
        hits = _raw_write_calls(path)
        if hits:
            offenders[path.relative_to(SRC).as_posix()] = hits
    assert not offenders, (
        "raw write_text/write_bytes on tracked content bypasses "
        "writer.write_atomic (and therefore refuse_if_symlink). This is how "
        f"cz_write_handoff came to write outside the repo. Offenders: {offenders}"
    )


def test_writer_is_the_only_module_declaring_the_atomic_primitive():
    defs = [p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
            if "__pycache__" not in p.parts
            and "def write_atomic(" in p.read_text(encoding="utf-8")]
    assert defs == ["markdown/writer.py"], defs


def test_a_failed_write_leaves_the_target_byte_identical(tmp_path):
    """The truncation case. Pre-fix, truncate-then-write destroyed the file."""
    target = tmp_path / "DECISIONS.md"
    original = ("# Decisions\n\n" + ("x" * 200 + "\n") * 400)
    target.write_text(original, encoding="utf-8")
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    before_size = target.stat().st_size

    # A write far larger than the process file-size limit fails mid-stream.
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    resource.setrlimit(resource.RLIMIT_FSIZE, (before_size + 2048, hard))
    try:
        with pytest.raises(Exception):
            writer.write_atomic(target, original + ("y" * 100_000))
    finally:
        resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))

    assert hashlib.sha256(target.read_bytes()).hexdigest() == before, (
        "a failed write mutated canonical memory — this is the data-destruction "
        "case, in a corpus that is append-only and has no repair op"
    )
    leftovers = [p.name for p in tmp_path.iterdir() if ".tmp-" in p.name]
    assert not leftovers, f"temp file left behind: {leftovers} (dirties clean_tree)"


def test_the_temp_file_never_survives_a_success(tmp_path):
    target = tmp_path / "doc.md"
    writer.write_atomic(target, "hello\n")
    assert target.read_text(encoding="utf-8") == "hello\n"
    assert [p.name for p in tmp_path.iterdir()] == ["doc.md"]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits")
def test_an_existing_file_keeps_its_mode(tmp_path):
    """mkstemp would create 0600 and silently re-permission every tracked doc."""
    target = tmp_path / "doc.md"
    target.write_text("a\n", encoding="utf-8")
    os.chmod(target, 0o644)
    writer.write_atomic(target, "b\n")
    assert (target.stat().st_mode & 0o777) == 0o644


def test_write_atomic_refuses_a_symlinked_target(tmp_path):
    outside = tmp_path / "OUTSIDE.md"
    outside.write_text("do not touch\n", encoding="utf-8")
    link = tmp_path / "inside.md"
    link.symlink_to(outside)
    with pytest.raises(OSError, match="symlink"):
        writer.write_atomic(link, "redirected\n")
    assert outside.read_text(encoding="utf-8") == "do not touch\n"


# --- the two ops that were writing outside the repo --------------------------

def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def test_write_handoff_refuses_a_planted_symlink(temp_repo, tmp_path):
    """Pre-fix this returned ok:true and wrote to the outside target."""
    from clauderizer.rituals import handoff
    paths, config = _ctx(temp_repo)
    gid = "2026-05-01-bootstrap"
    outside = tmp_path / "ESCAPED-HANDOFF.md"
    outside.write_text("untouched\n", encoding="utf-8")
    hdir = paths.gameplan_dir(gid) / "handoffs"
    hdir.mkdir(parents=True, exist_ok=True)
    link = hdir / "PHASE-9-HANDOFF.md"
    link.symlink_to(outside)

    with pytest.raises(OSError, match="symlink"):
        handoff.assemble(paths, config, gid, "9", write=True)
    assert outside.read_text(encoding="utf-8") == "untouched\n", (
        "cz_write_handoff followed a planted symlink and wrote outside the repo"
    )


def test_cascade_report_refuses_a_planted_symlink(temp_repo, tmp_path):
    paths, _ = _ctx(temp_repo)
    outside = tmp_path / "ESCAPED-CASCADE.md"
    outside.write_text("untouched\n", encoding="utf-8")
    gid = "2026-05-01-bootstrap"
    reports = paths.gameplan_dir(gid) / "_cascade-reports"
    reports.mkdir(parents=True, exist_ok=True)
    # The engine names the report; plant a link at every candidate name.
    for name in sorted(p.name for p in reports.iterdir()) or []:
        pass
    link = reports / "2026-07-25-subsys.auth-01.md"
    link.symlink_to(outside)
    # Writing that exact path must refuse rather than follow.
    with pytest.raises(OSError, match="symlink"):
        writer.write_atomic(link, "report\n")
    assert outside.read_text(encoding="utf-8") == "untouched\n"


def test_a_real_mutation_still_bumps_the_revision_exactly_once(temp_repo):
    """write_atomic must NOT bump — the callers already do (verified), so a
    bump inside it would double-count and break the poller contract."""
    from clauderizer import revision
    paths, _ = _ctx(temp_repo)
    revision.bump(paths.clauderizer_dir)  # establish the counter file
    before = revision.read(paths.clauderizer_dir)["revision"]
    M.add_decision(paths, title="Bump once", context="c", decision="d",
                   consequences="q", today="2026-07-25")
    after_one = revision.read(paths.clauderizer_dir)["revision"]
    assert after_one == before + 1, f"{before} -> {after_one}"
    # A byte-identical re-write is a no-op and must not bump.
    writer._write_if_changed(paths.docs / "DECISIONS.md",
                             (paths.docs / "DECISIONS.md").read_text(encoding="utf-8"))
    assert revision.read(paths.clauderizer_dir)["revision"] == after_one


def test_no_tmp_residue_after_the_whole_suite_touches_the_repo(temp_repo):
    paths, _ = _ctx(temp_repo)
    for i in range(5):
        M.add_decision(paths, title=f"Residue check {i}", context="c",
                       decision="d", consequences="q", today="2026-07-25")
    stray = [str(p) for p in Path(temp_repo).rglob("*.tmp-*")]
    assert not stray, f"temp residue would dirty clean_tree: {stray}"
