"""Phase 5: foreign config survives, and the fix reaches existing installs."""
from __future__ import annotations
import json
import pytest
from clauderizer import hosttargets, modernize
from clauderizer import config as cfg, paths as P
from clauderizer.scaffold.init import init


def test_foreign_mcp_servers_survive_every_encoding(empty_python_repo, adversarial_encoding):
    # The shared matrix also carries a markdown-comment case, which is not valid
    # JSON by construction — skip it here rather than weaken the JSON contract.
    """D-046 promised non-destructive merges; L-54 said BUILD the guard. Neither
    happened, and a BOM was enough to delete every co-resident MCP server."""
    label, encode = adversarial_encoding
    if label == "unicode":
        pytest.skip("appends an HTML comment — a markdown case, not a JSON one")
    doc = json.dumps({"mcpServers": {"github": {"command": "gh-mcp"},
                                     "postgres": {"command": "pg-mcp"}},
                      "unrelatedTopLevel": "keep me"}, indent=2)
    (empty_python_repo / ".mcp.json").write_bytes(encode(doc))
    init(empty_python_repo, spawn_test=False)
    after = json.loads((empty_python_repo / ".mcp.json").read_text(encoding="utf-8-sig"))
    assert set(after["mcpServers"]) >= {"github", "postgres", "clauderizer"}, label
    assert after.get("unrelatedTopLevel") == "keep me", label


def test_an_unparseable_config_is_refused_not_rewritten(empty_python_repo,
                                                        adversarial_json_bytes):
    """The file belongs to someone else — and for a bespoke host it lives outside
    the repo, where git checkout cannot restore it (L-29)."""
    label, raw = adversarial_json_bytes
    path = empty_python_repo / hosttargets.HOST_EMITTERS["cursor"].config_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    before = path.read_bytes()
    data, refusal = hosttargets.read_foreign_json(path)
    if refusal:
        with pytest.raises(ValueError, match="refusing to rewrite"):
            hosttargets.emit_mcp("cursor", empty_python_repo)
        assert path.read_bytes() == before, f"{label}: refused but still rewrote"
    else:
        assert isinstance(data, dict), label


def test_upgrade_converges_a_pre_1_14_install(empty_python_repo):
    """D-042 tier-1. Without this the policy fix reaches ZERO existing installs —
    and every install in the world already ran init."""
    init(empty_python_repo, spawn_test=False)
    gi = empty_python_repo / ".gitignore"
    new = (".clauderizer/proposals.dream.jsonl", ".clauderizer/dreams.watermark.json",
           ".clauderizer/revision.json", ".clauderizer/hook.sh",
           ".clauderizer/hook.cmd", ".clauderizer/write.lock")
    gi.write_text("\n".join(l for l in gi.read_text(encoding="utf-8").splitlines()
                            if l not in new) + "\n", encoding="utf-8")
    paths = P.resolve(empty_python_repo)
    config = cfg.Config.load(paths.config_file)
    out = modernize.apply(paths, config)
    assert "ensure_gitignore_current" in out["applied"]
    have = set(gi.read_text(encoding="utf-8").splitlines())
    assert set(new) <= have, sorted(set(new) - have)
    # Idempotent: a second run reports nothing to do.
    assert "ensure_gitignore_current" not in modernize.apply(paths, config)["applied"]


def test_upgrade_never_touches_docs(empty_python_repo):
    """D-042: no markdown memory file is ever auto-mutated."""
    import hashlib
    init(empty_python_repo, spawn_test=False)
    paths = P.resolve(empty_python_repo)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths.docs.rglob("*.md")}
    modernize.apply(paths, cfg.Config.load(paths.config_file))
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in paths.docs.rglob("*.md")}
    assert before == after


def test_the_ignore_set_is_single_sourced():
    """init, upgrade and the doctor nudge must not drift (L-55)."""
    import inspect
    from clauderizer.scaffold import init as init_mod
    src = inspect.getsource(init_mod)
    for line in modernize.LOCAL_STATE_IGNORES:
        assert line in src, f"{line} is in LOCAL_STATE_IGNORES but init never writes it"


def test_transcript_mining_refuses_an_unrelated_project(empty_python_repo, monkeypatch):
    """A probe once returned ok:true with 47 proposals from ANOTHER project."""
    from clauderizer import ops
    home = empty_python_repo / "fakehome"
    (home / ".claude" / "projects" / "some-other-project-py_app").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    monkeypatch.chdir(empty_python_repo)
    monkeypatch.delenv("CLAUDERIZER_TRANSCRIPTS_DIR", raising=False)
    assert ops._default_transcripts_dir() == "", (
        "a directory merely ENDING with this repo's folder name was mined")
