"""Phase 0 of 2026-07-23-dreaming-loop: the dream-journal substrate (D-058).

Round-trip, schema/PII rejection (validate-then-append — INVARIANT-03 means no
retroactive redaction), content-hash dedupe, lock discipline, and the contract
surface (schema_version, registry parity, init gitignoring).
"""

import contextlib
import json
import os

from clauderizer import contract, dreams, mutations, ops
from clauderizer.paths import resolve
from clauderizer.tools_list import TOOL_NAMES


@contextlib.contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _add(paths, note="Found a gap in the docs. The tokenizer rule was hard to locate.",
         kind="gap", **kw):
    kw.setdefault("gameplan", "2026-05-01-bootstrap")
    kw.setdefault("phase", "1")
    kw.setdefault("today", "2026-07-24")
    return mutations.add_dream(paths, kind=kind, note=note, **kw)


# --- round-trip -------------------------------------------------------------------


def test_add_dream_appends_one_sorted_key_jsonl_record(temp_repo):
    paths = resolve(temp_repo)
    res = _add(paths, refs=["D-058", "L-50"])
    assert res["ok"] is True and res["appended"] is True
    assert res["id"].startswith("dream:")
    raw = paths.dreams_file.read_text(encoding="utf-8")
    assert raw.count("\n") == 1
    rec = json.loads(raw)
    assert rec == res["record"]
    assert rec["kind"] == "gap" and rec["phase"] == "1"
    assert rec["date"] == "2026-07-24"
    assert rec["refs"] == ["D-058", "L-50"]
    # sort_keys makes the bytes deterministic (telemetry substrate contract)
    assert raw.strip() == json.dumps(rec, sort_keys=True, ensure_ascii=False)


def test_second_note_appends_prior_line_untouched(temp_repo):
    paths = resolve(temp_repo)
    first = _add(paths)["record"]
    res = _add(paths, note="The preflight surprised me by refreshing the baseline.",
               kind="surprise")
    assert res["count"] == 2
    lines = paths.dreams_file.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == first  # append-only: line 0 byte-stable
    assert dreams.read_notes(paths)[1]["kind"] == "surprise"


def test_read_notes_tolerates_garbled_lines(temp_repo):
    paths = resolve(temp_repo)
    _add(paths)
    with open(paths.dreams_file, "a", encoding="utf-8") as f:
        f.write("{torn write\n")
    assert len(dreams.read_notes(paths)) == 1


# --- validate-then-append rejects ---------------------------------------------------


def _assert_rejected(paths, res, needle):
    assert res["ok"] is False and res["appended"] is False
    assert any(needle in p for p in res["problems"]), res["problems"]
    assert not paths.dreams_file.exists()  # nothing appended on reject


def test_unknown_kind_rejected(temp_repo):
    paths = resolve(temp_repo)
    _assert_rejected(paths, _add(paths, kind="musing"), "unknown kind")


def test_oversize_chars_rejected(temp_repo):
    paths = resolve(temp_repo)
    _assert_rejected(paths, _add(paths, note="x" * 601), "chars")


def test_oversize_sentences_rejected(temp_repo):
    paths = resolve(temp_repo)
    note = "One thing. Two things. Three things. Four things. Five things."
    _assert_rejected(paths, _add(paths, note=note), "sentences")


def test_empty_note_rejected(temp_repo):
    paths = resolve(temp_repo)
    _assert_rejected(paths, _add(paths, note="   "), "empty")


def test_pii_shapes_rejected(temp_repo):
    paths = resolve(temp_repo)
    for bad, label in [
        ("User mail is somebody@example.com here.", "email"),
        ("The key sk-abcdEFGH1234567890 leaked into logs.", "secret-token"),
        ("Token ghp_" + "a1B2" * 6 + " appeared in stderr.", "secret-token"),
        ("Cred AKIAIOSFODNN7EXAMPLE was in the diff.", "secret-token"),
        ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIx was pasted.",
         "secret-token"),
        ("Wiring lives at /home/somebody/repo/x today.", "home path"),
        ("Config sits in C:\\Users\\somebody\\app now.", "home path"),
        ("Mounted via \\\\wsl.localhost\\Ubuntu\\repo path.", "home path"),
    ]:
        _assert_rejected(paths, _add(paths, note=bad), label)


def test_repo_relative_paths_pass_the_pii_lint(temp_repo):
    paths = resolve(temp_repo)
    res = _add(paths, note="The rule hides in src/clauderizer/analyze.py today. "
                           "ARCHITECTURE.md never points at it.")
    assert res["ok"] is True and res["appended"] is True


def test_too_many_refs_rejected(temp_repo):
    paths = resolve(temp_repo)
    _assert_rejected(paths, _add(paths, refs=[f"L-{i:02d}" for i in range(9)]),
                     "refs")


# --- dedupe -------------------------------------------------------------------------


def test_identical_note_is_a_noop(temp_repo):
    paths = resolve(temp_repo)
    first = _add(paths)
    dup = _add(paths)
    assert dup["ok"] is True and dup["appended"] is False and dup["deduped"] is True
    assert dup["id"] == first["id"]
    assert paths.dreams_file.read_text(encoding="utf-8").count("\n") == 1


def test_rewrapped_whitespace_still_dedupes(temp_repo):
    paths = resolve(temp_repo)
    _add(paths, note="Found a gap in the docs.\nThe tokenizer rule was hard to locate.")
    dup = _add(paths, note="Found a gap  in the docs. The tokenizer rule was hard to locate.")
    assert dup["deduped"] is True


def test_same_note_in_a_later_phase_is_new_signal(temp_repo):
    paths = resolve(temp_repo)
    _add(paths, phase="1")
    res = _add(paths, phase="2")
    assert res["appended"] is True  # phase is part of the identity


# --- lock + registry + contract surface ----------------------------------------------


def test_add_dream_takes_the_write_lock():
    # _locked wraps with functools.wraps — the blessed-write shape (H-05)
    assert hasattr(mutations.add_dream, "__wrapped__")


def test_registered_as_writer_and_advertised():
    assert "cz_add_dream" in TOOL_NAMES
    assert "cz_add_dream" in ops.REGISTRY
    assert ops.REGISTRY["cz_add_dream"].writes is True


def test_op_result_carries_schema_version_and_contract_keys(temp_repo):
    with _chdir(temp_repo):
        res = ops.run_op(
            "cz_add_dream", kind="friction",
            note="The cascade tool asked for verdicts twice. Confusing order.")
    assert res["schema_version"] == contract.CONTRACT_SCHEMA_VERSION
    # the captured contract surface of a successful append — keys clients see
    assert {"ok", "appended", "deduped", "id", "record", "count", "path",
            "summary", "schema_version"} <= set(res)


def test_op_defaults_resolve_active_gameplan_and_current_phase(temp_repo):
    with _chdir(temp_repo):
        res = ops.run_op(
            "cz_add_dream", kind="win",
            note="Defaults resolved without me naming the gameplan.")
    assert res["record"]["gameplan"] == "2026-05-01-bootstrap"
    assert res["record"]["phase"] == "1"  # the fixture's IN PROGRESS phase


def test_dream_journal_writes_never_bump_the_revision(temp_repo):
    from clauderizer import revision
    paths = resolve(temp_repo)
    with _chdir(temp_repo):
        before = revision.read(paths.clauderizer_dir)
        ops.run_op("cz_add_dream", kind="gap",
                   note="Journal writes are operational state, not memory.")
        after = revision.read(paths.clauderizer_dir)
    assert after == before  # inside .clauderizer/ — not a memory write


# --- gitignore discipline -------------------------------------------------------------


def test_init_gitignores_the_dream_journal_and_telemetry(empty_python_repo):
    from clauderizer.scaffold.init import init
    init(empty_python_repo, spawn_test=False)
    gi = (empty_python_repo / ".gitignore").read_text(encoding="utf-8")
    assert ".clauderizer/dreams.jsonl" in gi
    assert ".clauderizer/telemetry.jsonl" in gi


def test_this_repo_gitignores_the_dream_journal():
    from pathlib import Path
    gi = (Path(__file__).parent.parent / ".gitignore").read_text(encoding="utf-8")
    assert ".clauderizer/dreams.jsonl" in gi.splitlines()
