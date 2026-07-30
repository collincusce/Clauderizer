"""Negative-space close-outs (2.0 P8, D-075/A-002): the procedure text asks
every close-out to declare "What I did not check" — the UNKNOWN residue,
complementing deferred-status/open-items which name the KNOWN residue.

Pins (L-65: an executable seam, not sweep discipline):
  * BOTH copies — the source template and the blessed docs/ render — carry the
    guidance, in the Ending Protocol AND the phase-summary instruction;
  * the honesty clause is present: the engine-side detector is stated
    DEFERRED-UNENFORCED (L-68 clause 5) right where the discipline is asked;
  * the version-parity weld (test_dreams.test_procedure_doc_version_and_
    section_match_engine) keeps the v1.12.0 bump single-sourced; this file
    pins the changelog names the mechanism at that version.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
COPIES = (ROOT / "src" / "clauderizer" / "templates" / "GAMEPLAN-PROCEDURE.md",
          ROOT / "docs" / "gameplans" / "GAMEPLAN-PROCEDURE.md")


def _flat(p: Path) -> str:
    """Whitespace-normalized: the WORDS are pinned, not the line wrap."""
    return re.sub(r"\s+", " ", p.read_text(encoding="utf-8"))


def test_both_copies_carry_the_negative_space_guidance():
    for p in COPIES:
        text = _flat(p)
        assert text.count("What I did not check") >= 3, (
            f"{p}: the negative-space field must be named in the changelog, "
            f"the Ending Protocol, and the phase-summary guidance")
        assert "negative space" in text.lower(), p


def test_the_unenforced_residue_is_stated_not_hidden():
    """L-68 clause 5: asking for a discipline without an executable check is
    honest only while the doc SAYS the check does not exist."""
    for p in COPIES:
        text = _flat(p)
        assert "DEFERRED-UNENFORCED" in text or "deferred-unenforced" in text, p
        assert "L-68" in text, p


def test_changelog_lands_the_mechanism_at_v1_12_0():
    from clauderizer import PROCEDURE_VERSION

    # AT LEAST 1.12.0, not exactly: this test pins where the negative-space
    # mechanism LANDED (the v1.12.0 changelog entry below), and an equality
    # assert here froze the procedure version itself — every later procedure
    # bump would fail a test about a mechanism it did not touch.
    major, minor, _patch = (int(x) for x in PROCEDURE_VERSION.split("."))
    assert (major, minor) >= (1, 12), PROCEDURE_VERSION
    for p in COPIES:
        text = _flat(p)
        assert "**v1.12.0**" in text, p
        # the changelog entry names the field it introduces
        head = text.split("**v1.11.0**", 1)[0]
        assert "What I did not check" in head, p


def test_render_is_the_template_verbatim():
    """The blessed render is modernize's refresh_procedure_doc — a byte copy of
    the shipped template (assets.procedure_text). Editing only one copy is the
    L-65 drift this pin exists to stop."""
    src, render = COPIES
    assert src.read_bytes() == render.read_bytes()
