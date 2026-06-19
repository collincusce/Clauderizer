"""Idea #3: the failure-miner detects failure->fix patterns and PROPOSES only.

Synthetic JSONL fixtures exercise each detector and the precision guards. The
miner is read-only and stdlib-only; it returns draft cz_add_correction args and
writes nothing (D-015/INVARIANT-05).
"""
import json

from clauderizer import learn


def _write(tmp_path, records):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


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


def test_detects_tool_error_then_fix(tmp_path):
    # is_error is unreliable for shells, so the error is detected by content.
    recs = [_use("a1", "Bash"), _result("a1", "bash: line 1: gh: command not found"),
            _use("a2", "Bash"), _result("a2", "ok done")]
    props = learn.mine(_write(tmp_path, recs))
    assert len(props) == 1
    assert props[0]["kind"] == "tool-fix" and props[0]["tool"] == "Bash"


def test_detects_test_fail_then_pass(tmp_path):
    recs = [_use("a1", "PowerShell"), _result("a1", "1 failed, 304 passed in 5s", is_error=True),
            _use("a2", "PowerShell"), _result("a2", "305 passed in 5s")]
    props = learn.mine(_write(tmp_path, recs))
    assert any(p["kind"] == "test-fix" for p in props)


def test_excludes_tool_protocol_noise(tmp_path):
    recs = [_use("a1", "Edit"), _result("a1", "File has not been read yet. Read it first.", is_error=True),
            _use("a2", "Edit"), _result("a2", "ok")]
    assert learn.mine(_write(tmp_path, recs)) == []


def test_no_fix_means_no_proposal(tmp_path):
    # An error with no subsequent same-tool success is not a fix.
    recs = [_use("a1", "Bash"), _result("a1", "fatal: something broke")]
    assert learn.mine(_write(tmp_path, recs)) == []


def test_zero_failed_count_is_not_an_error(tmp_path):
    # A clean pytest summary ("0 failed") must NOT be mistaken for a failure —
    # precision over recall. No spurious test-fix even when a same-tool success
    # follows the passing run.
    recs = [_use("a1", "PowerShell"), _result("a1", "305 passed, 0 failed in 5s"),
            _use("a2", "PowerShell"), _result("a2", "all good")]
    assert learn.mine(_write(tmp_path, recs)) == []


def test_ignores_benign_search_tool_errors(tmp_path):
    # Grep/Glob no-match is not a corrected mistake (not in _RETRY_TOOLS).
    recs = [_use("a1", "Grep"), _result("a1", "No matches found", is_error=True),
            _use("a2", "Grep"), _result("a2", "found it")]
    assert learn.mine(_write(tmp_path, recs)) == []


def test_detects_user_correction(tmp_path):
    recs = [_use("a1", "Edit"), _result("a1", "ok"),
            _user("No, that's wrong — you should have used the existing helper instead.")]
    props = learn.mine(_write(tmp_path, recs))
    assert any(p["kind"] == "user-correction" for p in props)


def test_long_message_with_no_in_prose_is_not_a_correction(tmp_path):
    recs = [_use("a1", "Edit"), _result("a1", "ok"),
            _user("There is no rush on this; the plan looks great and I am happy with it. " * 12)]
    props = learn.mine(_write(tmp_path, recs))
    assert not any(p["kind"] == "user-correction" for p in props)


def test_proposes_drafts_writes_nothing(tmp_path):
    recs = [_use("a1", "Bash"), _result("a1", "Exit code 1 Traceback (most recent call last):"),
            _use("a2", "Bash"), _result("a2", "ok")]
    props = learn.mine(_write(tmp_path, recs))
    assert props
    for p in props:
        assert set(p["draft"]) >= {"gameplan_said", "actually", "why"}


def test_cz_mine_failures_op_on_explicit_dir(tmp_path):
    from clauderizer import ops
    recs = [_use("a1", "Bash"), _result("a1", "fatal: boom"),
            _use("a2", "Bash"), _result("a2", "ok")]
    (tmp_path / "s.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    res = ops.cz_mine_failures(transcripts_dir=str(tmp_path))
    assert res["ok"] is True
    assert res["proposal_count"] >= 1
    assert res["proposals"][0]["source"] == "s.jsonl"
    assert "decide" in res["prompt"]


def test_cz_mine_failures_op_missing_dir_is_graceful():
    from clauderizer import ops
    res = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    assert res["ok"] is False and "not found" in res["error"]
