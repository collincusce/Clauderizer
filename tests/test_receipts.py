"""Seen-vs-open engagement receipts (D-073) — the whole safety envelope.

Pins the binding conditions from the vetting: receipts land ONLY on genuine
engagement (cz_get success + the three engagement writes, never handoff/
phase-context assembly), the append is a lock-free single-line O_APPEND to the
gitignored sidecar and never breaks the op it rides on, the digest split is
ANY-reader labeling that drops nothing (every open id in exactly one bucket,
resolved ids in neither — D-068), and with no receipts recorded the bundle and
digest are byte-identical while compute() never creates the sidecar
(INVARIANT-06/08 — the golden gate).
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import modernize
from clauderizer import mutations as M
from clauderizer import ops
from clauderizer import paths as P
from clauderizer import receipts
from clauderizer.rituals import status_bundle as S

GID = "2026-05-01-bootstrap"  # the fixture's active gameplan


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


@contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


# --- the sidecar module ---------------------------------------------------------

def test_record_seen_appends_one_sorted_line_and_is_idempotent_per_id(temp_repo):
    paths, _ = _ctx(temp_repo)
    rec = receipts.record_seen(paths, ["H-01"], via="cz_get", reader="tester",
                               today="2026-07-27")
    assert rec["ids"] == ["H-01"]
    raw = paths.seen_file.read_text(encoding="utf-8")
    assert raw == json.dumps(
        {"date": "2026-07-27", "ids": ["H-01"], "kind": "seen",
         "reader": "tester", "via": "cz_get"}, sort_keys=True) + "\n"
    # already receipted: nothing appended, regardless of via or reader
    assert receipts.record_seen(paths, ["H-01"], via="cz_resolve_finding",
                                reader="other") is None
    assert paths.seen_file.read_text(encoding="utf-8") == raw


def test_load_seen_merges_and_tolerates_torn_lines(temp_repo):
    paths, _ = _ctx(temp_repo)
    p = paths.seen_file
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"kind": "seen", "date": "2026-07-01", "via": "cz_get",
                    "reader": "a", "ids": ["H-01", "H-02"]}) + "\n"
        + '{"kind": "seen", "date": "2026-07-02", "via": "cz_get", "re'  # torn
        + "\nnot json at all\n"
        + json.dumps({"kind": "other", "ids": ["H-09"]}) + "\n"  # not a receipt
        + json.dumps({"kind": "seen", "date": "2026-07-03",
                      "via": "cz_resolve_finding", "reader": "b",
                      "ids": ["H-01"]}) + "\n",
        encoding="utf-8")
    seen = receipts.load_seen(paths)
    assert set(seen) == {"H-01", "H-02"}
    assert seen["H-01"]["first_seen"] == "2026-07-01"
    assert seen["H-01"]["last_seen"] == "2026-07-03"
    assert seen["H-01"]["readers"] == ["a", "b"]
    assert receipts.load_seen(P.resolve(temp_repo / "nowhere")) == {}


def test_split_seen_partitions_exhaustively_and_respects_prefix():
    seen = {"H-02": {}, "g1:O-01": {}}
    never, engaged = receipts.split_seen(["H-01", "H-02", "H-03"], seen)
    assert (never, engaged) == (["H-01", "H-03"], ["H-02"])
    assert sorted(never + engaged) == ["H-01", "H-02", "H-03"]  # exactly one bucket
    never, engaged = receipts.split_seen(["O-01", "O-02"], seen, prefix="g1:")
    assert (never, engaged) == (["O-02"], ["O-01"])


def test_record_seen_refuses_symlinked_sidecar_and_never_touches_docs(temp_repo):
    paths, _ = _ctx(temp_repo)
    docs_before = {p: p.read_bytes() for p in sorted(paths.docs.rglob("*.md"))}
    receipts.record_seen(paths, ["D-001"], via="cz_get", reader="t")
    assert {p: p.read_bytes() for p in sorted(paths.docs.rglob("*.md"))} == docs_before
    paths.seen_file.unlink()
    paths.seen_file.symlink_to(temp_repo / "elsewhere.jsonl")
    try:
        receipts.record_seen(paths, ["D-002"], via="cz_get", reader="t")
        assert False, "symlinked sidecar must be refused"
    except OSError:
        pass


def test_reader_defaults_to_detected_session_agent(temp_repo, monkeypatch):
    from clauderizer import session
    paths, _ = _ctx(temp_repo)
    monkeypatch.setattr(session, "detect_session_agent", lambda env=None: "probe")
    receipts.record_seen(paths, ["H-01"], via="cz_get")
    assert receipts.load_seen(paths)["H-01"]["readers"] == ["probe"]


# --- genuine engagement only: the four REGISTRY sites ---------------------------

def test_registry_cz_get_success_writes_exactly_one_receipt(temp_repo):
    with _chdir(temp_repo):
        paths, _ = _ctx(temp_repo)
        assert ops.run_op("cz_get", id="D-001")["ok"]
        seen = receipts.load_seen(paths)
        assert set(seen) == {"D-001"}
        assert seen["D-001"]["via"] == "cz_get"
        # failed lookup receipts nothing; repeat success appends nothing
        before = paths.seen_file.read_text(encoding="utf-8")
        assert not ops.run_op("cz_get", id="H-999")["ok"]
        assert ops.run_op("cz_get", id="D-001")["ok"]
        assert paths.seen_file.read_text(encoding="utf-8") == before


def test_direct_library_cz_get_stays_byte_free(temp_repo):
    with _chdir(temp_repo):
        paths, _ = _ctx(temp_repo)
        assert ops.cz_get("D-001")["ok"]  # the unwrapped module-level original
        assert not paths.seen_file.exists()  # receipts ride the REGISTRY seam only


def test_resolve_and_check_ops_receipt_what_they_engaged(temp_repo):
    with _chdir(temp_repo):
        paths, _ = _ctx(temp_repo)
        M.add_finding(paths, title="probe", severity="low", impact="i",
                      today="2026-07-27")
        M.add_open_item(paths, gameplan_id=GID, text="an open probe")
        M.set_exit_criteria(paths, gameplan_id=GID, phase="1", criteria=["works"])
        assert ops.run_op("cz_resolve_finding", finding_id="H-01")["ok"]
        assert ops.run_op("cz_resolve_open_item", id="O-01", resolution="done",
                          gameplan_id=GID)["ok"]
        assert ops.run_op("cz_check_exit_criterion", phase="1", criterion="works",
                          gameplan_id=GID)["ok"]
        seen = receipts.load_seen(paths)
        assert set(seen) == {"H-01", f"{GID}:O-01", f"criteria:{GID}:1"}


def test_receipt_allowlist_is_exactly_the_four_engagement_ops():
    assert ops._RECEIPT_OPS == {"cz_get", "cz_resolve_finding",
                                "cz_resolve_open_item", "cz_check_exit_criterion"}


def test_no_auto_receipts_from_assembly_ops(temp_repo):
    with _chdir(temp_repo):
        paths, _ = _ctx(temp_repo)
        assert ops.run_op("cz_status")["ok"]
        assert ops.run_op("cz_next_phase_context")["ok"]
        assert not paths.seen_file.exists()


def test_a_failed_append_never_breaks_the_op(temp_repo):
    with _chdir(temp_repo):
        paths, _ = _ctx(temp_repo)
        paths.seen_file.parent.mkdir(parents=True, exist_ok=True)
        paths.seen_file.symlink_to(temp_repo / "elsewhere.jsonl")
        got = ops.run_op("cz_get", id="D-001")
        assert got["ok"] and got["id"] == "D-001"  # read unharmed (best-effort)


# --- the digest split: golden gates ---------------------------------------------

def test_no_sidecar_bundle_and_digest_byte_identical_and_nothing_created(temp_repo):
    paths, config = _ctx(temp_repo)
    M.add_finding(paths, title="probe", severity="low", impact="i",
                  today="2026-07-27")
    M.add_open_item(paths, gameplan_id=GID, text="an open probe")
    bundle = S.compute(paths, config)
    digest = S.render_digest(bundle)
    assert not paths.seen_file.exists()  # compute() never creates it (INVARIANT-06)
    assert "findings_engagement" not in bundle
    assert "open_items_engagement" not in bundle
    assert "never-engaged" not in digest
    assert "Open findings: 1 (H-01)." in digest
    assert "Open items: 1 unresolved (O-01)." in digest
    # a second compute renders byte-identically — no receipt state accrues
    assert S.render_digest(S.compute(paths, config)) == digest


def test_with_receipts_every_open_id_in_exactly_one_bucket(temp_repo):
    paths, config = _ctx(temp_repo)
    for t in ("one", "two"):
        M.add_finding(paths, title=t, severity="low", impact="i",
                      today="2026-07-27")
    M.add_open_item(paths, gameplan_id=GID, text="first")
    M.add_open_item(paths, gameplan_id=GID, text="second")
    receipts.record_seen(paths, ["H-02"], via="cz_get", reader="t")
    receipts.record_seen(paths, [f"{GID}:O-02"], via="cz_resolve_open_item",
                         reader="t")
    bundle = S.compute(paths, config)
    eng = bundle["findings_engagement"]
    assert (eng["never"], eng["engaged"]) == (["H-01"], ["H-02"])
    assert sorted(eng["never"] + eng["engaged"]) == sorted(bundle["open_findings"])
    eng = bundle["open_items_engagement"]
    assert (eng["never"], eng["engaged"]) == (["O-01"], ["O-02"])
    digest = S.render_digest(bundle)
    assert "Open findings: 2 — 1 never-engaged (H-01); 1 engaged-but-open (H-02)." in digest
    assert "Open items: 2 unresolved — 1 never-engaged (O-01); 1 engaged-but-open (O-02)." in digest


def test_resolved_ids_appear_in_neither_bucket(temp_repo):
    paths, config = _ctx(temp_repo)
    for t in ("one", "two"):
        M.add_finding(paths, title=t, severity="low", impact="i",
                      today="2026-07-27")
    receipts.record_seen(paths, ["H-01"], via="cz_get", reader="t")
    M.resolve_finding(paths, finding_id="H-01", status="resolved", note="done")
    bundle = S.compute(paths, config)
    eng = bundle["findings_engagement"]
    assert "H-01" not in eng["never"] + eng["engaged"]  # resolved: in neither
    assert bundle["open_findings"] == ["H-02"] == eng["never"]


# --- D-067 classification ships complete ----------------------------------------

def test_sidecar_is_gitignored_by_init_and_converged_by_modernize(temp_repo):
    for line in (".clauderizer/seen.local.jsonl", ".clauderizer/sessions.jsonl",
                 ".clauderizer/refusals.jsonl"):
        assert line in modernize.LOCAL_STATE_IGNORES
    paths, config = _ctx(temp_repo)
    gi = temp_repo / ".gitignore"
    gi.write_text("", encoding="utf-8")
    assert ".clauderizer/seen.local.jsonl" in modernize._missing_local_state_ignores(paths)
    rep = modernize.report(paths, config)
    assert any(i["action"] == "ensure_gitignore_current" for i in rep["mechanical"])
    modernize.apply(paths, config)
    assert ".clauderizer/seen.local.jsonl" in gi.read_text(encoding="utf-8").splitlines()
