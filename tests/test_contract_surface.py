"""The external read-contract additions (PhaseKeep m0 asks):

schema_version stamping (O-05), the monotonic revision (O-03), structured
graph pins (O-16), and the machine-readable ops enumeration (O-15).
"""

import contextlib
import json
import os
from pathlib import Path

from clauderizer import contract, ops, revision
from clauderizer.paths import resolve


@contextlib.contextmanager
def _chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


# --- schema_version (O-05) ----------------------------------------------------


def test_every_op_result_carries_schema_version(temp_repo):
    with _chdir(temp_repo):
        for name in ("cz_status", "cz_gameplans", "cz_graph_query",
                     "cz_list_open_items", "cz_revision"):
            result = ops.REGISTRY[name].fn()
            assert result["schema_version"] == contract.CONTRACT_SCHEMA_VERSION, name


def test_write_op_results_carry_schema_version(temp_repo):
    with _chdir(temp_repo):
        result = ops.REGISTRY["cz_add_open_item"].fn(text="probe item")
        assert result["ok"] is True
        assert result["schema_version"] == contract.CONTRACT_SCHEMA_VERSION


def test_stamp_never_overwrites_an_existing_version():
    assert contract.stamp({"schema_version": "9.9"})["schema_version"] == "9.9"
    assert contract.stamp({"ok": True})["schema_version"] == contract.CONTRACT_SCHEMA_VERSION


def test_op_schema_still_introspects_through_the_stamp_wrapper():
    sch = ops.op_schema("cz_get")
    assert sch["required"] == ["id"]
    assert any(o["name"] == "kind" for o in sch["optional"])


# --- monotonic revision (O-03) ------------------------------------------------


def test_memory_write_bumps_revision(temp_repo):
    paths = resolve(temp_repo)
    assert revision.read(paths.clauderizer_dir) is None
    with _chdir(temp_repo):
        ops.REGISTRY["cz_add_open_item"].fn(text="first")
    rec = revision.read(paths.clauderizer_dir)
    assert rec is not None and rec["revision"] >= 1
    before = rec["revision"]
    with _chdir(temp_repo):
        ops.REGISTRY["cz_add_open_item"].fn(text="second")
    after = revision.read(paths.clauderizer_dir)
    assert after["revision"] > before
    assert after["epoch"] == rec["epoch"]
    assert after["schema_version"] == contract.CONTRACT_SCHEMA_VERSION


def test_noop_write_does_not_bump(temp_repo):
    from clauderizer.markdown import writer

    paths = resolve(temp_repo)
    target = temp_repo / "docs" / "DECISIONS.md"
    writer.replace_text(target, target.read_text(encoding="utf-8"))
    assert revision.read(paths.clauderizer_dir) is None


def test_revision_reset_mints_a_new_epoch(temp_repo):
    paths = resolve(temp_repo)
    first = revision.bump(paths.clauderizer_dir)
    revision.revision_file(paths.clauderizer_dir).unlink()
    second = revision.bump(paths.clauderizer_dir)
    assert second["epoch"] != first["epoch"]


def test_corrupt_revision_file_reads_as_absent(temp_repo):
    paths = resolve(temp_repo)
    revision.revision_file(paths.clauderizer_dir).write_text("{torn", encoding="utf-8")
    assert revision.read(paths.clauderizer_dir) is None
    assert revision.bump(paths.clauderizer_dir)["revision"] == 1


def test_writes_inside_clauderizer_dir_never_bump(temp_repo):
    paths = resolve(temp_repo)
    assert revision.bump_for(paths.telemetry_file) is None
    assert revision.read(paths.clauderizer_dir) is None


def test_status_bundle_carries_the_revision(temp_repo):
    with _chdir(temp_repo):
        ops.REGISTRY["cz_add_open_item"].fn(text="bump it")
        bundle = ops.REGISTRY["cz_status"].fn()
    assert bundle["revision"]["revision"] >= 1


def test_cascade_report_write_bumps_revision(temp_repo):
    paths = resolve(temp_repo)
    with _chdir(temp_repo):
        result = ops.REGISTRY["cz_cascade"].fn(
            entity_id="subsys.calc-engine", transition="status probe")
    assert result["ok"] is True
    assert revision.read(paths.clauderizer_dir)["revision"] >= 1


def test_focus_flip_bumps_revision(temp_repo):
    paths = resolve(temp_repo)
    with _chdir(temp_repo):
        result = ops.REGISTRY["cz_focus"].fn(gameplan_id="2026-05-01-bootstrap")
    assert result["ok"] is True
    assert revision.read(paths.clauderizer_dir) is not None


# --- structured pins (O-16) ---------------------------------------------------


def test_graph_entities_carry_structured_pins(temp_repo):
    with _chdir(temp_repo):
        result = ops.REGISTRY["cz_graph_query"].fn()
    assert result["ok"] is True
    for ent in result["entities"]:
        assert len(ent["depends_on_pins"]) == len(ent["depends_on"])
        for raw, pin in zip(ent["depends_on"], ent["depends_on_pins"]):
            assert raw.startswith(pin["target"])
            if pin["constraint"]:
                assert raw == f"{pin['target']}@{pin['constraint']}"


# --- machine-readable ops enumeration (O-15) ----------------------------------


def test_ops_list_json_via_cli(temp_repo, capsys):
    from clauderizer.cli import main

    with _chdir(temp_repo):
        rc = main(["ops", "--list", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == contract.CONTRACT_SCHEMA_VERSION
    names = {o["op"] for o in payload["ops"]}
    assert names == set(ops.REGISTRY)
    by_name = {o["op"]: o for o in payload["ops"]}
    assert by_name["cz_get"]["required"] == ["id"]
    assert by_name["cz_status"]["writes"] is False


def test_status_json_cli_carries_schema_version(temp_repo, capsys):
    from clauderizer.cli import main

    with _chdir(temp_repo):
        rc = main(["status", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == contract.CONTRACT_SCHEMA_VERSION
    assert "portfolio" in payload
