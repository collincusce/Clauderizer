"""Phase 3 of engine-structural-robustness: lesson state is a trailing
structured marker parsed by one grammar (gameplan D8) — never a substring.

The defect class: a lesson whose *text* contains "(obsolete" was silently
miscounted by the gauge and mispruned from handoff roll-ups, because five
call sites each substring-matched the markers independently.
"""

from clauderizer import config as cfg
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import lesson_state as LS
from clauderizer.rituals import status_bundle
from clauderizer.rituals.handoff import collect_lessons

GID = "2026-05-01-bootstrap"


def _ctx(repo):
    paths = P.resolve(repo)
    return paths, cfg.Config.load(paths.config_file)


# --- the grammar itself --------------------------------------------------------


def test_trailing_markers_parse():
    assert LS.parse_state("**1.** text (obsolete 2026-06-09)") == ("obsolete", "2026-06-09")
    assert LS.parse_state("**2.** text (obsolete 2026-06-09: superseded)") == (
        "obsolete", "2026-06-09: superseded")
    assert LS.parse_state("**3.** text (promoted 2026-06-09: L-04)") == (
        "promoted", "2026-06-09: L-04")
    assert LS.parse_state("~~**4.** struck~~") == ("obsolete", "struck through")


def test_mid_text_mentions_are_inert():
    line = "**5.** never write '(obsolete' by hand mid-line; the tool appends it"
    assert LS.parse_state(line) == ("active", "")
    assert LS.is_active(line)
    line2 = "**6.** the (promoted 2026: L-01) form appears in older docs as prose"
    # marker words mid-line, more text after — still active
    assert LS.is_active(line2 + " so read carefully")


def test_marker_reason_with_parentheses_parses():
    # H-18: a reason containing '()' must not make the line read as active
    # (else the "obsoleted" lesson silently keeps riding every handoff).
    assert LS.parse_state("**8.** t (obsolete 2026-07-16: superseded (see L-50))") == (
        "obsolete", "2026-07-16: superseded (see L-50)")
    assert LS.parse_state(
        "**9.** t (obsolete 2026-07-16: a (x) then (y) done)") == (
        "obsolete", "2026-07-16: a (x) then (y) done")
    # a mid-text balanced-paren mention, not at end, is still inert
    assert LS.is_active(
        "**10.** discusses (obsolete (foo) bar) markers then keeps going as prose")


def test_mark_produces_documented_forms():
    assert LS.mark("**7.** t", "obsolete", "2026-06-09") == "**7.** t (obsolete 2026-06-09)"
    assert LS.mark("**7.** t", "obsolete", "2026-06-09", "why") == (
        "**7.** t (obsolete 2026-06-09: why)")
    assert LS.mark("**7.** t", "promoted", "2026-06-09", "L-09") == (
        "**7.** t (promoted 2026-06-09: L-09)")


# --- the consumers -------------------------------------------------------------

TRICKY = "the marker word (obsolete appears mid-text here) and life goes on"


def test_tricky_lesson_counts_active_and_rolls_up(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_lesson(paths, gameplan_id=GID, text=TRICKY, category="Process")
    n = r["number"]
    idx = paths.gameplan_dir(GID) / "CHAT-HANDOFF-INDEX.md"
    text = idx.read_text(encoding="utf-8")

    rolled, count = collect_lessons(text)
    assert TRICKY in rolled  # survives the roll-up despite the substring

    gauge = status_bundle._memory_gauge(paths, None, text)
    # fixture has 3 active lessons; ours is the 4th — none misclassified
    assert gauge["active_lessons"] == 4
    assert gauge["obsolete_lessons"] == 0

    # the blessed obsolescence still works on it (trailing marker)
    r2 = M.obsolete_lesson(paths, gameplan_id=GID, number=n, reason="done",
                           today="2026-06-09")
    assert r2["ok"] and not r2["already_obsolete"]
    text = idx.read_text(encoding="utf-8")
    rolled, _ = collect_lessons(text)
    assert TRICKY not in rolled
    # idempotent: second call is a recognized no-op
    r3 = M.obsolete_lesson(paths, gameplan_id=GID, number=n, today="2026-06-09")
    assert r3["already_obsolete"]


def test_promote_and_consolidate_reject_only_truly_marked(temp_repo):
    paths, _ = _ctx(temp_repo)
    r = M.add_lesson(paths, gameplan_id=GID, text=TRICKY, category="Process")
    n = r["number"]
    # active despite the substring -> promotable
    p = M.promote_lesson(paths, gameplan_id=GID, number=n, today="2026-06-09")
    assert p["ok"]
    # now truly marked -> consolidate must reject it
    c = M.consolidate_lessons(paths, gameplan_id=GID, numbers=[1, n],
                              text="synthesis", today="2026-06-09")
    assert not c["ok"] and "already obsolete/promoted" in c["summary"]
