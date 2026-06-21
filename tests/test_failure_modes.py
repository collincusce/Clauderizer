"""Phase 11 — concurrency, I/O robustness & failure modes.

Extends the adversarial-input battery (L-18/L-19/L-24) to the parse paths the
prior sweeps left uncovered — config.toml, doc frontmatter, the graph index +
its disposable cache — and adds a mixed-op concurrency stress over the write
lock (H-05/H-10). Contract: every file the engine parses degrades gracefully
(a clear error or a safe fallback, never a raw traceback), and interleaved
cz_* writes never corrupt or lose data.
"""

from __future__ import annotations

import threading

import pytest

from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.config import Config, ConfigError
from clauderizer.graph import index
from clauderizer.markdown import frontmatter, sections
from clauderizer.scaffold.init import init

GID = "2026-05-01-bootstrap"


# --- config.toml: a corrupt config must not crash the CLI (it is the diagnostic) ---

@pytest.mark.parametrize("bad", [
    b"this = = not valid toml [",            # malformed TOML
    b"size = \"\xff\xfe\"",                   # non-UTF-8 bytes
    b"[memory]\nactive_lessons_warn = \"x\"\n",  # non-int threshold (L-04: must be visible)
])
def test_config_load_raises_clean_config_error(tmp_path, bad):
    p = tmp_path / "config.toml"
    p.write_bytes(bad)
    with pytest.raises(ConfigError) as ei:
        Config.load(p)
    assert str(p) in str(ei.value)              # names the offending file
    assert isinstance(ei.value, ValueError)     # back-compat: still a ValueError


def test_empty_config_is_defaults_not_error(tmp_path):
    p = tmp_path / "config.toml"
    p.write_bytes(b"")
    cfg = Config.load(p)                          # empty file -> all defaults, no raise
    assert cfg.size == "standard" and cfg.host_target == "claude-code"


# --- forward/cross-version preservation: a rewrite never drops unmodeled data ----
# (generalizes the host_target-strip class observed in P9: an engine that does not
# model a config field must NOT silently drop it on rewrite.)

def test_config_preserves_unknown_keys_and_sections(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(
        '[clauderizer]\nversion = "1"\nsize = "standard"\nfuture_flag = "keepme"\n\n'
        '[host]\nprofile = "python"\ntarget = "cursor"\nnew_axis = "preserved"\n\n'
        '[memory]\nactive_lessons_warn = 12\nproject_lessons_warn = 20\n\n'
        '[experimental]\nbeta = true\nratio = 3\nitems = ["a", "b"]\n',
        encoding="utf-8")
    cfg = Config.load(p)
    assert cfg.host_target == "cursor"               # modeled fields still load
    p.write_text(cfg.to_toml(), encoding="utf-8")    # rewrite through to_toml
    again = Config.load(p)
    text = p.read_text(encoding="utf-8")
    assert again.host_target == "cursor"
    assert 'future_flag = "keepme"' in text          # unknown key in a known section
    assert 'new_axis = "preserved"' in text          # unknown key under [host]
    assert "[experimental]" in text                  # unknown WHOLE section
    assert "beta = true" in text and "ratio = 3" in text and 'items = ["a", "b"]' in text
    assert again.extra["experimental"]["ratio"] == 3  # int preserved as int, not "3"


def test_config_to_toml_unchanged_without_extras(empty_python_repo):
    # the preservation change must NOT alter a normal config's bytes (idempotency)
    init(empty_python_repo, spawn_test=False)
    p = empty_python_repo / ".clauderizer" / "config.toml"
    cfg = Config.load(p)
    assert cfg.extra == {}
    assert cfg.to_toml() == p.read_text(encoding="utf-8")   # round-trips byte-identical


def test_config_merge_missing_preserves_extra(tmp_path):
    from clauderizer.config import merge_missing
    p = tmp_path / "config.toml"
    p.write_text('[clauderizer]\nversion = "1"\nsize = "standard"\n\n'
                 '[host]\ntarget = "zed"\n\n[future]\nx = 1\n', encoding="utf-8")
    merged = merge_missing(Config.load(p), Config.for_size("standard"))
    assert "future" in merged.extra and "x = 1" in merged.to_toml()  # re-run keeps it


def test_frontmatter_write_preserves_unmodeled_fields(tmp_path):
    # the markdown writer round-trips arbitrary frontmatter (generic dict, not a
    # typed model) — confirm an unmodeled entity field survives a structured write
    from clauderizer.markdown import writer
    p = tmp_path / "e.md"
    p.write_text("---\nid: subsys.x\ntype: subsystem\ncustom_field: keep\n---\nbody\n",
                 encoding="utf-8")
    writer.set_frontmatter_fields(p, {"status": "active"})
    text = p.read_text(encoding="utf-8")
    assert "custom_field: keep" in text and "status: active" in text


@pytest.mark.parametrize("cmd", [["doctor"], ["status"], ["reindex"]])
def test_cli_degrades_on_corrupt_config(empty_python_repo, monkeypatch, capsys, cmd):
    from clauderizer import cli
    init(empty_python_repo, spawn_test=False)
    (empty_python_repo / ".clauderizer" / "config.toml").write_text(
        "this = = not valid toml [\n", encoding="utf-8")
    monkeypatch.chdir(empty_python_repo)
    code = cli.main(cmd)                          # must NOT raise a TOMLDecodeError
    out = capsys.readouterr().out
    assert code == 1
    assert "config.toml is malformed" in out
    assert "clauderize init" in out               # actionable


# --- frontmatter: malformed docs degrade to a partial/empty parse, never crash ----

@pytest.mark.parametrize("text", [
    "---\nid: x\ntype: subsystem\n# no close\nbody",   # unclosed fence
    "---\nid: [unclosed\n---\nbody",                    # broken YAML-ish value
    "---\nid: x\n\tweird: 1\n---\nb",                   # tab indent
    "",                                                  # empty
    "---\n---\n",                                        # empty fence
])
def test_frontmatter_parse_never_crashes(text):
    data, body = frontmatter.parse(text)             # no raise
    assert isinstance(data, dict) and isinstance(body, str)


# --- graph index: a malformed / non-utf8 doc must not abort the whole build -------

def test_index_build_tolerates_malformed_and_nonutf8_docs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "good.md").write_text(
        "---\nid: subsys.good\ntype: subsystem\nstatus: active\n---\nok", encoding="utf-8")
    (docs / "bad.md").write_text(
        "---\nid: [broken\ntype: subsystem\n---\nbody", encoding="utf-8")
    (docs / "nonutf8.md").write_bytes(b"---\nid: subsys.x\ntype: subsystem\n---\n\xff\xfe raw")
    graph = index.build(docs)                         # must not raise
    assert "subsys.good" in graph.entities            # the healthy doc still indexes


def test_index_load_or_rebuild_tolerates_corrupt_cache(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "good.md").write_text(
        "---\nid: subsys.good\ntype: subsystem\nstatus: active\n---\nok", encoding="utf-8")
    cache = tmp_path / "idx.json"
    for corrupt in (b"{not valid json", b"\xff\xfe non-utf8 cache", b""):
        cache.write_bytes(corrupt)
        graph = index.load_or_rebuild(docs, cache)    # falls back to a fresh rebuild
        assert "subsys.good" in graph.entities


# --- concurrency: interleaved DIFFERENT cz_* ops lose nothing (H-05) --------------

def test_mixed_ops_concurrent_lose_nothing(temp_repo):
    """Different ops (add_lesson -> CHAT-HANDOFF-INDEX, add_decision -> DECISIONS)
    racing through the write lock: every entry lands, ids stay distinct per
    counter, no torn write."""
    paths = P.resolve(temp_repo)
    n = 6
    start = threading.Barrier(2 * n)
    errors: list[Exception] = []
    lesson_ids: list[int] = []
    decision_ids: list[str] = []
    lock = threading.Lock()

    def add_lesson(i):
        start.wait()
        try:
            r = M.add_lesson(paths, gameplan_id=GID, text=f"mixed lesson {i}", category="Process")
            with lock:
                lesson_ids.append(r["number"])
        except Exception as e:  # noqa: BLE001 - collected and re-raised in the assert
            with lock:
                errors.append(e)

    def add_decision(i):
        start.wait()
        try:
            r = M.add_decision(paths, title=f"Mixed decision {i}", context="c",
                               decision="d", consequences="e")
            with lock:
                decision_ids.append(r["id"])
        except Exception as e:  # noqa: BLE001
            with lock:
                errors.append(e)

    threads = ([threading.Thread(target=add_lesson, args=(i,)) for i in range(n)]
               + [threading.Thread(target=add_decision, args=(i,)) for i in range(n)])
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"concurrent ops raised: {errors}"
    # every write landed, ids are distinct (no duplicate allocation under the lock)
    assert len(lesson_ids) == n and len(set(lesson_ids)) == n
    assert len(decision_ids) == n and len(set(decision_ids)) == n
    # and both target files actually contain all the entries (no lost update)
    idx = (temp_repo / "docs" / "gameplans" / GID / "CHAT-HANDOFF-INDEX.md").read_text(encoding="utf-8")
    for i in range(n):
        assert f"mixed lesson {i}" in idx
    dec = (temp_repo / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    for i in range(n):
        assert f"Mixed decision {i}" in dec
    # the lessons section has no duplicated numbers (torn append guard)
    body = sections.get_section(idx, "Accumulated Lessons") or ""
    import re
    nums = [int(m.group(1)) for m in re.finditer(r"^\s*\*\*(\d+)\.\*\*", body, re.M)]
    assert len(nums) == len(set(nums))
