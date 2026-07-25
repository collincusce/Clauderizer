"""A symlinked PARENT directory redirects a write the leaf check cannot see (H-16).

The leaf guard refuses `docs/DECISIONS.md` when that file is a link. It says
nothing about `docs -> /tmp/evil`, under which every file is a perfectly ordinary
non-symlink — so the guard passes and the write lands outside the repo exactly as
if the leaf had been linked. Same escape, one level up.

Isolation is proved rather than assumed (L-29): each test asserts the write was
refused AND that nothing appeared at the link's destination.
"""

from __future__ import annotations

import pytest

from clauderizer.markdown import writer


@pytest.fixture
def planted(tmp_path):
    """A repo whose `docs` is a symlink to an attacker-chosen directory."""
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    (repo / "docs").symlink_to(outside, target_is_directory=True)
    return repo, outside


def test_write_through_a_symlinked_parent_is_refused(planted):
    repo, outside = planted
    with pytest.raises(OSError, match="symlinked directory"):
        writer.write_atomic(repo / "docs" / "DECISIONS.md", "# owned\n")
    assert list(outside.iterdir()) == [], "nothing may escape to the link target"


def test_a_deeper_ancestor_is_caught_too(planted):
    """The link need not be the immediate parent."""
    repo, outside = planted
    with pytest.raises(OSError, match="symlinked directory"):
        writer.write_atomic(repo / "docs" / "gameplans" / "gp" / "GAMEPLAN.md", "x\n")
    assert list(outside.iterdir()) == []


def test_the_error_names_the_link_not_just_the_file(planted):
    repo, _ = planted
    with pytest.raises(OSError) as exc:
        writer.write_atomic(repo / "docs" / "X.md", "x\n")
    msg = str(exc.value)
    assert str(repo / "docs") in msg, "name the directory the user must remove"
    assert "not a link" in msg, "explain why the leaf check looked clean"


def test_the_leaf_guard_still_works(tmp_path):
    """No regression in the 1.14.0 behavior this extends."""
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    (repo / "docs").mkdir(parents=True)
    outside.mkdir()
    (repo / "docs" / "D.md").symlink_to(outside / "D.md")
    with pytest.raises(OSError, match="through a symlink"):
        writer.write_atomic(repo / "docs" / "D.md", "x\n")
    assert not (outside / "D.md").exists()


def test_an_ordinary_write_is_untouched(tmp_path):
    """The common path must not acquire a false positive — this walks every
    ancestor to the filesystem root on every single write."""
    target = tmp_path / "repo" / "docs" / "OK.md"
    writer.write_atomic(target, "# fine\n")
    assert target.read_text(encoding="utf-8") == "# fine\n"


def test_a_tracked_mutation_inherits_the_guard(planted):
    """The guard must hold at the layer mutations actually use, not only when
    write_atomic is called directly."""
    repo, outside = planted
    with pytest.raises(OSError, match="symlinked directory"):
        writer.append_to_section(repo / "docs" / "LESSONS.md", "Lessons", "**L-01.** x")
    assert list(outside.iterdir()) == []
