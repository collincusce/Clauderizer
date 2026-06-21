"""Decision supersession lifecycle (Phase 4): bidirectional back-refs + status.

A new decision that supersedes ``D-X`` records the forward ``**Supersedes**`` AND
writes the missing reverse link — ``D-X`` gains a ``**Superseded by**`` pointer and
its ``**Status**`` flips to ``superseded`` (annotated IN PLACE; INVARIANT-03: memory
is never deleted). The analyze ranker then demotes the superseded decision below its
active replacement, so the agent is handed the current decision, not a stale one.
"""

from clauderizer import analyze
from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import writer


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _decisions_text(paths):
    return writer.full_text(paths.doc("DECISIONS"))


def _block(text: str, decision_id: str) -> str:
    """The raw markdown of a single ``### D-NNN —`` entry (up to the next entry)."""
    return text.split(f"### {decision_id} —")[1].split("\n### ")[0]


def test_superseding_writes_back_ref_and_flips_status(temp_repo):
    """(a) Superseding D-X writes a ``Superseded by`` back-ref on D-X and sets its
    status superseded — and (d) D-X is annotated in place, never deleted."""
    paths, _ = _ctx(temp_repo)
    old = M.add_decision(paths, title="Use REST for the public API",
                         context="public API transport choice",
                         decision="expose a REST JSON API",
                         consequences="simple clients", today="2026-06-20")["id"]
    new = M.add_decision(paths, title="Switch the public API to GraphQL",
                         context="public API transport choice",
                         decision="expose a GraphQL API",
                         consequences="flexible typed queries",
                         supersedes=old, today="2026-06-20")["id"]
    text = _decisions_text(paths)
    old_block = _block(text, old)
    # the reverse link the flat-status model lacked
    assert f"**Superseded by**: {new} (2026-06-20)" in old_block
    assert "**Status**: superseded (2026-06-20)" in old_block
    # (d) append-only: the predecessor entry is still present, not removed
    assert f"### {old} — Use REST for the public API" in text
    assert "expose a REST JSON API" in text  # its original content is intact


def test_new_decision_is_active_with_a_date(temp_repo):
    """(b) The new (superseding) decision is status active with a date; a plain
    decision is born active too."""
    paths, _ = _ctx(temp_repo)
    plain = M.add_decision(paths, title="Adopt Stripe", context="payment vendor",
                           decision="integrate Stripe Billing",
                           consequences="per-transaction fees", today="2026-06-20")["id"]
    new = M.add_decision(paths, title="Switch the public API to GraphQL",
                         context="public API transport choice",
                         decision="expose a GraphQL API",
                         consequences="typed queries",
                         supersedes=plain, today="2026-06-20")["id"]
    text = _decisions_text(paths)
    assert "**Status**: active (2026-06-20)" in _block(text, new)
    # parse_entries reflects the lifecycle state
    entries = {e["id"]: e for e in analyze.parse_entries(text, "Decisions")}
    assert entries[new]["status"] == "active"
    assert entries[plain]["status"] == "superseded"  # the one it replaced


def test_supersession_is_idempotent_and_append_only(temp_repo):
    """Re-applying the same supersession does not double-write the back-ref/status
    (idempotent) and never deletes the predecessor (append-only, INVARIANT-03)."""
    paths, _ = _ctx(temp_repo)
    old = M.add_decision(paths, title="Use REST", context="transport",
                         decision="REST", consequences="simple", today="2026-06-20")["id"]
    new = M.add_decision(paths, title="Use GraphQL", context="transport",
                         decision="GraphQL", consequences="typed",
                         supersedes=old, today="2026-06-20")["id"]
    before = _decisions_text(paths)
    # a second, identical mark is a no-op: file unchanged, fields not duplicated
    changed = M._mark_superseded(paths.doc("DECISIONS"), "Decisions", old, new, "2026-06-20")
    assert changed is False
    after = _decisions_text(paths)
    assert after == before
    old_block = _block(after, old)
    assert old_block.count("**Superseded by**:") == 1
    assert old_block.count("**Status**:") == 1
    assert f"### {old} —" in after  # still present


def test_superseded_decision_ranks_below_its_replacement(temp_repo):
    """(c) For a query that matches both, the superseded decision ranks BELOW its
    active replacement — the knowledge-updates contradiction is gone."""
    paths, _ = _ctx(temp_repo)
    old = M.add_decision(paths, title="Use REST for the public API",
                         context="public API transport choice",
                         decision="expose a REST JSON API",
                         consequences="simple clients", today="2026-06-20")["id"]
    new = M.add_decision(paths, title="Switch the public API to GraphQL",
                         context="public API transport choice; REST is superseded",
                         decision="expose a GraphQL API",
                         consequences="flexible typed queries",
                         supersedes=old, today="2026-06-20")["id"]
    res = analyze.analyze(paths, "what is the current public API transport choice")
    ids = [d["id"] for d in res["decisions"]]
    assert new in ids and old in ids
    assert ids.index(new) < ids.index(old)  # active replacement outranks the stale one
    # the surfaced stale entry is annotated as superseded for the agent
    stale = next(d for d in res["decisions"] if d["id"] == old)
    assert stale.get("status") == "superseded"


def test_superseding_an_entry_without_a_prior_status_line(temp_repo):
    """An older decision with no ``**Status**`` line (e.g. the fixture's D-001) still
    gains both the back-ref and a fresh superseded Status when superseded."""
    paths, _ = _ctx(temp_repo)
    # fixture D-001 "Adopt Clauderizer" has no Status field
    assert "**Status**" not in _block(_decisions_text(paths), "D-001")
    new = M.add_decision(paths, title="Replace the memory engine",
                         context="memory engine choice",
                         decision="adopt a new engine", consequences="migration",
                         supersedes="D-001", today="2026-06-20")["id"]
    block = _block(_decisions_text(paths), "D-001")
    assert f"**Superseded by**: {new} (2026-06-20)" in block
    assert "**Status**: superseded (2026-06-20)" in block
    assert "Use Clauderizer." in block  # original content untouched


def test_mark_superseded_missing_target_is_a_noop(temp_repo):
    """A supersedes pointer to a non-existent decision id is advisory, not an error:
    the new decision is still written; nothing is back-reffed."""
    paths, _ = _ctx(temp_repo)
    r = M.add_decision(paths, title="A decision", context="c", decision="d",
                       consequences="x", supersedes="D-999", today="2026-06-20")
    assert r["ok"] is True
    assert "superseded" not in r  # no target found -> no back-ref recorded
    assert M._mark_superseded(paths.doc("DECISIONS"), "Decisions", "D-999",
                              r["id"], "2026-06-20") is False
