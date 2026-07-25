"""The nudge fires on the cost it names, and the register stops being write-only
(H-26 + the aging detector).

H-26, measured: the digest warned "N project lessons (> 20) — docs/LESSONS.md
rides in every handoff" — thresholding a COUNT while naming TOKENS as the cost.
A coverage-gated re-distill then took the corpus 26 → 20 entries and made it
*larger* (+1.1% chars, +14% handoff), because the handoff renders the top five in
full and a synthesis outranks its own sources. The warning went quiet by way of
work that made the warned-about thing worse.

The aging half is the same shape one level up: the register listed open findings
but never said how long they had been open, so a finding carried across four
releases read exactly like one opened an hour ago.
"""

from __future__ import annotations

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.rituals import status_bundle as S

BIG = "x" * 400


def _lessons(repo, n: int, size: int = 400) -> None:
    doc = repo / "docs" / "LESSONS.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"**L-{i:02d}.** {'w' * size}\n\n" for i in range(1, n + 1))
    doc.write_text("# Lessons\n\n## Lessons\n\n" + body, encoding="utf-8")


def _gauge(repo):
    paths = P.resolve(repo)
    return S.compute(paths, cfg.Config.load(paths.config_file))["memory"]


# --- the trigger is tokens, not entries ---------------------------------------

def test_many_short_lessons_stay_quiet_when_they_are_cheap(temp_repo, monkeypatch):
    """The count alone must not fire: 40 tiny entries cost little and the nudge's
    whole justification is handoff weight."""
    monkeypatch.setattr(S, "PROJECT_LESSON_TOKENS_WARN", 5000)
    _lessons(temp_repo, 40, size=20)
    g = _gauge(temp_repo)
    assert g["project_lessons"] == 40
    assert g["warning"] is None, "40 cheap entries are not a cost problem"


def test_few_long_lessons_do_fire(temp_repo, monkeypatch):
    """And the converse — which is exactly what a re-distill produces."""
    monkeypatch.setattr(S, "PROJECT_LESSON_TOKENS_WARN", 1000)
    _lessons(temp_repo, 12, size=1200)
    g = _gauge(temp_repo)
    assert g["project_lessons"] == 12
    assert "project lessons cost ~" in g["warning"]
    assert "tok in every handoff" in g["warning"]


def test_consolidation_that_does_not_shrink_bytes_does_not_clear_the_warning(
        temp_repo, monkeypatch):
    """H-26's acceptance case, in miniature: fewer entries, same total weight.
    Under the old count trigger this went quiet; it must not now."""
    monkeypatch.setattr(S, "PROJECT_LESSON_TOKENS_WARN", 1000)
    _lessons(temp_repo, 20, size=600)
    before = _gauge(temp_repo)
    _lessons(temp_repo, 12, size=1000)          # 20→12 entries, ~same bytes
    after = _gauge(temp_repo)

    assert after["project_lessons"] < before["project_lessons"], "entries fell"
    assert after["project_lesson_tokens"] >= before["project_lesson_tokens"] * 0.9
    assert after["warning"] is not None, (
        "the count fell but the cost did not — the nudge must still fire")


def test_the_warning_says_consolidation_may_not_help(temp_repo, monkeypatch):
    """Because following it blindly is what produced H-26."""
    monkeypatch.setattr(S, "PROJECT_LESSON_TOKENS_WARN", 100)
    _lessons(temp_repo, 5, size=400)
    assert "may NOT reduce this" in _gauge(temp_repo)["warning"]


def test_token_gauge_is_reported_even_when_quiet(temp_repo, monkeypatch):
    monkeypatch.setattr(S, "PROJECT_LESSON_TOKENS_WARN", 100000)
    _lessons(temp_repo, 5)
    g = _gauge(temp_repo)
    assert g["project_lesson_tokens"] > 0 and g["warning"] is None


# --- an open finding's age ------------------------------------------------------

def _open(fid: str, date: str) -> dict:
    return {"id": fid, "date": date, "status": "open"}


def test_age_is_silent_for_a_young_register():
    assert S._findings_by_age(
        [_open("H-01", "2026-07-20")], today="2026-07-25") is None


def test_age_is_silent_when_nothing_is_dated():
    """Evidence read, never assumed (D-065): an undated entry makes no claim."""
    assert S._findings_by_age(
        [{"id": "H-01", "status": "open"}, _open("H-02", "not-a-date")],
        today="2026-07-25") is None


def test_age_names_the_oldest_and_counts_the_stale():
    got = S._findings_by_age(
        [_open("H-16", "2026-06-23"), _open("H-21", "2026-06-25"),
         _open("H-99", "2026-07-25")], today="2026-07-25")
    assert got["oldest_id"] == "H-16"
    assert got["oldest_days"] == 32
    assert got["stale_ids"] == ["H-16", "H-21"], "newest-open excluded, oldest first"


def test_digest_line_carries_the_age_and_the_remedy(temp_repo, monkeypatch):
    bundle = {"active_gameplan": "gp", "summary": "S", "size": "standard",
              "host_profile": "python", "memory": None,
              "open_findings": ["H-16", "H-21"],
              "findings_age": {"oldest_id": "H-16", "oldest_days": 32,
                               "stale_ids": ["H-16", "H-21"]}}
    line = next(l for l in S.render_digest(bundle).splitlines()
                if l.startswith("Open findings:"))
    assert "H-16 at 32d" in line
    assert "2 open 30+ days" in line
    assert "dated acceptance" in line, "name the honest alternative to fixing"


def test_digest_line_is_unchanged_without_aging(temp_repo):
    """INVARIANT-08: a young register renders byte-identically to before."""
    bundle = {"active_gameplan": "gp", "summary": "S", "size": "standard",
              "host_profile": "python", "memory": None,
              "open_findings": ["H-99"]}
    line = next(l for l in S.render_digest(bundle).splitlines()
                if l.startswith("Open findings:"))
    assert line == "Open findings: 1 (H-99)."
