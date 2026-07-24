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


# --- Phase 1: capture ritual & read-only nudges ---------------------------------


def test_digest_dream_gauge_quiet_when_empty(temp_repo):
    from clauderizer.config import Config
    from clauderizer.rituals import status_bundle as S
    paths = resolve(temp_repo)
    with _chdir(temp_repo):
        out = S.render_digest(S.compute(paths, Config.load(paths.config_file)))
    assert "Dreams:" not in out  # no journal -> byte-identical digest (L-41)


def test_digest_dream_gauge_counts_notes_single_header(temp_repo):
    from clauderizer.config import Config
    from clauderizer.rituals import status_bundle as S
    paths = resolve(temp_repo)
    _add(paths)
    _add(paths, note="A second observation. The gauge should say two.", kind="drift")
    with _chdir(temp_repo):
        out = S.render_digest(S.compute(paths, Config.load(paths.config_file)))
    assert "Dreams: 2 note(s) awaiting the dreamer." in out
    assert out.count("[Clauderizer]") == 1  # one injection point (INVARIANT-08)


def test_pre_compact_reminds_the_dream_note(temp_repo):
    from clauderizer.hook import handlers
    with _chdir(temp_repo):
        msg = handlers.pre_compact({})
    assert msg is not None and "cz_add_dream" in msg


def test_hook_handlers_read_only_with_dream_journal(temp_repo):
    """INVARIANT-06 extended over the new advisory path: with a journal present,
    every handler still mutates nothing (same skip-set as the house sweep)."""
    from clauderizer.hook import handlers
    paths = resolve(temp_repo)
    _add(paths)
    skip = {"index.json", "write.lock"}
    def snap():
        return {str(p.relative_to(temp_repo)): p.read_bytes()
                for p in sorted(temp_repo.rglob("*"))
                if p.is_file() and p.name not in skip and ".git" not in p.parts}
    before = snap()
    with _chdir(temp_repo):
        handlers.session_start({})
        handlers.pre_compact({})
        handlers.post_compact({})
        handlers.user_prompt_submit({"prompt": "does the dream ritual apply here?"})
    assert snap() == before


def test_stanza_source_and_both_renders_carry_the_ritual():
    from pathlib import Path
    root = Path(__file__).parent.parent
    for rel in ("src/clauderizer/templates/claude_stanza.md", "CLAUDE.md", "AGENTS.md"):
        assert "cz_add_dream" in (root / rel).read_text(encoding="utf-8"), \
            f"{rel} lost the dream-note ritual (L-55: source + renders move together)"


def test_procedure_doc_version_and_section_match_engine():
    from pathlib import Path
    from clauderizer import PROCEDURE_VERSION
    root = Path(__file__).parent.parent
    for rel in ("docs/gameplans/GAMEPLAN-PROCEDURE.md",
                "src/clauderizer/templates/GAMEPLAN-PROCEDURE.md"):
        text = (root / rel).read_text(encoding="utf-8")
        assert f"**Procedure version**: {PROCEDURE_VERSION}" in text[:400], rel
        assert "## Dream Notes (experiential capture)" in text, rel


# --- Phase 2: cz_dream — ripeness-gated, bounded, deterministic assembly ----------


def _seed(paths, n, topic="distinct"):
    """n unique notes; topic='same' makes them lexically related."""
    for i in range(n):
        if topic == "same":
            note = (f"The tokenizer documentation gap bit again in spot {i}. "
                    f"Nothing points readers at the canonical splitter rule.")
        else:
            note = (f"Observation alpha{i} bravo{i} charlie{i} delta{i}. "
                    f"Unique territory echo{i} foxtrot{i} golf{i}.")
        r = _add(paths, note=note, kind="gap" if i % 2 else "friction",
                 phase=str(i))
        assert r["appended"] is True, r


def test_dream_not_ripe_reports_counts(temp_repo):
    paths = resolve(temp_repo)
    _seed(paths, dreams.RIPENESS_NOTES - 1)
    res = dreams.assemble(paths, today="2026-07-24")
    assert res["state"] == "not_ripe"
    assert res["unconsumed"] == dreams.RIPENESS_NOTES - 1
    assert res["ripeness"] == dreams.RIPENESS_NOTES


def test_dream_ripe_bundle_clusters_and_reports_weight(temp_repo):
    paths = resolve(temp_repo)
    _seed(paths, 4, topic="same")
    _seed(paths, dreams.RIPENESS_NOTES - 4)
    res = dreams.assemble(paths, today="2026-07-24")
    assert res["state"] == "ripe"
    assert res["clusters"], "ripe bundle must carry clusters"
    # the four related notes grouped: some cluster holds all four ids
    sizes = [c["size"] for c in res["clusters"]]
    assert max(sizes) >= 4
    top = res["clusters"][0]
    assert len(top["exemplars"]) <= dreams.CLUSTER_MAX_EXEMPLARS
    assert isinstance(res["est_tokens"], int) and res["est_tokens"] > 0
    assert "corpus_health" in res and "lesson_flags" in res


def test_dream_bundle_is_bounded_and_names_the_tail(temp_repo):
    paths = resolve(temp_repo)
    _seed(paths, 30)  # 30 lexically-disjoint notes -> 30 candidate clusters
    res = dreams.assemble(paths, today="2026-07-24")
    assert res["state"] == "ripe"
    assert len(res["clusters"]) <= dreams.BUNDLE_MAX_CLUSTERS
    assert res["clusters_dropped"] == 30 - dreams.BUNDLE_MAX_CLUSTERS  # no silent caps


def test_dream_blocked_while_proposals_untriaged_and_resumes_after(temp_repo):
    from clauderizer import proposals as P
    from clauderizer.telemetry import _append
    paths = resolve(temp_repo)
    _seed(paths, dreams.RIPENESS_NOTES)
    _append(dreams.proposals_path(paths),
            {"id": "dream-prop:aaaa0000bbbb", "detail": "seeded", "created": "2026-07-24"})
    blocked = dreams.assemble(paths, today="2026-07-24")
    assert blocked["state"] == "blocked_on_triage"          # A-001, side 1
    assert blocked["pending"] == ["dream-prop:aaaa0000bbbb"]
    P.dismiss(paths, "dream-prop:aaaa0000bbbb")
    resumed = dreams.assemble(paths, today="2026-07-24")
    assert resumed["state"] == "ripe"                        # A-001, side 2


def test_dream_handled_marker_unblocks_too(temp_repo):
    from clauderizer.telemetry import _append
    paths = resolve(temp_repo)
    _seed(paths, dreams.RIPENESS_NOTES)
    _append(dreams.proposals_path(paths),
            {"id": "dream-prop:cccc1111dddd", "detail": "seeded", "created": "2026-07-24"})
    _append(dreams.proposals_path(paths),
            {"id": "dream-prop:cccc1111dddd", "handled": "2026-07-24"})
    assert dreams.assemble(paths, today="2026-07-24")["state"] == "ripe"


def test_dream_watermark_consumption_shrinks_unconsumed(temp_repo):
    paths = resolve(temp_repo)
    _seed(paths, dreams.RIPENESS_NOTES)
    ids = [n["id"] for n in dreams.read_notes(paths)]
    dreams.watermark_path(paths).write_text(
        json.dumps({"consumed": ids[:6]}), encoding="utf-8")
    res = dreams.assemble(paths, today="2026-07-24")
    assert res["state"] == "not_ripe" and res["unconsumed"] == len(ids) - 6


def test_dream_is_deterministic_and_read_only(temp_repo):
    paths = resolve(temp_repo)
    _seed(paths, dreams.RIPENESS_NOTES + 2)
    skip = {"index.json", "write.lock"}
    def snap():
        return {str(p.relative_to(temp_repo)): p.read_bytes()
                for p in sorted(temp_repo.rglob("*"))
                if p.is_file() and p.name not in skip and ".git" not in p.parts}
    before = snap()
    a = dreams.assemble(paths, today="2026-07-24")
    b = dreams.assemble(paths, today="2026-07-24")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert snap() == before  # INVARIANT-05: assembly writes nothing


def test_dream_clustering_uses_the_canonical_tokenizer():
    # INVARIANT-09: the clustering path imports analyze._tokens — no local fork
    from pathlib import Path
    src = Path(dreams.__file__).read_text(encoding="utf-8")
    assert "from .analyze import _tokens" in src
    assert "def _tokens" not in src


def test_cz_dream_registered_read_only_and_stamped(temp_repo):
    assert "cz_dream" in TOOL_NAMES and "cz_dream" in ops.REGISTRY
    assert ops.REGISTRY["cz_dream"].writes is False
    with _chdir(temp_repo):
        res = ops.run_op("cz_dream")
    assert res["schema_version"] == contract.CONTRACT_SCHEMA_VERSION
    assert res["state"] == "not_ripe"  # fresh fixture: empty journal
