"""Doctor certifies engine IDENTITY, not mere presence (H-20 / D-060 / D-065).

These are H-20's own recorded regression tests. The finding was written by this
repo, with its recommended fix and its test list, and then three independent
planning drafts re-derived it from scratch instead of reading it — the failure
mode reproducing inside the meta-work.

The defect: ``hosts.verify_wiring`` on a native host is ``shutil.which(argv[0])``,
and ``cmd_doctor`` deliberately routed the PORTABLE shipped ``.mcp.json`` — the
config most consumers get — down that path. "MCP server launchable — uvx" meant
the string ``uvx`` resolved on PATH. Nothing was spawned. That green is what let
a repo run its hook on one engine while its MCP client was served another,
advertising five tools the server did not have.

Three-state contract throughout (D-010, D-048, INVARIANT-05, L-59): ok / fail /
``unverifiable`` **by name**. Never a silent green, never a pass for an awkward
host, and ``unverifiable`` is never rendered as a failure.
"""

from __future__ import annotations

import json

import pytest

from clauderizer import cli, hosttargets, mcp_probe
from clauderizer.scaffold.init import init


def _probe_result(status="ok", *, version="1.13.0", detail=None):
    return {
        "status": status,
        "detail": detail or f"initialize → serverInfo clauderizer {version}",
        "server_name": "clauderizer" if status == "ok" else None,
        "server_version": version if status == "ok" else None,
    }


@pytest.fixture(autouse=True)
def _enable_the_probe(monkeypatch):
    """This module is ABOUT the spawn probe, so it opts past the global guard."""
    monkeypatch.delenv("CLAUDERIZER_NO_SPAWN_PROBE", raising=False)
    cli._HANDSHAKE_CACHE.clear()


def _doctor(repo, monkeypatch, capsys, *args):
    monkeypatch.chdir(repo)
    rc = cli.main(["doctor", *args])
    return rc, capsys.readouterr().out


# --- H-20's recorded regression tests -----------------------------------------

def test_wiring_contract_fails_for_a_command_that_does_not_launch(empty_python_repo,
                                                                  monkeypatch):
    """H-20 test 1. Pre-fix this PASSED for all eleven auto-write hosts: the
    check was `any("clauderizer-mcp" in tok for tok in argv)`, a substring match
    on a config naming a command that need not exist."""
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    monkeypatch.setattr(mcp_probe, "handshake_probe",
                        lambda *a, **k: _probe_result("fail",
                                                      detail="command not found"))
    ok, detail = hosttargets.verify_emitted_wiring("cursor", empty_python_repo)
    assert ok is False, "a non-launching config passed the wiring contract"
    assert "does not launch" in detail


def test_wiring_contract_receives_the_expected_server_name(empty_python_repo,
                                                           monkeypatch):
    """H-20 test 2: the gate completes an initialize handshake and gets
    serverInfo.name == 'clauderizer' for at least one emitted config."""
    init(empty_python_repo, host_target="cursor", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    monkeypatch.setattr(mcp_probe, "handshake_probe", lambda *a, **k: _probe_result())
    ok, detail = hosttargets.verify_emitted_wiring("cursor", empty_python_repo)
    assert ok is True
    assert "serverInfo clauderizer" in detail


def test_cross_host_doc_matches_the_behaviour_that_ships(monkeypatch):
    """H-20 test 3, a claim-pin (L-62). CROSS-HOST called the contract a
    launch-and-round-trip proof while the code did a substring match."""
    from pathlib import Path
    doc = (Path(__file__).resolve().parents[1] / "docs" / "CROSS-HOST.md"
           ).read_text(encoding="utf-8")
    import inspect
    src = inspect.getsource(hosttargets.verify_emitted_wiring)
    launches = "handshake_probe" in src
    claims_launch = "the MCP server launches" in doc or "initialize" in doc
    assert launches == claims_launch, (
        "docs/CROSS-HOST.md section 7 and hosttargets.verify_emitted_wiring "
        "disagree about whether the wiring contract launches anything"
    )


def test_a_command_that_will_not_launch_is_never_green(empty_python_repo,
                                                       monkeypatch, capsys):
    """Pre-fix: '✓ MCP server launchable' + exit 0, from shutil.which alone."""
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe",
                        lambda *a, **k: _probe_result("fail", detail="exited 1"))
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "✓ MCP server identity" not in out
    assert rc != 0, "a dead MCP command still produced a clean doctor"


def test_a_version_skew_warns_and_exits_three(empty_python_repo, monkeypatch, capsys):
    """The engine split, made visible. Pre-fix with --deep: ✓ on all 9 hosts."""
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe",
                        lambda *a, **k: _probe_result(version="0.1.0"))
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "0.1.0" in out and "version" in out.lower()
    assert rc == 3, f"a served-vs-source skew must warn, not pass. rc={rc}"
    assert "✗" not in out, "a skew is a warning, not a failure"


def test_a_hanging_server_is_unverifiable_by_name_not_a_failure(empty_python_repo,
                                                                monkeypatch, capsys):
    """Timeout / cold cache / offline / proxy -> unverifiable, exit 3, no ✗."""
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setattr(mcp_probe, "handshake_probe",
                        lambda *a, **k: _probe_result("unverifiable",
                                                      detail="timed out after 8.0s"))
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    assert "unverifiable" in out
    assert rc == 3
    assert "✗ MCP server identity" not in out


def test_the_handshake_is_memoized_to_exactly_one_spawn(empty_python_repo,
                                                        monkeypatch, capsys):
    """All nine auto-write emitters share the identical portable entry, so
    --deep's nine identical handshakes must collapse to one."""
    init(empty_python_repo, spawn_test=False)
    calls: list = []

    def counting(entry, **kw):
        calls.append(tuple((entry or {}).get("args") or ()))
        return _probe_result()

    monkeypatch.setattr(mcp_probe, "handshake_probe", counting)
    _doctor(empty_python_repo, monkeypatch, capsys, "--deep")
    distinct = set(calls)
    assert len(calls) == len(distinct), (
        f"handshake ran {len(calls)} times for {len(distinct)} distinct "
        f"commands — the memo is not working"
    )


def test_the_probe_can_be_suppressed_and_says_so_rather_than_guessing(
        empty_python_repo, monkeypatch, capsys):
    """CLAUDERIZER_NO_SPAWN_PROBE returns 'skipped', NOT 'unverifiable'.

    "I was told not to look" is a different claim from "I looked and could not
    tell". Collapsing them is the evidence-traversal error this release fixes.
    """
    init(empty_python_repo, spawn_test=False)
    monkeypatch.setenv("CLAUDERIZER_NO_SPAWN_PROBE", "1")

    def explode(*a, **k):  # must never be reached
        raise AssertionError("the spawn probe ran despite being disabled")

    monkeypatch.setattr(mcp_probe, "handshake_probe", explode)
    rc, out = _doctor(empty_python_repo, monkeypatch, capsys)
    # Falls back to the presence check, so nothing is silently unchecked.
    assert "MCP server launchable for session host" in out
    assert rc == 0
