"""The process says when it is not the build the working tree describes (H-27).

Distinct from tests/test_engine_identity.py, which covers H-20: whether some
OTHER registered command is launchable, answered by spawning it. This is the
reflexive question — is the process *executing this code* the one this repo's
source describes — which needs no spawn at all.

Measured live 2026-07-25: `.mcp.json` wires `uvx --from clauderizer[mcp]`, so
every cz_* write in a session that edited the engine ran the PUBLISHED build
while the fix sat green in the working tree. A write guard was authored, tested
and committed, and executed for zero tool writes that day — found only when a
malformed call produced exactly the corruption it exists to prevent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from clauderizer import config as cfg
from clauderizer import engine_identity as eid
from clauderizer import paths as P
from clauderizer.rituals import status_bundle as S

REPO_ROOT = Path(__file__).resolve().parents[1]
UVX_LIKE = "/home/u/.cache/uv/archive-v0/FCYnO1Z/lib/python3.12/site-packages/clauderizer/__init__.py"


def _src_repo(tmp_path: Path, version: str = "1.14.2") -> Path:
    """A repo that CONTAINS the engine's source — i.e. one where the question
    'am I running this?' is meaningful at all."""
    repo = tmp_path / "engine"
    pkg = repo / "src" / "clauderizer"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    return repo


# --- the primitive -------------------------------------------------------------

def test_silent_for_an_ordinary_consumer_repo(tmp_path):
    """No src/clauderizer means nothing to compare — the overwhelmingly common
    case must produce no claim at all."""
    repo = tmp_path / "consumer"
    (repo / "docs").mkdir(parents=True)
    assert eid.serving_build(P.resolve(repo), module_file=UVX_LIKE,
                             running_version="1.14.1") is None


def test_silent_when_the_process_is_running_the_tree(tmp_path):
    repo = _src_repo(tmp_path)
    running = repo / "src" / "clauderizer" / "__init__.py"
    assert eid.serving_build(P.resolve(repo), module_file=running,
                             running_version="1.14.2") is None


def test_the_uvx_case_fires_and_names_both_sides(tmp_path):
    """The case that actually happened: served from uv's cache, tree elsewhere."""
    repo = _src_repo(tmp_path, version="1.14.2")
    m = eid.serving_build(P.resolve(repo), module_file=UVX_LIKE,
                          running_version="1.14.1")
    assert m is not None
    assert "uv/archive-v0" in m["serving_path"]
    assert m["serving_version"] == "1.14.1"
    assert m["tree_version"] == "1.14.2"
    assert str(repo.resolve()) in m["tree_path"]


def test_it_fires_even_when_the_versions_agree(tmp_path):
    """The nastiest shape: same version string, different build — precisely the
    situation during 1.14.1's development. A version-only check calls this
    healthy; the PATH is what disambiguates."""
    repo = _src_repo(tmp_path, version="1.14.1")
    m = eid.serving_build(P.resolve(repo), module_file=UVX_LIKE,
                          running_version="1.14.1")
    assert m is not None
    assert "both report 1.14.1" in eid.describe(m)


def test_describe_names_the_remedy(tmp_path):
    repo = _src_repo(tmp_path)
    text = eid.describe(eid.serving_build(P.resolve(repo), module_file=UVX_LIKE,
                                          running_version="1.14.1"))
    assert "clauderize ops" in text, "name the fresh-process path that does work"
    assert "NOT running this repo's source" in text


def test_tree_version_is_read_as_text_not_imported(tmp_path):
    """Importing would re-import the RUNNING module and compare it to itself."""
    repo = _src_repo(tmp_path, version="9.9.9")
    assert eid.tree_version(P.resolve(repo)) == "9.9.9"


@pytest.mark.parametrize("payload", ["", "no version here\n", "__version__ = \n"])
def test_unreadable_tree_version_degrades_to_none(tmp_path, payload):
    repo = tmp_path / "engine"
    pkg = repo / "src" / "clauderizer"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(payload, encoding="utf-8")
    assert eid.tree_version(P.resolve(repo)) is None
    # Still fires on the path mismatch — a missing version must not silence it.
    assert eid.serving_build(P.resolve(repo), module_file=UVX_LIKE,
                             running_version="1.14.1") is not None


# --- the gap this exists for --------------------------------------------------

def test_the_mtime_check_is_blind_to_this_and_that_is_the_point():
    """engine_source_newer_than answers 'did my files change since I started',
    not 'am I the right build'. For an INSTALLED package its own docstring notes
    mtimes are install-time, so it cannot fire for the H-27 situation. Pinned so
    nobody mistakes tightening THAT check for fixing this one."""
    import time
    assert S.engine_source_newer_than(time.time() + 3600) is False


# --- the digest surface -------------------------------------------------------

def test_digest_emits_the_line_when_the_build_is_wrong(temp_repo, monkeypatch):
    pkg = temp_repo / "src" / "clauderizer"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    real = eid.serving_build
    monkeypatch.setattr(eid, "serving_build",
                        lambda paths, **kw: real(paths, module_file=UVX_LIKE,
                                                 running_version="1.14.1"))
    paths = P.resolve(temp_repo)
    bundle = S.compute(paths, cfg.Config.load(paths.config_file))
    assert bundle.get("engine_identity")
    digest = S.render_digest(bundle)
    assert "⚠ Engine identity:" in digest
    assert "uv/archive-v0" in digest


def test_digest_is_byte_identical_when_there_is_nothing_to_say(temp_repo):
    """INVARIANT-08: a repo with no engine source renders exactly as before."""
    paths = P.resolve(temp_repo)
    bundle = S.compute(paths, cfg.Config.load(paths.config_file))
    assert "engine_identity" not in bundle
    assert "Engine identity" not in S.render_digest(bundle)


def test_this_repo_running_its_own_source_is_silent():
    """Live: the suite runs from src/, so the engine must not flag itself — a
    false positive here would be noise on every contributor's every session."""
    m = eid.serving_build(P.resolve(REPO_ROOT))
    assert m is None, f"false positive against the working tree: {m}"
