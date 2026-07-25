"""No caller string can forge an entry, burn an id, or escape a block (D-066).

The highest-severity defect in the evidence-traversal release. No structured
write applied any well-formedness check to caller strings, so through the real
``clauderize ops`` path::

    add_decision(title="ok\\n\\n### D-900 — FAKE\\n\\n**Context**: forged")

returned ``ok: true``, created a genuine-looking ``D-900``, **absorbed the true
entry's body** so it rendered empty, and advanced the next id to ``D-901`` —
899 ids burned irreversibly, in an append-only corpus (INVARIANT-03) with no
repair op.

No adversary is required. A fenced code block containing a heading renders
correctly to a human and is enough, and this repo writes those constantly.

The contract is NORMALIZE, never reject: no write is lost and no mutation gains a
hard block. This is D-007/INVARIANT-02 well-formedness, **not** a discipline gate
— INVARIANT-05 enumerates exactly three gates, and ``dreams.validate`` plus
D-058's write-time schema validation are the shipped precedent that a blessed
write may check its own input.
"""

from __future__ import annotations

import re

from clauderizer import analyze
from clauderizer import config as cfg
from clauderizer import listing
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import frontmatter, sections

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


def _decision_entries(paths) -> list[dict]:
    _fm, body = frontmatter.split(
        (paths.docs / "DECISIONS.md").read_text(encoding="utf-8"))
    return analyze.parse_entries(body, "Decisions")


def test_forged_heading(temp_repo):
    """THE case. One heading in, one heading out, and no id burned."""
    paths, _ = _ctx(temp_repo)
    before = _decision_entries(paths)
    before_ids = {e["id"] for e in before}

    r = M.add_decision(
        paths,
        title="ok\n\n### D-900 — FAKE\n\n**Context**: forged",
        context="c", decision="d", consequences="q", today="2026-07-25")

    after = _decision_entries(paths)
    new = [e for e in after if e["id"] not in before_ids]
    assert len(new) == 1, f"expected exactly one new entry, got {[e['id'] for e in new]}"
    assert new[0]["id"] == r["id"]
    assert "D-900" not in {e["id"] for e in after}, "a fake decision was forged"
    # The next allocated id must be sequential, not 901.
    r2 = M.add_decision(paths, title="next", context="c", decision="d",
                        consequences="q", today="2026-07-25")
    n1 = int(r["id"].split("-")[1])
    n2 = int(r2["id"].split("-")[1])
    assert n2 == n1 + 1, f"id sequence jumped: {r['id']} -> {r2['id']}"
    # And the victim entry keeps its own body.
    assert "forged" in new[0]["title"] or "forged" in new[0]["body"]
    assert new[0]["status"] == "active"


def test_accident_fenced_heading(temp_repo):
    """No adversary needed: a quoted heading inside a fenced block."""
    paths, _ = _ctx(temp_repo)
    before = len(_decision_entries(paths))
    M.add_decision(paths, title="Quoting markdown",
                   context="the doc showed:\n```\n### D-999 — example\n```\nwhich we copied",
                   decision="d", consequences="q", today="2026-07-25")
    assert len(_decision_entries(paths)) == before + 1


def test_empty_title_stays_reachable(temp_repo):
    """An unreachable entry consumes an id forever — worse than a bad title."""
    paths, _ = _ctx(temp_repo)
    for bad in ("", "   ", "\n\n"):
        r = M.add_decision(paths, title=bad, context="c", decision="d",
                           consequences="q", today="2026-07-25")
        rec = [d for d in listing.decisions(paths) if d["id"] == r["id"]]
        assert rec, f"id {r['id']} allocated but unreachable by the reader"
        assert rec[0]["title"].strip(), "title rendered empty"


def test_lesson_number_not_burned(temp_repo):
    """A quoted '**99.**' must not shift the numbered sequence."""
    paths, _ = _ctx(temp_repo)
    a = M.add_lesson(paths, gameplan_id=GID,
                     text="the roll-up showed:\n**99.** a quoted line")
    b = M.add_lesson(paths, gameplan_id=GID, text="the next lesson")
    assert b["number"] == a["number"] + 1, f"{a['number']} -> {b['number']}"


def test_phase_table_stays_contiguous_and_transitionable(temp_repo):
    """H-02, marked resolved and live: a '|' ate half the name and a newline
    made the phase permanently untransitionable, with no rename op to recover."""
    paths, _ = _ctx(temp_repo)
    for name in ("Ranker | normalize", "two\nlines"):
        r = M.add_phase(paths, gameplan_id=GID, name=name, goal="g")
        n = r["phase"]
        # The status row lands in the two trackers, not GAMEPLAN.md.
        for fname in ("CHAT-HANDOFF-INDEX.md", "PHASE-STATUS.md"):
            text = (paths.gameplan_dir(GID) / fname).read_text(encoding="utf-8")
            rows = [l for l in text.splitlines() if l.startswith(f"| {n} |")]
            assert len(rows) == 1, f"{fname}: phase {n} row split: {rows}"
            header = next(l for l in text.splitlines()
                          if l.lstrip().startswith("| Phase"))
            # Count UNESCAPED pipes: "\\|" is a literal pipe inside a cell, not
            # a delimiter, so the row stays a 6-cell row and renders correctly.
            def _cells(line: str) -> int:
                return len(re.split(r"(?<!\\)\|", line))
            assert _cells(rows[0]) == _cells(header), (
                f"{fname} cell-count drift: row={rows[0]!r} header={header!r}")
        out = M.transition_phase(paths, gameplan_id=GID, phase_n=str(n),
                                 to_status="complete", today="2026-07-25")
        assert out["ok"], f"phase {n} named {name!r} is untransitionable: {out}"


def test_handoff_marker_cannot_escape_its_block(temp_repo):
    """A body containing the marker permanently escapes the block, voiding
    D-008's byte-for-byte guarantee with no op to undo it."""
    paths, _ = _ctx(temp_repo)
    M.add_decision(paths, title="Marker case",
                   context="the block is delimited by clauderizer:handoff markers",
                   decision="d", consequences="q", today="2026-07-25")
    text = (paths.docs / "DECISIONS.md").read_text(encoding="utf-8")
    # The literal marker string must not appear verbatim in tracked prose.
    assert "clauderizer:handoff" not in text.replace("​", "​")  # noqa
    assert "clauderizer​:handoff" in text


def test_invariant_multiline_contract_is_preserved(temp_repo):
    """add_invariant documents first-line-is-title; normalization must not
    change that, and a byte-identical rewrite must stay a no-op."""
    paths, _ = _ctx(temp_repo)
    r = M.add_invariant(paths, text="Title line here.\n\nA longer body follows.")
    rec = [i for i in listing.invariants(paths) if i["id"] == r["id"]][0]
    assert rec["title"] == "Title line here."
    from clauderizer.markdown import writer
    path = paths.docs / "INVARIANTS.md"
    assert writer._write_if_changed(path, path.read_text(encoding="utf-8")) is False


def test_normalization_is_idempotent(temp_repo):
    """Runs before the diff, so the same input twice is a no-op — not a second
    round of escaping."""
    paths, _ = _ctx(temp_repo)
    body = "note:\n### D-777 — quoted\nand more"
    M.add_decision(paths, title="Idem", context=body, decision="d",
                   consequences="q", today="2026-07-25")
    once = (paths.docs / "DECISIONS.md").read_text(encoding="utf-8")
    assert once.count("\\###") == 1
    assert "\\\\###" not in once, "double-escaped on a single pass"


def test_pii_shapes_warn_but_still_write(temp_repo):
    """D-058's own justification is that INVARIANT-03 makes retroactive
    redaction impossible — yet the lint shipped only on the gitignored journal
    where deletion is trivial. Advisory here, never a block."""
    paths, _ = _ctx(temp_repo)
    r = M.add_decision(paths, title="Has a key",
                       context="the id is AKIAIOSFODNN7EXAMPLE",
                       decision="d", consequences="q", today="2026-07-25")
    assert r["ok"] is True, "the write must still land (INVARIANT-03/05)"
    assert [d for d in listing.decisions(paths) if d["id"] == r["id"]]
