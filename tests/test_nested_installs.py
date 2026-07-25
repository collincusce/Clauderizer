"""Nested clauderized repos stop contradicting each other (H-23, Phase 1).

The live pathology: /home/ccusce is itself a clauderized repo containing
/home/ccusce/Clauderizer, so a session in the inner repo got TWO SessionStart
digests and the FIRST one announced "No active gameplan" about a repo that was
mid-release. It was the first thing in that session's context and it was read
past for the entire release.

The fix is ownership, decided fresh from the hook payload every event: for a
given session cwd exactly one install is the owner (the nearest clauderized
ancestor), and a non-owner stays silent. No flag, no file, nothing to fall out
of date (INVARIANT-05/08), and hooks stay read-only and exit 0 (INVARIANT-06).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from clauderizer import nesting
from clauderizer.hook import dispatch, handlers

FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture
def nested_pair(tmp_path: Path) -> tuple[Path, Path]:
    """``(outer, inner)`` — two clauderized repos, the inner nested in the outer.

    The outer is stripped of its gameplans so it renders the exact digest the
    live pathology produced: "[Clauderizer] No active gameplan." about a repo the
    session is not working in.
    """
    outer = tmp_path / "outer"
    shutil.copytree(FIXTURE, outer)
    shutil.rmtree(outer / "docs" / "gameplans")
    cfg = outer / ".clauderizer" / "config.toml"
    # `[active_gameplan]` is a TOML table, so drop the whole trailing section —
    # that is what makes the outer render the exact live line, "No active gameplan".
    cfg.write_text(cfg.read_text(encoding="utf-8").split("[active_gameplan]")[0],
                   encoding="utf-8")

    inner = outer / "projects" / "inner"
    inner.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE, inner)
    return outer, inner


def _session_start(anchored_at: Path, session_cwd: Path, monkeypatch) -> str | None:
    """Fire SessionStart the way the wrapper does: cwd anchored to the install's
    own repo, with the host's real session cwd in the payload."""
    monkeypatch.chdir(anchored_at)
    return handlers.session_start(
        {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(session_cwd)})


# --- the criterion: exactly one digest ----------------------------------------

def test_inner_speaks_and_outer_stays_silent(nested_pair, monkeypatch):
    outer, inner = nested_pair
    # Guard the fixture actually reproduces the pathology: the outer install,
    # left to itself, emits the exact "No active gameplan" line H-23 describes.
    monkeypatch.chdir(outer)
    assert "No active gameplan" in handlers.session_start(
        {"hook_event_name": "SessionStart"})

    assert _session_start(outer, inner, monkeypatch) is None, (
        "the outer install must not narrate a repo the session is not in")
    inner_digest = _session_start(inner, inner, monkeypatch)
    assert inner_digest and "[Clauderizer]" in inner_digest


def test_exactly_one_digest_reaches_the_session(nested_pair, monkeypatch):
    """The whole point, stated as the user experiences it."""
    outer, inner = nested_pair
    digests = [d for d in (_session_start(outer, inner, monkeypatch),
                           _session_start(inner, inner, monkeypatch)) if d]
    assert len(digests) == 1
    assert "No active gameplan" not in digests[0]


def test_outer_still_speaks_for_its_own_sessions(nested_pair, monkeypatch):
    """The silence is scoped to sessions the inner repo owns — not blanket."""
    outer, _inner = nested_pair
    assert _session_start(outer, outer, monkeypatch) is not None


def test_unrelated_session_cwd_is_unchanged(nested_pair, monkeypatch, tmp_path):
    """A session outside this repo entirely keeps 1.14.0 behavior — silencing it
    would regress anyone who wired a hook globally on purpose (INVARIANT-07)."""
    outer, _inner = nested_pair
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert _session_start(outer, elsewhere, monkeypatch) is not None


def test_no_payload_cwd_is_unchanged(nested_pair, monkeypatch):
    """A host that sends no cwd makes no ownership claim: behave as before."""
    outer, _inner = nested_pair
    monkeypatch.chdir(outer)
    assert handlers.session_start({"hook_event_name": "SessionStart"}) is not None


def test_every_event_honors_ownership(nested_pair, monkeypatch):
    """Not just SessionStart — the outer install must stay out of the way on the
    prompt and compaction events too, or it re-enters context by another door."""
    outer, inner = nested_pair
    monkeypatch.chdir(outer)
    payload = {"cwd": str(inner), "prompt": "should the login feature change?"}
    assert handlers.user_prompt_submit({**payload, "hook_event_name": "UserPromptSubmit"}) is None
    assert handlers.pre_compact({**payload, "hook_event_name": "PreCompact"}) is None
    assert handlers.post_compact({**payload, "hook_event_name": "PostCompact"}) is None


def test_hook_exits_zero_and_prints_nothing_when_outranked(
        nested_pair, monkeypatch, capsys):
    """INVARIANT-06/04 end to end: through the real dispatcher, silence is empty
    stdout AND exit 0 — never a crash the wrapper would turn into a breadcrumb."""
    outer, inner = nested_pair
    monkeypatch.chdir(outer)
    payload = json.dumps({"hook_event_name": "SessionStart", "cwd": str(inner)})
    monkeypatch.setattr("sys.stdin", type("S", (), {"buffer": type(
        "B", (), {"read": staticmethod(lambda: payload.encode())})()})())
    assert dispatch.main([]) == 0
    assert capsys.readouterr().out == ""


def test_ownership_is_not_persisted(nested_pair, monkeypatch):
    """No flag, no file: firing twice must give the same answer both times, and
    nothing may appear on disk to remember it (INVARIANT-05/08)."""
    outer, inner = nested_pair
    before = sorted(p.name for p in (outer / ".clauderizer").iterdir())
    assert _session_start(outer, inner, monkeypatch) is None
    assert _session_start(outer, inner, monkeypatch) is None
    assert sorted(p.name for p in (outer / ".clauderizer").iterdir()) == before


# --- the primitives -----------------------------------------------------------

def test_owner_is_the_nearest_clauderized_ancestor(nested_pair):
    outer, inner = nested_pair
    deep = inner / "src" / "deep"
    deep.mkdir(parents=True)
    assert nesting.owner_of(deep) == inner.resolve()
    assert nesting.owner_of(outer / "docs") == outer.resolve()
    assert nesting.owner_of(None) is None


def test_nested_installs_finds_the_inner_repo(nested_pair):
    outer, inner = nested_pair
    assert nesting.nested_installs(outer) == [inner.resolve()]
    assert nesting.nested_installs(inner) == []


def test_nested_scan_does_not_descend_into_a_found_install(nested_pair):
    """An install nested inside an install is reported once, at the outermost
    level — the finding is the install, not its whole subtree."""
    outer, inner = nested_pair
    deeper = inner / "sub"
    shutil.copytree(FIXTURE, deeper)
    assert nesting.nested_installs(outer) == [inner.resolve()]


def test_clauderized_ancestors(nested_pair):
    outer, inner = nested_pair
    assert nesting.clauderized_ancestors(inner) == [outer.resolve()]
    assert nesting.clauderized_ancestors(outer) == []


# --- doctor names it, init warns ----------------------------------------------

def test_doctor_names_the_nested_install_by_path(nested_pair, monkeypatch, capsys):
    outer, inner = nested_pair
    monkeypatch.chdir(outer)
    from clauderizer import cli

    cli.cmd_doctor(type("A", (), {"deep": False})())
    out = capsys.readouterr().out
    assert "nested clauderized install" in out
    assert str(inner.relative_to(outer.resolve())) in out


def test_doctor_from_inside_names_the_ancestor(nested_pair, monkeypatch, capsys):
    outer, inner = nested_pair
    monkeypatch.chdir(inner)
    from clauderizer import cli

    cli.cmd_doctor(type("A", (), {"deep": False})())
    assert "clauderized ancestor" in capsys.readouterr().out


def test_init_warns_before_creating_a_second_install(nested_pair, tmp_path):
    """Warns and proceeds — nesting is supported, just never silent."""
    outer, _inner = nested_pair
    fresh = outer / "projects" / "fresh"
    fresh.mkdir(parents=True)
    from clauderizer.scaffold.init import init

    report = init(fresh, spawn_test=False)
    assert any("inside an existing clauderized repo" in w for w in report.warnings)
    assert (fresh / ".clauderizer" / "config.toml").exists(), "it must still install"


def test_init_on_a_standalone_repo_does_not_warn(tmp_path):
    from clauderizer.scaffold.init import init

    report = init(tmp_path / "solo", spawn_test=False)
    assert not any("clauderized repo" in w for w in report.warnings)
