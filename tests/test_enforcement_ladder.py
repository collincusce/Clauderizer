"""The enforcement ladder's pin (2.0 P4, D-076).

Deliberately MINIMAL parsed surface — row name + tier column only — so
hand-edited-doc format drift does not train anyone to weaken the test. What is
pinned: the tier vocabulary is exactly the four defined tokens; every mechanism
phases 0–3 landed has a row; the fleet rows exist (A-001's cannot-drop rule);
and the doc restates D-066 and INVARIANT-05 verbatim, because a ladder that
paraphrases the law becomes the vector for the enforcement-creep it exists to
prevent.
"""

from __future__ import annotations

import re
from pathlib import Path

DOC = Path(__file__).parent.parent / "docs" / "ENFORCEMENT.md"

TIERS = {"hard-NORMALIZE", "preflight-blocking", "advisory", "instructions-floor"}


def _rows() -> list[tuple[str, str]]:
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Discipline", "") or set(cells[0]) <= {"-"}:
            continue
        rows.append((cells[0], cells[1]))
    return rows


def test_every_tier_token_is_one_of_the_four_defined():
    rows = _rows()
    assert len(rows) >= 25, "the ladder shrank — a discipline row was dropped"
    bad = [(n, t) for n, t in rows if t not in TIERS]
    assert not bad, f"undefined tier token(s): {bad} — the vocabulary is {sorted(TIERS)}"


def test_the_nine_phase_0_to_3_mechanisms_all_have_rows():
    names = " || ".join(n.lower() for n, _ in _rows())
    for needle in ("terminal vocabulary", "epistemics", "stranded", "interrupted",
                   "refusal", "live-state stamp", "budget", "receipts",
                   "merge-base", "correction write-back"):
        assert needle in names, f"no ladder row for the landed mechanism: {needle}"


def test_fleet_rows_exist_per_a001():
    rows = dict((n.lower(), t) for n, t in _rows())
    hub = next((t for n, t in rows.items() if "hub-and-spoke" in n), None)
    own = next((t for n, t in rows.items() if "assignment ownership" in n), None)
    assert hub == "instructions-floor" and own == "advisory"


def _flat() -> str:
    """Whitespace-normalized doc text: verbatim means the WORDS, not the wrap."""
    return re.sub(r"\s+", " ", DOC.read_text(encoding="utf-8"))


def test_d066_and_invariant05_are_restated_verbatim():
    text = _flat()
    assert ("PREFER NEUTRALIZE OVER REJECT, so no write is ever lost "
            "(INVARIANT-03) and no mutation gains a hard block (INVARIANT-05)"
            ) in text
    assert ("they surface findings in tool results for the agent to act on, "
            "and MUST NOT hard-block a mutation or phase transition, nor "
            "introduce an enable/disable config flag. The engine surfaces "
            "candidates; the agent decides.") in text


def test_preflight_real_semantics_stated_and_no_capability_digest_line():
    text = _flat()
    assert "blocking by default" in text and "preflight_advisory" in text  # D-024
    # the D-076 defense: disclosure rides the instructions floor, never the digest
    assert "no capability line in the digest" in text
    from clauderizer.rituals import status_bundle
    src = Path(status_bundle.__file__).read_text(encoding="utf-8")
    assert "negative-capability" not in src and "capability line" not in src
