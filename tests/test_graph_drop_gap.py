"""The graph drop gap and the init spawn-test, carried from 1.14.0 (Phase 3).

Two defects with one shape: a component asserting a clean result from evidence
it never read.

  * `model.from_file` returned a bare `None` for an unreadable entity doc, which
    is the same value it returns for ordinary prose. A BOM'd entity vanished
    from the graph in silence, and `cz_cascade` then answered "0 dependents" —
    indistinguishable from a real leaf, silently voiding D-018.
  * `init` spawn-tested the commands composed at step 0b but never the PORTABLE
    command it actually writes to `.mcp.json`, so it certified wiring it did not
    write and wrote wiring it never certified (task 4.6).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from clauderizer import hosts, hosttargets, model
from clauderizer import paths as P
from clauderizer.graph import index
from clauderizer.model import Drop, Entity

ENTITY = "---\nid: subsys.probe\ntype: subsystem\nversion: 0.1.0\nstatus: active\n---\n\n# Probe\n"


def _write(repo: Path, rel: str, text: str, *, encoding: str = "utf-8") -> Path:
    p = repo / "docs" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding=encoding)
    return p


# --- from_file returns a drop record, not a bare None -------------------------

def test_bomd_entity_doc_is_a_drop_naming_the_path(tmp_path):
    """The motivating case (L-24 class): PowerShell and several Windows editors
    write UTF-8 BOM by default, and the frontmatter fence anchors at offset 0."""
    p = tmp_path / "e.md"
    p.write_text(ENTITY, encoding="utf-8-sig")
    got = Entity.from_file(p)
    assert isinstance(got, Drop)
    assert got.reason == "bom-before-frontmatter"
    assert got.path == p
    assert "BOM" in got.detail or "byte-order mark" in got.detail


def test_undecodable_and_unreadable_are_drops(tmp_path):
    bad = tmp_path / "latin1.md"
    bad.write_bytes(b"---\nid: x\ntype: subsystem\nname: caf\xe9\n---\n")
    assert isinstance(Entity.from_file(bad), Drop)
    assert Entity.from_file(bad).reason == "undecodable"

    missing = Entity.from_file(tmp_path / "nope.md")
    assert isinstance(missing, Drop) and missing.reason == "unreadable"


def test_unterminated_frontmatter_is_a_drop(tmp_path):
    p = tmp_path / "open.md"
    p.write_text("---\nid: subsys.x\ntype: subsystem\n\n# body, fence never closed\n",
                 encoding="utf-8")
    got = Entity.from_file(p)
    assert isinstance(got, Drop) and got.reason == "unterminated-frontmatter"


@pytest.mark.parametrize("block,missing", [
    ("id: subsys.x", "type"),
    ("type: subsystem", "id"),
])
def test_half_an_entity_is_a_drop(tmp_path, block, missing):
    p = tmp_path / "half.md"
    p.write_text(f"---\n{block}\n---\n\n# Half\n", encoding="utf-8")
    got = Entity.from_file(p)
    assert isinstance(got, Drop) and got.reason == "incomplete-frontmatter"
    assert missing in got.detail


@pytest.mark.parametrize("text", [
    "# Just prose\n\nNo frontmatter at all.\n",
    "---\ntitle: A doc\nauthor: someone\n---\n\n# Body\n",
    "",
])
def test_ordinary_docs_are_not_drops(tmp_path, text):
    """No false positives: a doc that never intended to be an entity reports
    nothing, or the count stops being actionable."""
    p = tmp_path / "prose.md"
    p.write_text(text, encoding="utf-8")
    assert Entity.from_file(p) is None


def test_a_valid_entity_still_loads(tmp_path):
    p = tmp_path / "ok.md"
    p.write_text(ENTITY, encoding="utf-8")
    got = Entity.from_file(p)
    assert isinstance(got, Entity) and got.id == "subsys.probe"


# --- the index accumulates drops and collisions -------------------------------

def test_build_accumulates_drops_and_the_accounting_identity_holds(temp_repo):
    before = index.build(temp_repo / "docs").integrity()
    _write(temp_repo, "subsystems/bomd.md", "")
    (temp_repo / "docs" / "subsystems" / "bomd.md").write_text(
        ENTITY, encoding="utf-8-sig")

    report = index.build(temp_repo / "docs").integrity()
    assert report["dropped"] == 1
    assert "bomd.md" in report["drops"][0]["path"]
    assert report["entities_indexed"] == before["entities_indexed"]
    # The criterion's identity, with no collisions in play.
    assert report["entities_indexed"] + report["dropped"] == report["entities_on_disk"]
    assert not report["ok"]


def test_duplicate_ids_are_recorded_and_last_still_wins(temp_repo):
    _write(temp_repo, "subsystems/a-first.md", ENTITY)
    _write(temp_repo, "subsystems/z-second.md", ENTITY)
    g = index.build(temp_repo / "docs")

    assert len(g.collisions) == 1
    c = g.collisions[0]
    assert c.id == "subsys.probe"
    assert c.shadowed.name == "a-first.md" and c.kept.name == "z-second.md"
    # Behavior is unchanged — last one wins, it is merely no longer silent.
    assert g.entities["subsys.probe"].path.name == "z-second.md"


def test_collisions_are_counted_in_the_full_accounting(temp_repo):
    _write(temp_repo, "subsystems/a-first.md", ENTITY)
    _write(temp_repo, "subsystems/z-second.md", ENTITY)
    (temp_repo / "docs" / "subsystems" / "bomd.md").write_text(
        ENTITY.replace("subsys.probe", "subsys.other"), encoding="utf-8-sig")

    g = index.build(temp_repo / "docs")
    r = g.integrity()
    assert (r["entities_indexed"] + r["dropped"] + r["collisions"]
            == r["entities_on_disk"] == g.entity_files_seen)


def test_a_healthy_corpus_reports_ok(temp_repo):
    r = index.build(temp_repo / "docs").integrity()
    assert r["ok"] and r["dropped"] == 0 and r["collisions"] == 0


def test_this_repo_indexes_cleanly():
    """The engine's own corpus must have no dropped or shadowed entity docs."""
    root = Path(__file__).resolve().parents[1]
    r = index.build(root / "docs").integrity()
    assert r["ok"], r["drops"] + r["collision_details"]


# --- surfaced in corpus health and doctor -------------------------------------

def test_corpus_health_surfaces_the_drop(temp_repo):
    from clauderizer import telemetry

    (temp_repo / "docs" / "subsystems" / "bomd.md").write_text(
        ENTITY, encoding="utf-8-sig")
    health = telemetry.corpus_health(P.resolve(temp_repo))
    gi = health["graph_integrity"]
    assert gi["dropped"] == 1 and not gi["ok"]
    assert "GRAPH FAULT" in health["summary"]
    assert "bomd.md" in gi["summary"]


def test_corpus_health_is_quiet_on_a_clean_corpus(temp_repo):
    from clauderizer import telemetry

    health = telemetry.corpus_health(P.resolve(temp_repo))
    assert health["graph_integrity"]["ok"]
    assert "GRAPH FAULT" not in health["summary"]


def test_doctor_names_the_dropped_doc(temp_repo, monkeypatch, capsys):
    (temp_repo / "docs" / "subsystems" / "bomd.md").write_text(
        ENTITY, encoding="utf-8-sig")
    monkeypatch.chdir(temp_repo)
    from clauderizer import cli

    cli.cmd_doctor(type("A", (), {"deep": False})())
    out = capsys.readouterr().out
    assert "entity doc not indexed" in out and "bomd.md" in out


def test_doctor_names_a_duplicate_id(temp_repo, monkeypatch, capsys):
    _write(temp_repo, "subsystems/a-first.md", ENTITY)
    _write(temp_repo, "subsystems/z-second.md", ENTITY)
    monkeypatch.chdir(temp_repo)
    from clauderizer import cli

    cli.cmd_doctor(type("A", (), {"deep": False})())
    out = capsys.readouterr().out
    assert "duplicate entity id" in out and "subsys.probe" in out


# --- cz_cascade stops answering "0 dependents" for a node it never had --------

def test_cz_cascade_on_an_unknown_entity_is_not_ok(temp_repo, monkeypatch):
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops

    res = ops.cz_cascade("subsys.does-not-exist", "0.1.0 -> 0.2.0")
    assert res["ok"] is False
    assert "unknown entity" in res["error"]
    assert "0 dependents" in res["error"], "say WHY the old answer was dangerous"


def test_cz_cascade_points_at_the_drop_that_explains_it(temp_repo, monkeypatch):
    """The payoff of the drop record: the cascade failure names the reason."""
    (temp_repo / "docs" / "subsystems" / "probe.md").write_text(
        ENTITY, encoding="utf-8-sig")
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops

    res = ops.cz_cascade("subsys.probe", "0.1.0 -> 0.2.0")
    assert res["ok"] is False
    assert "failed to index" in res["error"] and "bom" in res["error"].lower()


def test_cz_cascade_on_a_known_entity_still_works(temp_repo, monkeypatch):
    """No regression in the 1.14.0 behavior this touches."""
    monkeypatch.chdir(temp_repo)
    from clauderizer import ops

    res = ops.cz_cascade("subsys.auth", "0.1.0 -> 0.2.0")
    assert res["ok"] is True
    assert res["entity_id"] == "subsys.auth"


# --- init spawn-tests the portable command it actually writes (task 4.6) ------

def _init_multi(repo: Path, monkeypatch, probe: hosts.Probe):
    """Run init wiring every host (so the portable .mcp.json branch is taken),
    with a stubbed probe. Returns (report, list of probed argv)."""
    seen: list[list[str]] = []

    def _probe(argv, **kw):
        seen.append(list(argv))
        return probe if list(argv) == list(hosttargets.PORTABLE_COMMAND) \
            else hosts.Probe("ok", "stub")

    monkeypatch.setattr(hosts, "spawn_probe", _probe)
    # The wrapper leg has its own probe (hook_digest_probe); stub it green so this
    # test measures only the portable-command verdict.
    monkeypatch.setattr(hosts, "hook_digest_probe",
                        lambda argv, **kw: hosts.Probe("ok", "stub digest"))
    monkeypatch.delenv("CLAUDERIZER_NO_SPAWN_PROBE", raising=False)
    from clauderizer.scaffold.init import init

    return init(repo), seen                    # bare init = multi-host default


def test_init_probes_the_portable_command(tmp_path, monkeypatch):
    report, seen = _init_multi(tmp_path / "r", monkeypatch, hosts.Probe("ok", "fine"))
    assert list(hosttargets.PORTABLE_COMMAND) in seen, (
        "init must certify the wiring it actually writes, not only what it composed")
    assert not [w for w in report.warnings if "portable MCP" in w]


@pytest.mark.parametrize("status,detail", [
    ("fail", "network unreachable"),
    ("unverifiable", "no interop path"),
])
def test_a_failing_portable_probe_warns_and_still_installs(
        tmp_path, monkeypatch, status, detail):
    """Never WiringRefused: the portable form is `uvx --from clauderizer[mcp]`,
    which needs the network on a cold cache — an offline or proxied first run
    must still install, and simply learn in-band that this leg is uncertified."""
    repo = tmp_path / "r"
    report, _ = _init_multi(repo, monkeypatch, hosts.Probe(status, detail))

    assert (repo / ".clauderizer" / "config.toml").exists(), "it must still install"
    assert (repo / ".mcp.json").exists(), "the wiring is still written"
    warned = [w for w in report.warnings if "portable MCP wiring" in w]
    assert warned and status in warned[0] and detail in warned[0]
    assert "offline first run must still install" in warned[0]


def test_no_spawn_test_skips_the_portable_probe(tmp_path, monkeypatch):
    seen: list[list[str]] = []
    monkeypatch.setattr(hosts, "spawn_probe",
                        lambda argv, **kw: seen.append(list(argv)) or hosts.Probe("ok", ""))
    from clauderizer.scaffold.init import init

    init(tmp_path / "r", spawn_test=False)
    assert list(hosttargets.PORTABLE_COMMAND) not in seen
