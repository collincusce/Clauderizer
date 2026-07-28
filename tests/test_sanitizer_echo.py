"""H-29: write-guard removals echo to the writer at write time.

The sanitizer strips leaked tool-call framing and unbalanced closing tags from
prose before persist (L-63 class rejection, code spans exempt). Silently: the
writer discovered 'carrying , , and three fragments' only by rereading the
stored entry. The fix echoes what was removed in the WRITE RESULT — an
advisory naming the stripped fragments with the code-span nudge — attached at
the REGISTRY seam so every cz_* transport carries it (INVARIANT-05: advisory,
never a block; the write still succeeds with the sanitized body).
"""

from clauderizer import ops


def _run(temp_repo, monkeypatch, name, **kwargs):
    monkeypatch.setenv("CLAUDERIZER_REPO", str(temp_repo))
    return ops.run_op(name, **kwargs)


def test_stripped_fragments_echo_in_write_result(temp_repo, monkeypatch):
    r = _run(temp_repo, monkeypatch, "cz_add_lesson",
             text="Guard rendering: carrying </function_results> and </output> "
                  "markers plus a stray </thing> closer in prose.",
             gameplan_id="2026-05-01-bootstrap")
    assert r["ok"]
    adv = r.get("sanitizer_advisory", "")
    assert adv, "removals must echo in the write result (H-29)"
    assert "</thing>" in adv or "thing" in adv
    assert "code span" in adv or "`" in adv          # the rewrite nudge


def test_code_spanned_markup_is_kept_and_silent(temp_repo, monkeypatch):
    r = _run(temp_repo, monkeypatch, "cz_add_lesson",
             text="Documenting the guard: quote literal markup like "
                  "`</function_results>` in code spans and it survives.",
             gameplan_id="2026-05-01-bootstrap")
    assert r["ok"]
    assert "sanitizer_advisory" not in r


def test_clean_write_carries_no_advisory_and_no_stale_leak(temp_repo, monkeypatch):
    dirty = _run(temp_repo, monkeypatch, "cz_add_lesson",
                 text="A </leak> that the guard strips.",
                 gameplan_id="2026-05-01-bootstrap")
    assert dirty.get("sanitizer_advisory")
    clean = _run(temp_repo, monkeypatch, "cz_add_lesson",
                 text="A perfectly ordinary lesson about nothing markup-shaped.",
                 gameplan_id="2026-05-01-bootstrap")
    assert clean["ok"]
    assert "sanitizer_advisory" not in clean, \
        "the accumulator must reset per op — no cross-op leakage"


def test_advisory_never_blocks_the_write(temp_repo, monkeypatch):
    r = _run(temp_repo, monkeypatch, "cz_add_decision",
             title="Ship the </widget> parser",
             context="The </widget> closer appears unquoted.",
             decision="Parse it.", consequences="None.")
    assert r["ok"] and r.get("id")                   # write landed (INVARIANT-05)
    assert r.get("sanitizer_advisory")
