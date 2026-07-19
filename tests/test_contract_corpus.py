"""The external contract-break gate (phasekeep proposal 15.5).

``tests/fixtures/contract_corpus/`` is the fixture corpus the PhaseKeep
contract client develops against, captured from real repos of every gameplan
kind on the released 1.12.0 surface (its scripts/capture-fixtures.js). This
suite replays it against the CURRENT engine so a contract break fails CI here
BEFORE a release ships it to external clients:

1. every corpus payload still parses and matches the engine's schema MAJOR —
   a deliberate major bump must regenerate the corpus in the same change;
2. current output stays a key-SUPERSET of the corpus (the additive-only
   compatibility promise of contract schema 1.x);
3. every op the corpus enumerates still exists — verbs are never removed
   within a major.
"""

import contextlib
import json
import os
from pathlib import Path

import pytest

from clauderizer import contract, ops

CORPUS = Path(__file__).parent / "fixtures" / "contract_corpus"

_MAJOR = contract.CONTRACT_SCHEMA_VERSION.split(".")[0]


@contextlib.contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def _corpus_payloads():
    for path in sorted(CORPUS.rglob("*.json")):
        if path.name in ("MANIFEST.json", "revision-artifact.json"):
            continue
        yield path, json.loads(path.read_text(encoding="utf-8"))


def test_corpus_present_and_parses():
    payloads = list(_corpus_payloads())
    assert len(payloads) >= 60, "corpus missing or gutted"


def test_every_corpus_payload_matches_the_engine_schema_major():
    for path, data in _corpus_payloads():
        emitted = data.get("schema_version")
        assert emitted is not None, f"{path} carries no schema_version"
        assert str(emitted).split(".")[0] == _MAJOR, (
            f"{path} was captured at schema {emitted}; engine now declares "
            f"{contract.CONTRACT_SCHEMA_VERSION} — a major break must "
            f"regenerate the corpus in the same change (phasekeep "
            f"scripts/capture-fixtures.js)")


def test_current_output_is_a_key_superset_of_the_corpus(temp_repo):
    """The additive-only promise, checked structurally: keys clients saw at
    capture time never vanish within a major."""
    with _chdir(temp_repo):
        live = {
            "status.json": ops.run_op("cz_status"),
            "gameplans.json": ops.run_op("cz_gameplans"),
        }
        for op_name in ("cz_graph_query", "cz_list_open_items",
                        "cz_list_decisions", "cz_list_invariants",
                        "cz_list_findings", "cz_list_lessons",
                        "cz_list_corrections", "cz_list_amendments",
                        "cz_phase_detail", "cz_list_cascade_reports",
                        "cz_docs_index", "cz_assignments", "cz_revision"):
            live[f"ops/{op_name}.json"] = ops.run_op(op_name)

    corpus_rich = CORPUS / "driven-rich"
    checked = 0
    for rel, live_payload in live.items():
        fixture = corpus_rich / rel
        assert fixture.exists(), f"corpus lost {rel}"
        captured = json.loads(fixture.read_text(encoding="utf-8"))
        missing = set(captured) - set(live_payload)
        assert not missing, (
            f"{rel}: keys {sorted(missing)} were in the captured contract "
            f"but the engine no longer emits them — removing fields breaks "
            f"external clients within a major")
        checked += 1
    assert checked >= 15


def test_every_captured_op_still_exists():
    ops_list = json.loads(
        (CORPUS / "driven-rich" / "ops-list.json").read_text(encoding="utf-8"))
    captured_ops = {entry["op"] for entry in ops_list["ops"]}
    missing = captured_ops - set(ops.REGISTRY)
    assert not missing, (
        f"ops {sorted(missing)} existed at capture time but are gone — "
        f"verbs are never removed within a schema major")


def test_doctor_exit_codes_documented_by_the_corpus():
    # The corpus records the exit-code contract as live captures (1/2/3);
    # this pins their presence so the contract's diagnostic surface stays
    # covered evidence, not prose.
    for name in ("exit-1.txt", "exit-2.txt", "exit-3.txt"):
        cap = CORPUS.parent / "contract_corpus" / "doctor" / name
        if not cap.exists():
            pytest.skip("doctor captures not part of this corpus copy")
        first = cap.read_text(encoding="utf-8").splitlines()[0]
        assert first == f"# exit={name[5]}"
