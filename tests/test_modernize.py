"""Corpus modernization (D-042): versioned, two-tier — mechanical auto-apply,
memory advisory-only.

The temp_repo fixture is stamped current; staleness tests strip the stamp to
model a legacy corpus.
"""

from pathlib import Path

from clauderizer import PROCEDURE_VERSION
from clauderizer import config as cfg
from clauderizer import modernize
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import status_bundle

MEMORY_DOCS = ("DECISIONS", "INVARIANTS", "LESSONS", "HARDENING")


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _unstamp(repo: Path) -> None:
    cfgf = repo / ".clauderizer" / "config.toml"
    lines = [ln for ln in cfgf.read_text(encoding="utf-8").splitlines()
             if not ln.startswith("procedure_version")]
    cfgf.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _memory_snapshot(paths) -> dict:
    out = {}
    for name in MEMORY_DOCS:
        p = paths.doc(name)
        out[name] = p.read_text(encoding="utf-8") if p.exists() else None
    return out


def test_report_on_stale_corpus_lists_both_tiers(temp_repo):
    _unstamp(temp_repo)
    paths, config = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Ad Push", kind="campaign",
                            today="2026-07-01")["gameplan_id"]
    lid = M.create_gameplan(paths, "Maintenance", kind="loop",
                            today="2026-07-01")["gameplan_id"]
    M.add_invariant(paths, text="The logo is never AI-generated; only the real "
                                "brand-kit logo asset is used.")
    M.add_invariant(paths, text="logo never AI-generated — only the real "
                                "brand-kit logo asset is used")
    rep = modernize.report(paths, config)
    actions = [m["action"] for m in rep["mechanical"]]
    assert rep["stale"] is True
    assert "stamp_procedure_version" in actions
    assert "scaffold_preflight_example:campaign" in actions
    kinds_p = [p["kind"] for p in rep["proposals"]]
    assert "unwired_gates" in kinds_p
    assert "no_deliverables" in kinds_p
    assert "no_standing_conditions" in kinds_p
    assert "near_dup_invariants" in kinds_p
    # the loop-specific proposal names the loop gameplan
    loop_p = next(p for p in rep["proposals"] if p["kind"] == "no_standing_conditions")
    assert loop_p["gameplan"] == lid
    deliv_p = next(p for p in rep["proposals"] if p["kind"] == "no_deliverables")
    assert deliv_p["gameplan"] == gid


def test_report_is_read_only(temp_repo):
    _unstamp(temp_repo)
    paths, config = _ctx(temp_repo)
    M.create_gameplan(paths, "Ad Push", kind="campaign", today="2026-07-01")
    cfg_before = paths.config_file.read_text(encoding="utf-8")
    modernize.report(paths, config)
    assert paths.config_file.read_text(encoding="utf-8") == cfg_before
    assert not (paths.clauderizer_dir / "preflight.campaign.toml.example").exists()


def test_apply_performs_mechanics_and_never_touches_memory(temp_repo):
    _unstamp(temp_repo)
    paths, config = _ctx(temp_repo)
    M.create_gameplan(paths, "Ad Push", kind="campaign", today="2026-07-01")
    M.add_invariant(paths, text="Some standing rule about deploy windows")
    before = _memory_snapshot(paths)
    res = modernize.apply(paths, config)
    assert res["ok"] and "stamp_procedure_version" in res["applied"]
    assert any(a.startswith("scaffold_preflight_example:campaign")
               for a in res["applied"])
    # memory docs byte-identical (the D-042 guarantee)
    assert _memory_snapshot(paths) == before
    # config stamped; example scaffolded inert (commented -> loader yields {})
    config2 = cfg.Config.load(paths.config_file)
    assert config2.procedure_version == PROCEDURE_VERSION
    example = paths.clauderizer_dir / "preflight.campaign.toml.example"
    assert example.exists()
    from clauderizer.rituals.preflight import _load_preflight_gates

    assert _load_preflight_gates(paths, "campaign") == {}  # example is inert
    # idempotent: a second apply finds nothing mechanical for these items
    res2 = modernize.apply(paths, config2)
    assert "stamp_procedure_version" not in res2["applied"]
    assert not any(a.startswith("scaffold_preflight_example") for a in res2["applied"])


def test_apply_refreshes_stale_procedure_doc(temp_repo):
    paths, config = _ctx(temp_repo)
    proc = paths.procedure_file
    proc.parent.mkdir(parents=True, exist_ok=True)
    proc.write_text("# Gameplan Procedure\n\n**Procedure version**: 0.9.0\n",
                    encoding="utf-8")
    rep = modernize.report(paths, config)
    assert any(m["action"] == "refresh_procedure_doc" for m in rep["mechanical"])
    modernize.apply(paths, config)
    refreshed = proc.read_text(encoding="utf-8")
    assert "0.9.0" not in refreshed
    assert f"**Procedure version**: {PROCEDURE_VERSION}" in refreshed


def test_digest_modernization_line_stale_vs_current(temp_repo):
    paths, config = _ctx(temp_repo)
    d = status_bundle.render_digest(status_bundle.compute(paths, config))
    assert "⚙ Modernization" not in d  # stamped current by the fixture
    _unstamp(temp_repo)
    config2 = cfg.Config.load(paths.config_file)
    d2 = status_bundle.render_digest(status_bundle.compute(paths, config2))
    assert ("⚙ Modernization: corpus has no procedure stamp yet; "
            "this engine carries procedure") in d2
    assert "clauderize upgrade" in d2


def test_stale_kind_overlay_proposal(temp_repo):
    paths, config = _ctx(temp_repo)
    M.create_gameplan(paths, "Ad Push", kind="campaign", today="2026-07-01")
    kdir = paths.clauderizer_dir / "kinds"
    kdir.mkdir(parents=True, exist_ok=True)
    # a pre-lifecycle overlay: overrides the packaged campaign kind away
    (kdir / "campaign.toml").write_text(
        'name = "campaign"\n[preflight]\nchecks = ["clean_tree", "virality"]\n',
        encoding="utf-8")
    rep = modernize.report(paths, config)
    stale = [p for p in rep["proposals"] if p["kind"] == "stale_kind_overlay"]
    assert stale and "lifecycle" in stale[0]["detail"]
    # an overlay that keeps a lifecycle raises no proposal
    (kdir / "campaign.toml").write_text(
        'name = "campaign"\n[lifecycle]\nstatuses = ["draft", "done"]\n',
        encoding="utf-8")
    rep2 = modernize.report(paths, config)
    assert not [p for p in rep2["proposals"] if p["kind"] == "stale_kind_overlay"]


def test_cli_upgrade_subcommand(temp_repo, monkeypatch, capsys):
    from clauderizer import cli

    _unstamp(temp_repo)
    monkeypatch.chdir(temp_repo)
    assert cli.main(["upgrade", "--report"]) == 0
    out = capsys.readouterr().out
    assert "would apply: stamp_procedure_version" in out
    assert cli.main(["upgrade"]) == 0
    out = capsys.readouterr().out
    assert "applied: stamp_procedure_version" in out
    # stamped now — digest line clears
    paths, config = _ctx(temp_repo)
    d = status_bundle.render_digest(status_bundle.compute(paths, config))
    assert "⚙ Modernization" not in d
