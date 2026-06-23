"""F10: retiring an entity (a status transition to retired/obsolete) demotes it
in relevance surfacing — a real, append-only alternative to deleting its file."""

from clauderizer import analyze


def test_retired_entity_demoted_below_active_peer():
    q = "auth login session token"
    entries = [
        {"id": "feat.old", "title": "auth login session token", "body": "", "status": "retired"},
        {"id": "feat.live", "title": "auth login session token", "body": "", "status": "active"},
    ]
    ids = [e["id"] for e in analyze.rank_relevant(q, entries, k=5)]
    assert ids.index("feat.live") < ids.index("feat.old")  # active wins the tie


def test_retire_statuses_registered():
    assert {"retired", "obsolete"} <= analyze._STALE_STATUSES
