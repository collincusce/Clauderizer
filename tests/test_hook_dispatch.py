"""Phase 1 (kimi-lifecycle-integration): the event-dispatching hook engine.

Covers D-025 / INVARIANT-06: one entry dispatches on hook_event_name to read-only
handlers, always exits 0, preserves the --version identity probe, and falls back
to the SessionStart digest on empty/garbage stdin (the backward-compatible shape
the hardened no-arg digest probe sends). Input tolerance is exercised against the
diverse-malformed corpus L-18/L-19 demand.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from clauderizer import __version__
from clauderizer.hook import dispatch, handlers, sessionstart
from clauderizer.scaffold.init import init


class FakeStdin:
    """Minimal stand-in for sys.stdin exposing the .buffer byte stream dispatch reads."""

    def __init__(self, data: bytes):
        self.buffer = io.BytesIO(data)


def run(monkeypatch, capsys, *, argv=None, stdin: bytes = b"") -> tuple[int, str]:
    monkeypatch.setattr(dispatch.sys, "stdin", FakeStdin(stdin))
    rc = dispatch.main(argv if argv is not None else [])
    return rc, capsys.readouterr().out


def mark_handlers(monkeypatch):
    """Replace each event handler with a marker-returning stub; returns the markers."""
    markers = {
        "session_start": "MARK:SS",
        "pre_compact": "MARK:PRE",
        "post_compact": "MARK:POST",
        "user_prompt_submit": "MARK:UPS",
    }
    table = {
        "SessionStart": "session_start",
        "PreCompact": "pre_compact",
        "PostCompact": "post_compact",
        "UserPromptSubmit": "user_prompt_submit",
    }
    for event, name in table.items():
        monkeypatch.setitem(dispatch.EVENT_HANDLERS, event,
                            (lambda m: (lambda payload: m))(markers[name]))
    # the default fallback is session_start; keep it consistent with the map
    monkeypatch.setattr(handlers, "session_start", lambda payload: markers["session_start"])
    return markers


# --- the identity probe path (answered before any stdin/repo read) ----------------


def test_version_probe_answers_identity_before_stdin(monkeypatch, capsys):
    # stdin that would raise if read — the version path must not touch it (L-09/L-10).
    class Boom:
        @property
        def buffer(self):
            raise AssertionError("stdin must not be read on --version")

    monkeypatch.setattr(dispatch.sys, "stdin", Boom())
    rc = dispatch.main(["--version"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == f"clauderizer {__version__}"


def test_dash_capital_v_also_identity(monkeypatch, capsys):
    rc, out = run(monkeypatch, capsys, argv=["-V"])
    assert rc == 0 and out.strip() == f"clauderizer {__version__}"


def test_help_lists_events(monkeypatch, capsys):
    rc, out = run(monkeypatch, capsys, argv=["--help"])
    assert rc == 0
    assert "Events:" in out
    for ev in ("SessionStart", "PreCompact", "PostCompact", "UserPromptSubmit"):
        assert ev in out


# --- routing ---------------------------------------------------------------------


@pytest.mark.parametrize("event,expected", [
    ("SessionStart", "MARK:SS"),
    ("PreCompact", "MARK:PRE"),
    ("PostCompact", "MARK:POST"),
    ("UserPromptSubmit", "MARK:UPS"),
])
def test_routes_each_event_to_its_handler(monkeypatch, capsys, event, expected):
    mark_handlers(monkeypatch)
    payload = json.dumps({"hook_event_name": event, "prompt": "x", "source": "startup"}).encode()
    rc, out = run(monkeypatch, capsys, stdin=payload)
    assert rc == 0 and out.strip() == expected


def test_unknown_event_falls_back_to_session_start(monkeypatch, capsys):
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys,
                  stdin=json.dumps({"hook_event_name": "TeammateIdle"}).encode())
    assert rc == 0 and out.strip() == "MARK:SS"


# --- P10 seam fix: native cross-host event names route to the right handler -------


def test_windsurf_pre_user_prompt_routes_to_user_prompt_submit(monkeypatch, capsys):
    # windsurf's native prompt-submit event must route to the LIGHT analyze pointer
    # (user_prompt_submit), NOT the full cold-start digest (session_start) — else a
    # guide-wired windsurf gets the whole digest spammed on every prompt.
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys,
                  stdin=json.dumps({"hook_event_name": "pre_user_prompt", "prompt": "x"}).encode())
    assert rc == 0 and out.strip() == "MARK:UPS"


@pytest.mark.parametrize("event", ["BeforeAgent", "TaskStart", "session.start", "agent.start"])
def test_native_session_start_analogues_route_to_session_start(monkeypatch, capsys, event):
    # gemini/cline/amp session-start analogues map explicitly to the digest handler
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys,
                  stdin=json.dumps({"hook_event_name": event}).encode())
    assert rc == 0 and out.strip() == "MARK:SS"


@pytest.mark.parametrize("bad_event", [["SessionStart"], {"x": 1}, 42, True])
def test_unhashable_or_nonstr_event_falls_back_gracefully(monkeypatch, capsys, bad_event):
    # an unhashable (list/dict) or non-str hook_event_name must reach the graceful
    # SessionStart fallback, NOT raise inside dict.get and emit the error breadcrumb
    # (L-24 robustness class — read_payload tolerates every malformed shape).
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys,
                  stdin=json.dumps({"hook_event_name": bad_event}).encode())
    assert rc == 0
    assert out.strip() == "MARK:SS"
    assert "hook error" not in out               # graceful fallback, not the breadcrumb


def test_missing_event_name_falls_back_to_session_start(monkeypatch, capsys):
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys, stdin=json.dumps({"prompt": "hi"}).encode())
    assert rc == 0 and out.strip() == "MARK:SS"


def test_empty_stdin_falls_back_to_session_start(monkeypatch, capsys):
    # The no-arg digest probe sends empty stdin (stdin=DEVNULL) — must reach the
    # SessionStart digest, the property the hardened hook_digest_probe relies on.
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys, stdin=b"")
    assert rc == 0 and out.strip() == "MARK:SS"


# --- adversarial stdin (L-18/L-19): tolerate the whole malformed corpus -----------


@pytest.mark.parametrize("raw", [
    b"",                                                   # empty
    b"   \n  ",                                            # whitespace only
    b"not json at all",                                    # garbage
    b"\xff\xfe\x00\x01nonsense",                            # non-UTF-8 bytes
    b"\xef\xbb\xbf{\"hook_event_name\": \"SessionStart\"}",  # UTF-8 BOM + valid
    b"{\r\n  \"hook_event_name\": \"SessionStart\"\r\n}",    # CRLF
    b"[1, 2, 3]",                                          # valid JSON, not an object
    b"\"just a string\"",                                  # valid JSON string
    b"42",                                                  # valid JSON number
    b"null",                                                # valid JSON null
    b"{\"hook_event_name\": \"SessionStart\", \"emoji\": \"\xf0\x9f\x9a\x80\"}",  # unicode
])
def test_malformed_or_diverse_stdin_never_crashes_and_routes_to_session_start(
        monkeypatch, capsys, raw):
    mark_handlers(monkeypatch)
    rc, out = run(monkeypatch, capsys, stdin=raw)
    # Every shape exits 0; non-object payloads (and unknown/SessionStart events)
    # reach the SessionStart default — never an exception, never silence-by-crash.
    assert rc == 0
    assert out.strip() == "MARK:SS"


def test_stdin_without_buffer_falls_back(monkeypatch, capsys):
    class NoBuffer:  # e.g. a StringIO swapped in; .buffer raises AttributeError
        pass

    mark_handlers(monkeypatch)
    monkeypatch.setattr(dispatch.sys, "stdin", NoBuffer())
    rc = dispatch.main([])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "MARK:SS"


def test_read_payload_unit(monkeypatch):
    cases = {
        b'{"a": 1}': {"a": 1},
        b'[1,2]': {},
        b'"s"': {},
        b'42': {},
        b'null': {},
        b'': {},
        b'\xef\xbb\xbf{"x": true}': {"x": True},
        b'\xff\xff': {},
    }
    for raw, expected in cases.items():
        monkeypatch.setattr(dispatch.sys, "stdin", FakeStdin(raw))
        assert dispatch.read_payload() == expected


# --- always exit 0, even when a handler explodes (INVARIANT-04) --------------------


def test_exit_0_and_breadcrumb_when_handler_raises(monkeypatch, capsys):
    def boom(payload):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(dispatch.EVENT_HANDLERS, "SessionStart", boom)
    monkeypatch.setattr(handlers, "session_start", boom)
    rc, out = run(monkeypatch, capsys, stdin=b"")
    assert rc == 0
    assert "[Clauderizer] hook error" in out and "clauderize doctor" in out


# --- integration against a real clauderized repo ----------------------------------


def _payload(event, **extra) -> bytes:
    return json.dumps({"hook_event_name": event, **extra}).encode()


def test_session_start_prints_digest_even_without_gameplan(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    rc, out = run(monkeypatch, capsys, stdin=_payload("SessionStart", source="startup"))
    assert rc == 0
    assert "[Clauderizer]" in out and "No active gameplan" in out


def test_session_start_source_compact_is_framed(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, gameplan="demo-plan", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    rc, out = run(monkeypatch, capsys, stdin=_payload("SessionStart", source="compact"))
    assert rc == 0
    assert "Resumed after context compaction" in out
    assert "[Clauderizer]" in out


def test_not_clauderized_repo_is_silent(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)  # no .clauderizer here
    rc, out = run(monkeypatch, capsys, stdin=_payload("SessionStart"))
    assert rc == 0 and out.strip() == ""


def test_pre_post_compact_silent_without_active_gameplan(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, spawn_test=False)  # no gameplan
    monkeypatch.chdir(empty_python_repo)
    for ev in ("PreCompact", "PostCompact"):
        rc, out = run(monkeypatch, capsys, stdin=_payload(ev, matcher_value="auto"))
        assert rc == 0 and out.strip() == "", f"{ev} should be silent without a gameplan"


def test_pre_compact_reminds_with_active_gameplan(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, gameplan="demo-plan", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    rc, out = run(monkeypatch, capsys, stdin=_payload("PreCompact", trigger="auto"))
    assert rc == 0
    assert "about to compact" in out
    assert "cz_add_decision" in out and "cz_add_output" in out


def test_post_compact_redigests_with_active_gameplan(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, gameplan="demo-plan", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    rc, out = run(monkeypatch, capsys, stdin=_payload("PostCompact", trigger="auto"))
    assert rc == 0
    assert "[Clauderizer]" in out
    assert "Resumed after context compaction" in out


# --- UserPromptSubmit: analyze rendering + quiet-when-empty ------------------------


def test_user_prompt_submit_renders_ids(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    from clauderizer import analyze
    monkeypatch.setattr(analyze, "analyze", lambda paths, text, k=3: {
        "decisions": [{"id": "D-007", "title": "x"}],
        "invariants": [{"id": "INVARIANT-02", "title": "y"}],
        "adjacent": [{"id": "subsys.graph", "type": "subsystem", "status": "active"}],
    })
    rc, out = run(monkeypatch, capsys, stdin=_payload("UserPromptSubmit", prompt="touch the graph writer"))
    assert rc == 0
    assert "D-007" in out and "INVARIANT-02" in out and "subsys.graph" in out
    assert "cz_analyze" in out


def test_user_prompt_submit_quiet_when_nothing_relevant(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    from clauderizer import analyze
    monkeypatch.setattr(analyze, "analyze",
                        lambda paths, text, k=3: {"decisions": [], "invariants": [], "adjacent": []})
    rc, out = run(monkeypatch, capsys, stdin=_payload("UserPromptSubmit", prompt="ok"))
    assert rc == 0 and out.strip() == ""


@pytest.mark.parametrize("prompt", ["", "   ", None])
def test_user_prompt_submit_ignores_empty_prompt(monkeypatch, capsys, empty_python_repo, prompt):
    init(empty_python_repo, spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    extra = {} if prompt is None else {"prompt": prompt}
    rc, out = run(monkeypatch, capsys, stdin=_payload("UserPromptSubmit", **extra))
    assert rc == 0 and out.strip() == ""


def test_user_prompt_submit_real_analyze_surfaces_and_stays_read_only(monkeypatch, capsys, temp_repo):
    """L-34 seam: the Phase-2 cz_analyze abstract enrichment lives in the shared
    analyze.analyze that the UserPromptSubmit hook calls on every prompt. Exercise
    the REAL gate (not a stub): it must still surface relevant ids AND stay
    read-only — no abstract index cache written from the hot hook path (the
    enrichment caps the title in hand, it never builds/writes the index), or it
    would breach INVARIANT-06."""
    from clauderizer import paths as P
    paths = P.resolve(temp_repo)
    monkeypatch.chdir(temp_repo)
    rc, out = run(monkeypatch, capsys,
                  stdin=_payload("UserPromptSubmit", prompt="is markdown canonical for the index?"))
    assert rc == 0
    assert "INVARIANT-01" in out          # the real analyze gate surfaced the relevant invariant
    assert "cz_analyze" in out
    assert not paths.abstract_index_file.exists()   # read-only: no cache materialized on the hook path


# --- INVARIANT-06: every handler is read-only -------------------------------------


def _snapshot(root: Path) -> dict[str, bytes]:
    """Bytes of every file under root except the disposable cache/lock."""
    skip = {"index.json", "write.lock"}
    snap = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in skip and ".git" not in p.parts:
            snap[str(p.relative_to(root))] = p.read_bytes()
    return snap


def test_every_event_handler_is_read_only(monkeypatch, capsys, empty_python_repo):
    init(empty_python_repo, gameplan="demo-plan", spawn_test=False)
    monkeypatch.chdir(empty_python_repo)
    before = _snapshot(empty_python_repo)
    for ev in ("SessionStart", "PreCompact", "PostCompact", "UserPromptSubmit"):
        run(monkeypatch, capsys, stdin=_payload(ev, prompt="anything", source="compact",
                                                matcher_value="auto"))
    after = _snapshot(empty_python_repo)
    assert before == after, "a hook handler mutated tracked files (INVARIANT-06)"


# --- back-compat shim -------------------------------------------------------------


def test_sessionstart_shim_delegates_and_reexports(capsys):
    # The legacy entry target still answers identically (--version returns before
    # any stdin read), and re-exports the handler API.
    assert sessionstart.main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"clauderizer {__version__}"
    assert callable(sessionstart.build_digest)
    assert callable(sessionstart.session_start)
