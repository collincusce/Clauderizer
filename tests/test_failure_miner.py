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


def test_cz_mine_failures_op_missing_dir_is_graceful(temp_repo, monkeypatch):
    from clauderizer import ops
    # hermetic cwd: a repo with an empty refusal journal, so the graceful-error
    # contract is pinned independent of this machine's live journal
    monkeypatch.chdir(temp_repo)
    res = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    assert res["ok"] is False and "not found" in res["error"]


# --- the refusal journal's read side (O-03 / D-069) -----------------------------

def _journal_refusal(repo, op, summary, date="2026-07-27"):
    p = repo / ".clauderizer" / "refusals.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "refusal", "op": op, "date": date,
                            "summary": summary}) + "\n")


def test_refusals_surface_grouped_even_without_transcripts(temp_repo, monkeypatch):
    from clauderizer import ops
    monkeypatch.chdir(temp_repo)
    _journal_refusal(temp_repo, "cz_resolve_open_item", "no Open Items section")
    _journal_refusal(temp_repo, "cz_resolve_open_item", "O-09 not found")
    _journal_refusal(temp_repo, "cz_promote_lesson", "lesson #7 not found")
    res = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    assert res["ok"] is True          # journal evidence beats the missing dir
    assert res["refusal_events"] == 3
    by_op = {p["op"]: p for p in res["proposals"] if p["kind"] == "refusal"}
    assert set(by_op) == {"cz_resolve_open_item", "cz_promote_lesson"}
    assert by_op["cz_resolve_open_item"]["count"] == 2
    assert "O-09 not found" in by_op["cz_resolve_open_item"]["evidence"]  # latest wins
    assert all(p["id"].startswith("mine:") for p in by_op.values())
    assert "refusal journal" in res["summary"]


def test_dismissed_refusal_candidate_rearms_on_the_next_refusal(temp_repo, monkeypatch):
    from clauderizer import ops
    from clauderizer import paths as P
    from clauderizer import proposals as PR
    monkeypatch.chdir(temp_repo)
    _journal_refusal(temp_repo, "cz_promote_lesson", "lesson #7 not found")
    first = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    pid = first["proposals"][0]["id"]
    PR.dismiss(P.resolve(temp_repo), pid)
    after = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    assert after["ok"] is True and after["proposals"] == []
    assert after["suppressed_count"] == 1     # suppressed, and named as such
    # a NEW refusal of the same op re-arms the candidate under a new id
    _journal_refusal(temp_repo, "cz_promote_lesson", "lesson #9 not found")
    rearmed = ops.cz_mine_failures(transcripts_dir="/nonexistent/path/xyz")
    ids = [p["id"] for p in rearmed["proposals"]]
    assert ids and pid not in ids
    assert rearmed["proposals"][0]["count"] == 2


def test_corpus_health_counts_refusals_read_only(temp_repo):
    from clauderizer import paths as P
    from clauderizer import telemetry
    paths = P.resolve(temp_repo)
    quiet = telemetry.corpus_health(paths)
    assert quiet["refusal_events"] == 0
    assert "refused" not in quiet["summary"]      # zero renders nothing extra
    _journal_refusal(temp_repo, "cz_add_output", "no such phase")
    loud = telemetry.corpus_health(paths)
    assert loud["refusal_events"] == 1
    assert "1 refused write(s) journaled" in loud["summary"]


def test_mined_proposals_join_the_id_ledger_queue(tmp_path, temp_repo, monkeypatch):
    """D-074 merge-base: mined candidates carry stable content-hash ids and a
    dismissal suppresses re-surfacing until the pattern's content changes."""
    from clauderizer import ops
    from clauderizer import proposals as PR
    from clauderizer import paths as P

    recs = [_use("a1", "Bash"), _result("a1", "fatal: boom"),
            _use("a2", "Bash"), _result("a2", "ok")]
    (tmp_path / "s.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    monkeypatch.chdir(temp_repo)  # the triage ledger lives in the repo, not the transcripts
    first = ops.cz_mine_failures(transcripts_dir=str(tmp_path))
    assert first["proposals"] and first["proposals"][0]["id"].startswith("mine:")
    again = ops.cz_mine_failures(transcripts_dir=str(tmp_path))
    assert [p["id"] for p in first["proposals"]] == [p["id"] for p in again["proposals"]]
    PR.dismiss(P.resolve(temp_repo), first["proposals"][0]["id"])
    after = ops.cz_mine_failures(transcripts_dir=str(tmp_path))
    assert first["proposals"][0]["id"] not in [p["id"] for p in after["proposals"]]
    assert after["suppressed_count"] == 1
    assert "1 suppressed by your ledger" in after["summary"]
    assert first["proposals"][0]["id"] in [p["id"] for p in after["all_proposals"]]
