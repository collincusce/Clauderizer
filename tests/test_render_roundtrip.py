"""Every corpus kind survives the round trip: real writer -> real reader.

L-52 made executable ("every file the engine writes must round-trip through its
own parser… an engine can read its own corruption indefinitely"). The hardening
register was worse than L-52 predicted: the engine could not read its own
*render* at all — 21 findings reported ``active``/``date: null`` against a file
recording 17 resolved.

This is the regression oracle Phases 1 and 2 are measured against. Those phases
rebuild ``markdown/writer.py`` and the ``mutations.py`` render sites; if a write
stops round-tripping, it fails here rather than silently landing in append-only
memory that has no repair op.

Each case writes through the op an agent actually calls and reads through the op
an agent actually calls — never through a private helper, and never by grepping
the markdown, because grepping the file is what the broken readers already did.
"""

from __future__ import annotations

import pytest

from clauderizer import config as cfg
from clauderizer import listing
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import sections

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _one(records: list[dict], entry_id: str) -> dict:
    hit = [r for r in records if r["id"] == entry_id]
    assert hit, f"{entry_id} was written but the reader never returned it"
    assert len(hit) == 1, f"{entry_id} came back {len(hit)} times — duplicate entry"
    return hit[0]


# --- decision -----------------------------------------------------------------

def test_decision_round_trips(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_decision(paths, title="Round-trip the decision", context="c",
                       decision="d", consequences="q", today="2026-07-25")
    rec = _one(listing.decisions(paths), r["id"])
    assert rec["title"] == "Round-trip the decision"
    assert rec["status"] == "active"
    assert rec["status_source"] == sections.STATUS_PARSED, (
        "add_decision writes a Status line, so the reader must PARSE it, not "
        "arrive at 'active' by defaulting (D-065)"
    )
    assert rec["date"] == "2026-07-25"


def test_superseding_decision_round_trips_both_sides(temp_repo):
    """The supersession back-ref is the one status transition the corpus writes
    automatically; both entries must read back correctly."""
    paths, _ = _ctx(temp_repo)
    first = M.add_decision(paths, title="Original", context="c", decision="d",
                           consequences="q", today="2026-07-25")
    second = M.add_decision(paths, title="Replacement", context="c", decision="d",
                            consequences="q", supersedes=first["id"],
                            today="2026-07-25")
    recs = listing.decisions(paths)
    old, new = _one(recs, first["id"]), _one(recs, second["id"])
    assert old["status"] == "superseded"
    assert old["status_source"] == sections.STATUS_PARSED
    assert old["superseded_by"] == second["id"]
    assert new["supersedes"] == first["id"]
    assert new["status"] == "active"


# --- invariant ----------------------------------------------------------------

def test_invariant_round_trips(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_invariant(paths, text="Writes round-trip through their own reader.")
    rec = _one(listing.invariants(paths), r["id"])
    assert rec["title"].startswith("Writes round-trip")
    # Invariants carry no Status line by design — so the reader must report
    # 'defaulted', which is the honest answer, not a silent 'active'.
    assert rec["status"] == "active"
    assert rec["status_source"] == sections.STATUS_DEFAULTED


# --- finding (the kind that was actually broken) ------------------------------

@pytest.mark.parametrize("status", ["open", "resolved"])
def test_finding_round_trips_for_every_status(temp_repo, status):
    """The live defect: add_finding renders '- **Status**:' as a list bullet and
    two of three readers could not match it."""
    paths, _ = _ctx(temp_repo)
    r = M.add_finding(paths, title=f"Finding that is {status}", severity="medium",
                      impact="i", status=status, today="2026-07-25")
    rec = _one(listing.findings(paths), r["id"])
    assert rec["status"] == status, (
        f"wrote status={status!r}, read back {rec['status']!r} — the register "
        "cannot read its own render"
    )
    assert rec["status_source"] == sections.STATUS_PARSED
    assert rec["date"] == "2026-07-25"


def test_resolving_a_finding_round_trips(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_finding(paths, title="To be resolved", severity="high", impact="i",
                      today="2026-07-25")
    assert _one(listing.findings(paths), r["id"])["status"] == "open"
    M.resolve_finding(paths, finding_id=r["id"], note="fixed in P0",
                      today="2026-07-26")
    rec = _one(listing.findings(paths), r["id"])
    assert rec["status"] == "resolved", (
        "resolve_finding wrote a status no reader could read back — this is "
        "exactly the pre-fix behavior"
    )
    assert rec["date"] == "2026-07-26"


# --- lesson -------------------------------------------------------------------

def test_lesson_round_trips(temp_repo):
    paths, config = _ctx(temp_repo)
    text = "Round-tripping is the load-bearing test for every mutation."
    M.add_lesson(paths, gameplan_id=GID, text=text)
    recs = listing.lessons(paths, config, GID)
    assert any(text in (r.get("text") or r.get("title") or "") for r in recs), (
        f"lesson written but not readable back; got {recs!r}"
    )


# --- correction ---------------------------------------------------------------

def test_correction_round_trips(temp_repo):
    paths, _ = _ctx(temp_repo)
    M.add_correction(paths, gameplan_id=GID, phase="0",
                     gameplan_said="the plan said this",
                     actually="reality was this", why="because of that")
    recs = listing.corrections(paths, GID)
    assert recs, "correction written but the reader returned nothing"
    joined = " ".join(str(r) for r in recs)
    assert "reality was this" in joined


# --- the property Phases 1 and 2 must not break -------------------------------

def test_every_kind_is_readable_after_a_mixed_write_batch(temp_repo):
    """Writes interleaved across kinds must not corrupt each other's documents.

    Phase 1 reroutes every markdown byte-write through one atomic path and
    Phase 2 normalizes every render site; this asserts the whole surface still
    reads back afterwards, which no single-kind test would catch.
    """
    paths, config = _ctx(temp_repo)
    d = M.add_decision(paths, title="Mixed batch decision", context="c",
                       decision="d", consequences="q", today="2026-07-25")
    i = M.add_invariant(paths, text="Mixed batch invariant.")
    f = M.add_finding(paths, title="Mixed batch finding", severity="low",
                      impact="i", today="2026-07-25")
    M.add_lesson(paths, gameplan_id=GID, text="Mixed batch lesson.")
    M.add_correction(paths, gameplan_id=GID, phase="0", gameplan_said="a",
                     actually="b", why="c")

    assert _one(listing.decisions(paths), d["id"])["title"] == "Mixed batch decision"
    assert _one(listing.invariants(paths), i["id"])["id"] == i["id"]
    assert _one(listing.findings(paths), f["id"])["status"] == "open"
    assert listing.lessons(paths, config, GID)
    assert listing.corrections(paths, GID)

    # No kind may leak a 'defaulted' status where its writer emits a Status line.
    for rec in listing.decisions(paths) + listing.findings(paths):
        if rec["id"] in {d["id"], f["id"]}:
            assert rec["status_source"] == sections.STATUS_PARSED, rec
