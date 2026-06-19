"""Diverse / adversarial battery for the two Headroom-borrowed survivors.

Lenses: malformed & non-dict input, empty/blank, encoding (BOM/CRLF), unicode,
window boundaries, determinism, structural invariants (pointer ⊆ lessons; no
drops), the op-level cap, and a skip-guarded real-corpus smoke test.
"""
import json
import os
import re

import pytest

from clauderizer import learn
from clauderizer.rituals import handoff as H

# --- shared transcript builders ----------------------------------------------


def _use(tid, name):
    return {"type": "assistant",
            "message": {"role": "assistant",
                        "content": [{"type": "tool_use", "id": tid, "name": name}]}}


def _result(tid, text, is_error=False):
    return {"type": "user",
            "message": {"role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": tid,
                                     "content": text, "is_error": is_error}]}}


def _user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def _write(tmp_path, records, *, name="t.jsonl"):
    p = tmp_path / name
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def _index(lessons):
    body = "\n\n".join(f"**{i + 1}.** {t}" for i, t in enumerate(lessons))
    return f"# Index\n\n## Accumulated Lessons\n\n{body}\n"


# --- lens 1: malformed / non-dict / empty input (learn) ----------------------


def test_mine_tolerates_non_dict_json_lines(tmp_path):
    # Valid JSON that is NOT an object must not crash the dict-shaped parser.
    p = tmp_path / "t.jsonl"
    lines = ["42", '"a bare string"', "[1, 2, 3]", "null", "true", "3.14",
             json.dumps(_use("a1", "Bash")), json.dumps(_result("a1", "fatal: boom")),
             json.dumps(_use("a2", "Bash")), json.dumps(_result("a2", "ok"))]
    p.write_text("\n".join(lines), encoding="utf-8")
    props = learn.mine(p)  # must not raise
    assert any(pr["kind"] == "tool-fix" for pr in props)


def test_mine_tolerates_garbled_and_blank_lines(tmp_path):
    p = tmp_path / "t.jsonl"
    lines = ["", "   ", "{not json at all", "}{", "\x00\x01",
             json.dumps(_use("a1", "PowerShell")),
             json.dumps(_result("a1", "1 failed, 3 passed", is_error=True)),
             json.dumps(_use("a2", "PowerShell")), json.dumps(_result("a2", "4 passed"))]
    p.write_text("\n".join(lines), encoding="utf-8")
    props = learn.mine(p)
    assert any(pr["kind"] == "test-fix" for pr in props)


def test_mine_on_empty_file(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert learn.mine(p) == []


def test_mine_handles_bom_and_crlf(tmp_path):
    # A UTF-8 BOM on the first line and CRLF endings must not lose records.
    recs = [_use("a1", "Bash"), _result("a1", "fatal: kaboom"),
            _use("a2", "Bash"), _result("a2", "ok")]
    text = "\r\n".join(json.dumps(r) for r in recs)
    p = tmp_path / "bom.jsonl"
    p.write_bytes("﻿".encode("utf-8") + text.encode("utf-8"))
    props = learn.mine(p)
    assert any(pr["kind"] == "tool-fix" for pr in props)


# --- lens 1b: shape-validity crash vectors (valid JSON, hostile shape) -------
# Regression locks for three crash vectors found by adversarial fuzzing: invalid
# UTF-8 bytes (UnicodeDecodeError — a ValueError, which escaped mine_dir's
# OSError-only handler), an unhashable tool_use_id used as a dict key, and a
# non-str `text` in a structured content list. Contract: "never crash on
# malformed input" (O-03) — these extend tolerance past JSON validity to shape.


def test_invalid_utf8_bytes_do_not_abort_batch(tmp_path):
    (tmp_path / "bad.jsonl").write_bytes(b'{"x":1}\n\xff\xfe raw bytes \x80\xff\n')
    good = [_use("a1", "Bash"), _result("a1", "fatal: kaboom"),
            _use("a2", "Bash"), _result("a2", "ok")]
    (tmp_path / "good.jsonl").write_text(
        "\n".join(json.dumps(r) for r in good), encoding="utf-8")
    out = learn.mine_dir(str(tmp_path))  # must not raise on the bad bytes
    assert any(p["kind"] == "tool-fix" for p in out.get("good.jsonl", []))


def test_invalid_utf8_through_op_is_graceful(tmp_path):
    from clauderizer import ops
    (tmp_path / "bad.jsonl").write_bytes(b'\xff\xfe\x00 not utf-8 at all \xff\n')
    res = ops.cz_mine_failures(transcripts_dir=str(tmp_path))
    assert res["ok"] is True  # graceful, not a crash


def test_unhashable_tool_use_id_is_skipped(tmp_path):
    recs = [_use("a1", "Bash"),
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": ["a1"],
                 "content": "fatal: boom", "is_error": True}]}}]
    assert learn.mine(_write(tmp_path, recs)) == []  # id skipped, no crash


def test_nonstr_text_block_is_skipped(tmp_path):
    recs = [_use("a1", "Bash"),
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "a1",
                 "content": [{"type": "text", "text": 123}], "is_error": True}]}},
            _use("a2", "Bash"), _result("a2", "ok")]
    assert any(p["kind"] == "tool-fix" for p in learn.mine(_write(tmp_path, recs)))


def test_mine_dir_isolates_a_failing_file(tmp_path, monkeypatch):
    # Belt-and-suspenders: if mine() ever raises on one file (unforeseen drift),
    # mine_dir isolates it and still returns the other files' results.
    good = [_use("a1", "Bash"), _result("a1", "fatal: x"),
            _use("a2", "Bash"), _result("a2", "ok")]
    (tmp_path / "a_good.jsonl").write_text(
        "\n".join(json.dumps(r) for r in good), encoding="utf-8")
    (tmp_path / "b_bad.jsonl").write_text("{}", encoding="utf-8")
    real_mine = learn.mine

    def flaky(path, **kw):
        if str(path).endswith("b_bad.jsonl"):
            raise RuntimeError("simulated unforeseen drift")
        return real_mine(path, **kw)

    monkeypatch.setattr(learn, "mine", flaky)
    out = learn.mine_dir(str(tmp_path))
    assert "b_bad.jsonl" not in out  # the raiser was isolated
    assert any(p["kind"] == "tool-fix" for p in out.get("a_good.jsonl", []))


# --- lens 2: boundaries & determinism (learn) --------------------------------


def test_fix_within_window_detected(tmp_path):
    recs = [_use("e", "Bash"), _result("e", "fatal: x")]
    recs += [_use(f"r{i}", "Read") for i in range(7)]  # 7 unrelated tools
    recs += [_use("ok", "Bash"), _result("ok", "done")]  # success at offset 8 (in window)
    # interleave Read results so they're valid pairs
    p = _write(tmp_path, recs)
    assert any(pr["kind"] == "tool-fix" for pr in learn.mine(p))


def test_fix_outside_window_not_detected(tmp_path):
    recs = [_use("e", "Bash"), _result("e", "fatal: x")]
    recs += [_use(f"r{i}", "Read") for i in range(9)]  # 9 unrelated tools
    recs += [_use("ok", "Bash"), _result("ok", "done")]  # success at offset 10 (>window)
    p = _write(tmp_path, recs)
    assert learn.mine(p) == []


def test_mine_is_deterministic(tmp_path):
    recs = [_use("a1", "Bash"), _result("a1", "fatal: a"), _use("a2", "Bash"), _result("a2", "ok"),
            _use("b1", "PowerShell"), _result("b1", "2 failed, 1 passed", is_error=True),
            _use("b2", "PowerShell"), _result("b2", "3 passed"),
            _user("No, that's wrong, revert it.")]
    p = _write(tmp_path, recs)
    assert learn.mine(p) == learn.mine(p)


def test_unicode_content_does_not_crash(tmp_path):
    recs = [_use("a1", "Bash"), _result("a1", "fatal: café déjà vu ☕ 中文 ошибка"),
            _use("a2", "Bash"), _result("a2", "ok")]
    assert learn.mine(_write(tmp_path, recs))  # no crash, a proposal returned


# --- lens 3: op-level cap ----------------------------------------------------


def test_cz_mine_failures_caps_max_proposals(tmp_path):
    from clauderizer import ops
    recs = []
    for i in range(20):
        recs += [_use(f"e{i}", "Bash"), _result(f"e{i}", f"fatal: boom{i}"),
                 _use(f"s{i}", "Bash"), _result(f"s{i}", "ok")]
    _write(tmp_path, recs, name="m.jsonl")
    res = ops.cz_mine_failures(transcripts_dir=str(tmp_path), max_proposals=5)
    assert res["ok"] is True
    assert res["shown"] == 5 and res["proposal_count"] >= 20
    assert len(res["proposals"]) == 5


# --- lens 4: structural invariants (handoff) ---------------------------------


def test_pointer_is_subset_of_lessons():
    lessons = [f"Lesson {i} about alpha beta gamma topic{i}" for i in range(1, 9)]
    out = H.relevant_lesson_pointer(_index(lessons), "alpha beta gamma topic3 topic5", k=4)
    assert out
    ids = [int(x) for x in re.findall(r"#(\d+)", out)]
    assert ids and all(1 <= i <= 8 for i in ids) and len(ids) <= 4


def test_no_drop_property_across_sizes():
    for n in range(1, 15):
        idx = _index([f"Lesson {i} about topic{i} and handoff propagation" for i in range(1, n + 1)])
        rolled, count = H.collect_lessons(idx)
        assert count == n
        for i in range(1, n + 1):
            assert f"**{i}.**" in rolled


def test_no_drop_with_category_headings():
    idx = ("# I\n\n## Accumulated Lessons\n\n### Category: Process\n\n"
           "**1.** First process lesson.\n\n**2.** Second process lesson.\n\n"
           "### Category: Testing\n\n**3.** A testing lesson about handoff coverage.\n")
    rolled, count = H.collect_lessons(idx)
    assert count == 3
    assert "### Category: Process" in rolled and "### Category: Testing" in rolled
    out = H.relevant_lesson_pointer(idx, "handoff coverage testing", k=2)  # 3 > 2
    assert out is not None


def test_all_obsolete_yields_no_entries_and_no_pointer():
    lessons = [f"Lesson {i} about handoff (obsolete 2026-06-19: superseded)" for i in range(1, 8)]
    idx = _index(lessons)
    assert H._active_lesson_entries(idx) == []
    assert H.relevant_lesson_pointer(idx, "handoff", k=3) is None


def test_pointer_is_deterministic():
    lessons = [f"Lesson {i} alpha beta topic{i}" for i in range(1, 10)]
    idx = _index(lessons)
    q = "alpha beta topic2 topic7"
    assert H.relevant_lesson_pointer(idx, q, k=5) == H.relevant_lesson_pointer(idx, q, k=5)


def test_unicode_lessons_do_not_crash():
    lessons = ["Leçon sur les handoffs ☕", "Lección sobre café", "中文教训",
               "fourth lesson", "fifth lesson", "sixth lesson"]
    H.relevant_lesson_pointer(_index(lessons), "handoff café 中文", k=3)  # no crash


def test_blank_lesson_line_is_harmless():
    idx = "# I\n\n## Accumulated Lessons\n\n**1.**\n\n**2.** real lesson about handoff\n"
    entries = H._active_lesson_entries(idx)
    assert {e["id"] for e in entries} == {"1", "2"}


# --- lens 5: real-corpus smoke (local only) ----------------------------------

_CORPUS = "/mnt/c/Users/rafaj/.claude/projects/--wsl-localhost-ubuntu-home-ccusce-Clauderizer"


@pytest.mark.skipif(not os.path.isdir(_CORPUS), reason="local transcript corpus only")
def test_real_corpus_deterministic_and_crash_free():
    a = learn.mine_dir(_CORPUS)
    b = learn.mine_dir(_CORPUS)
    assert a == b  # deterministic over real, heterogeneous data
    assert sum(len(v) for v in a.values()) > 0
