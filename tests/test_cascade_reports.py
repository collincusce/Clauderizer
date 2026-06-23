"""Phase 1 of engine-structural-robustness: collision-proof cascade report
filenames (gameplan D4; discipline-seams lesson #5).

Two same-day cascades of one entity used to write the same date+entity
filename, silently overwriting the earlier report — context-economics D6
deferred all cascades to gameplan close just to dodge this.
"""

from datetime import datetime, timezone
from pathlib import Path

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.graph import cascade as C
from clauderizer.graph import index
from clauderizer.rituals.status_bundle import pending_cascades, report_sort_key

NOW = datetime(2026, 6, 9, 12, 0, 0, tzinfo=timezone.utc)


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _graph(paths):
    return index.build(paths.docs)


def _an_entity(g) -> str:
    return sorted(e.id for e in g.all())[0]


def test_same_day_cascades_produce_distinct_ordered_reports(temp_repo, tmp_path):
    paths, _ = _ctx(temp_repo)
    g = _graph(paths)
    eid = _an_entity(g)
    rd = tmp_path / "reports"
    r1 = C.run(g, eid, "status a -> b", rd, now=NOW)
    r2 = C.run(g, eid, "status b -> c", rd, now=NOW)
    p1, p2 = Path(r1["report_path"]), Path(r2["report_path"])
    assert p1 != p2
    assert p1.exists() and p2.exists()
    assert p1.name.endswith("-01.md")
    assert p2.name.endswith("-02.md")
    assert "status a -> b" in p1.read_text(encoding="utf-8")  # first report intact


def test_filename_sequences_beside_a_legacy_report(tmp_path):
    rd = tmp_path / "reports"
    rd.mkdir()
    legacy = rd / "2026-06-09-subsys.x.md"
    legacy.write_text("# legacy\n", encoding="utf-8")
    first = C.report_filename("subsys.x", NOW, rd)
    assert first == "2026-06-09-subsys.x-01.md"
    (rd / first).write_text("# one\n", encoding="utf-8")
    assert C.report_filename("subsys.x", NOW, rd) == "2026-06-09-subsys.x-02.md"
    # other entities and other days are independent sequences
    assert C.report_filename("subsys.y", NOW, rd) == "2026-06-09-subsys.y-01.md"


def test_report_sort_key_orders_legacy_before_sequenced():
    names = [
        "2026-06-09-subsys.x-02.md",
        "2026-06-09-subsys.x.md",       # legacy == sequence 0
        "2026-06-09-subsys.x-01.md",
        "2026-06-08-subsys.x-03.md",    # earlier day first regardless of seq
    ]
    ordered = sorted(names, key=report_sort_key)
    assert ordered == [
        "2026-06-08-subsys.x-03.md",
        "2026-06-09-subsys.x.md",
        "2026-06-09-subsys.x-01.md",
        "2026-06-09-subsys.x-02.md",
    ]


def test_resolve_defaults_to_newest_pending_report(temp_repo):
    paths, config = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "Cascade Plan", today="2026-06-08")["gameplan_id"]
    g = _graph(paths)
    eid = _an_entity(g)
    rd = paths.gameplan_dir(gid) / "_cascade-reports"
    C.run(g, eid, "status a -> b", rd, now=NOW)
    C.run(g, eid, "status b -> c", rd, now=NOW)
    pend = pending_cascades(rd)
    assert len(pend) == 2 and pend[-1].endswith("-02.md")
    r = M.resolve_cascade(paths, gameplan_id=gid,
                          updates_applied="no change needed anywhere",
                          updates_deferred="none")
    assert r["report"].endswith("-02.md")


def test_dry_run_writes_no_report(temp_repo, tmp_path):
    paths, _ = _ctx(temp_repo)
    g = _graph(paths)
    rd = tmp_path / "reports"
    r = C.run(g, _an_entity(g), "status a -> b", rd, dry_run=True, now=NOW)
    assert not r["written"]
    assert not rd.exists() or not list(rd.iterdir())


def test_cz_cascade_dedup_finds_pending_report_by_entity(temp_repo, tmp_path):
    # F6: a manual cz_cascade must reuse an existing pending report for the same
    # entity rather than duplicate it — matched by entity, not the transition
    # label (a transition cascades as "status a -> b"; a hand call as "a -> b").
    from clauderizer import ops
    paths, _ = _ctx(temp_repo)
    g = _graph(paths)
    eid = _an_entity(g)
    rd = tmp_path / "reports"
    C.run(g, eid, "status a -> b", rd, now=NOW)  # a real pending report for eid
    found = ops._pending_report_for(rd, eid)
    assert found is not None and found.exists()
    assert ops._pending_report_for(rd, eid + "-not-a-real-suffix") is None  # no prefix collision


def test_resolve_message_names_the_missing_updates_summary(temp_repo):
    # F9: recording verdicts is not enough to close a report — the "Updates
    # applied" summary is also required, and that was non-obvious. The result
    # message must say so explicitly (regardless of whether the entity has deps).
    paths, _ = _ctx(temp_repo)
    gid = M.create_gameplan(paths, "F9 Plan", today="2026-06-08")["gameplan_id"]
    g = _graph(paths)
    rd = paths.gameplan_dir(gid) / "_cascade-reports"
    C.run(g, _an_entity(g), "status a -> b", rd, now=NOW)
    r = M.resolve_cascade(paths, gameplan_id=gid)  # no updates_applied
    assert r["pending"] is True
    assert "updates_applied" in r["summary"]  # the message names exactly what's missing
    r2 = M.resolve_cascade(paths, gameplan_id=gid, updates_applied="none")
    assert "updates_applied" not in r2["summary"]  # the updates gate is now cleared
