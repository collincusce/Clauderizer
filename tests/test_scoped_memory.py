"""Scoped memory (D-043): filtering, not shadowing.

Phase 1 (write path): Scope/Audience metadata on invariants, audience markers on
lessons, the invariant near-duplicate advisory sharing the lesson advisory's
tokenizer + threshold (INVARIANT-09), and abstract-index round-tripping.
Phase 2 (read path) tests live further down: analyze scope filtering, handoff
audience filtering, curator scope/audience grouping.
"""

from clauderizer import analyze
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.graph import abstract_index

GID = "2026-05-01-bootstrap"


def _paths(repo):
    return P.resolve(repo)


# --- write path: invariants -------------------------------------------------


def test_add_invariant_untagged_is_byte_identical_to_1_3_1(temp_repo):
    paths = _paths(temp_repo)
    r = M.add_invariant(paths, text="Never push secrets", introduced_by="D-002")
    text = paths.doc("INVARIANTS").read_text(encoding="utf-8")
    assert r["ok"]
    assert (f"### {r['id']} — Never push secrets\n"
            "**Introduced by**: D-002\n\nNever push secrets") in text
    assert "**Scope**" not in text and "**Audience**" not in text


def test_add_invariant_writes_scope_and_audience_metadata(temp_repo):
    paths = _paths(temp_repo)
    r = M.add_invariant(paths, text="Logo is never AI-generated",
                        scope=f"gameplan:{GID}", audience="art-director")
    text = paths.doc("INVARIANTS").read_text(encoding="utf-8")
    assert r["ok"]
    assert f"**Scope**: gameplan:{GID}" in text
    assert "**Audience**: art-director" in text


def test_add_invariant_rejects_malformed_scope(temp_repo):
    paths = _paths(temp_repo)
    r = M.add_invariant(paths, text="x", scope="client:acme")
    assert not r["ok"]
    assert "gameplan:<id>" in r["summary"]


def test_add_invariant_warns_on_unknown_gameplan_scope(temp_repo):
    paths = _paths(temp_repo)
    r = M.add_invariant(paths, text="some rule", scope="gameplan:not-a-real-gameplan")
    assert r["ok"]  # advisory, never blocks (INVARIANT-05)
    assert "no GAMEPLAN.md" in r.get("advisory", "")


def test_invariant_near_dup_advisory_fires_on_verbatim_duplicate(temp_repo):
    paths = _paths(temp_repo)
    first = M.add_invariant(
        paths,
        text="The logo is never AI-generated; only the real brand-kit logo asset is used.")
    assert first["ok"] and "related_invariants" not in first
    dup = M.add_invariant(
        paths,
        text="logo never AI-generated — only the real brand-kit logo asset is used")
    assert dup["ok"]  # still appended (INVARIANT-03), advisory only (INVARIANT-05)
    assert any(d["id"] == first["id"] for d in dup.get("related_invariants", []))
    assert "scope" in dup["advisory"]


def test_invariant_near_dup_threshold_single_sourced():
    import inspect

    sig = inspect.signature(analyze.near_duplicate_invariants)
    assert sig.parameters["threshold"].default == analyze._LESSON_DUP_JACCARD


# --- write path: lessons ----------------------------------------------------


def test_add_lesson_audience_marker_and_untagged_identity(temp_repo):
    paths = _paths(temp_repo)
    M.add_lesson(paths, gameplan_id=GID, text="ffmpeg crop has no eval=frame here",
                 audience="coder")
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert "*(audience: coder)*" in idx
    r2 = M.add_lesson(paths, gameplan_id=GID, text="plain untagged lesson")
    idx = (paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    assert f"**{r2['number']}.** plain untagged lesson" in idx
    assert f"**{r2['number']}.** plain untagged lesson *(" not in idx


# --- abstract index round-trip ----------------------------------------------


def test_abstract_index_round_trips_scope_and_audience(temp_repo):
    paths = _paths(temp_repo)
    r = M.add_invariant(paths, text="Benefit-first messaging",
                        scope=f"gameplan:{GID}", audience="copywriter")
    rec = abstract_index.build(paths)["entries"][r["id"]]
    assert rec["scope"] == f"gameplan:{GID}"
    assert rec["audience"] == "copywriter"
    plain = M.add_invariant(paths, text="A global rule about deploys")
    rec2 = abstract_index.build(paths)["entries"][plain["id"]]
    assert rec2["scope"] == "project" and rec2["audience"] == ""


def test_parse_audience_marker():
    assert abstract_index.parse_audience(
        "**3.** text *(audience: copywriter)*") == "copywriter"
    assert abstract_index.parse_audience("**3.** text *(evidence: c1)*") == ""
    assert abstract_index.parse_audience("plain line") == ""


# --- read path: scope filtering (Phase 2) ------------------------------------


def test_analyze_excludes_other_gameplan_scoped_invariants(temp_repo):
    paths = _paths(temp_repo)
    mine = M.add_invariant(paths, text="Render specs drive every export size",
                           scope=f"gameplan:{GID}")
    other = M.add_invariant(paths, text="Render specs drive every export width",
                            scope="gameplan:some-other-campaign")
    glob = M.add_invariant(paths, text="Render specs are versioned entities")
    hits = analyze.analyze(paths, "render specs export size versioned",
                           focus_gameplan=GID)
    got = {h["id"] for h in hits["invariants"]}
    assert mine["id"] in got and glob["id"] in got
    assert other["id"] not in got
    # No focus known -> nothing filtered (surfacing bias).
    unfiltered = analyze.analyze(paths, "render specs export size versioned")
    assert other["id"] in {h["id"] for h in unfiltered["invariants"]}


def test_handoff_invariant_pointer_scope_filtered(temp_repo):
    from clauderizer.rituals import handoff as H

    paths = _paths(temp_repo)
    M.add_invariant(paths, text="Campaign hooks always lead with the pain point",
                    scope="gameplan:someone-elses-campaign")
    ours = M.add_invariant(paths, text="Campaign hooks never bury the brand")
    got = H.relevant_invariant_pointer(
        paths, "campaign hooks pain point brand", gameplan_id=GID)
    assert got is not None
    md, _shown, _total = got
    assert ours["id"] in md
    assert "someone-elses-campaign" not in md and "always lead with the pain point" not in md


# --- read path: audience filtering (Phase 2) ----------------------------------


def test_context_bundle_audience_filtering(temp_repo):
    from clauderizer import config as cfg
    from clauderizer.rituals import handoff as H

    paths = _paths(temp_repo)
    config = cfg.Config.load(paths.config_file)
    M.add_lesson(paths, gameplan_id=GID, text="crop filter gotcha in our ffmpeg build",
                 audience="coder")
    M.add_lesson(paths, gameplan_id=GID, text="talk pain then outcome, never spec cards",
                 audience="copywriter")
    M.add_lesson(paths, gameplan_id=GID, text="untagged lesson for everyone")
    bundle = H.assemble(paths, config, GID, "0", write=False, audience="copywriter")
    md = bundle["handoff_md"]
    assert "talk pain then outcome" in md
    assert "untagged lesson for everyone" in md
    assert "crop filter gotcha" not in md
    # Unfiltered bundle carries everything (the canonical view).
    full = H.assemble(paths, config, GID, "0", write=False)
    assert "crop filter gotcha" in full["handoff_md"]


def test_written_handoff_file_is_never_audience_filtered(temp_repo):
    from clauderizer import config as cfg
    from clauderizer.rituals import handoff as H

    paths = _paths(temp_repo)
    config = cfg.Config.load(paths.config_file)
    M.add_lesson(paths, gameplan_id=GID, text="coder-only render engine gotcha",
                 audience="coder")
    H.assemble(paths, config, GID, "0", write=True)
    written = (paths.gameplan_dir(GID) / "handoffs" / "PHASE-0-HANDOFF.md").read_text(
        encoding="utf-8")
    assert "coder-only render engine gotcha" in written


# --- read path: curator grouping (Phase 2) -------------------------------------


def _write_project_lessons(paths, lines):
    doc = paths.doc("LESSONS")
    body = "# Lessons\n\n## Lessons\n\n" + "\n".join(lines) + "\n"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(body, encoding="utf-8")


def test_curator_never_pairs_across_audiences(temp_repo):
    from clauderizer import telemetry

    paths = _paths(temp_repo)
    near_dup = "prefer explicit output paths over cwd-relative writes in batch jobs"
    _write_project_lessons(paths, [
        f"**L-01.** {near_dup} one *(audience: coder)*",
        f"**L-02.** {near_dup} two *(audience: copywriter)*",
        f"**L-03.** {near_dup} three *(audience: coder)*",
    ])
    health = telemetry.corpus_health(paths)
    pairs = {tuple(p) for p in health["redundant_examples"]}
    assert ("L-01", "L-03") in pairs          # same audience: proposed
    assert ("L-01", "L-02") not in pairs       # cross-audience: never proposed
    assert ("L-02", "L-03") not in pairs
