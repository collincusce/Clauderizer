"""Phase 0 (kimi-desktop-wiring-end-to-end-repair, D-055): repo discovery is
decoupled from the process cwd.

``clauderizer-mcp --repo <path>`` / ``$CLAUDERIZER_REPO`` names the repo to serve,
so a host that cannot spawn with the repo as its working directory (a Windows
desktop serving a ``\\\\wsl.localhost`` UNC repo, D-054/D-055) can still point the
stateless server at the right repo. Precedence: ``--repo`` > ``$CLAUDERIZER_REPO``
> cwd discovery.
"""

import os

import pytest

from clauderizer import ops
from clauderizer.mcp_server import _parse_repo


def test_parse_repo_forms():
    assert _parse_repo([]) is None
    assert _parse_repo(["--version"]) is None
    assert _parse_repo(["--repo", "/x"]) == "/x"
    assert _parse_repo(["--repo=/y"]) == "/y"
    # last wins, mixed forms
    assert _parse_repo(["--repo", "/a", "--repo=/b"]) == "/b"
    # a trailing bare --repo with no value is ignored, not an index error
    assert _parse_repo(["--repo"]) is None


def test_repo_ctx_honors_env_over_cwd(monkeypatch, temp_repo, tmp_path):
    """Env names the repo even when cwd is NOT a clauderized repo — proving the
    resolution is decoupled from the process cwd, not merely additive to it."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("CLAUDERIZER_REPO", str(temp_repo))
    paths, _cfg = ops.repo_ctx()
    assert paths.root == temp_repo.resolve()


def test_repo_ctx_env_accepts_a_subdir(monkeypatch, temp_repo, tmp_path):
    """The value may be any path inside the repo — find_repo_root walks up."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLAUDERIZER_REPO", str(temp_repo / "docs"))
    paths, _cfg = ops.repo_ctx()
    assert paths.root == temp_repo.resolve()


def test_repo_ctx_bad_override_raises_clear(monkeypatch, tmp_path):
    bad = tmp_path / "nope"
    bad.mkdir()
    monkeypatch.setenv("CLAUDERIZER_REPO", str(bad))
    with pytest.raises(RuntimeError) as excinfo:
        ops.repo_ctx()
    msg = str(excinfo.value)
    assert "CLAUDERIZER_REPO" in msg
    assert "clauderize init" in msg


def test_cli_repo_flag_wins_over_preexisting_env(monkeypatch, temp_repo):
    """main() exports --repo into $CLAUDERIZER_REPO before building the server,
    overwriting any inherited value — CLI beats env."""
    pytest.importorskip("mcp")
    import clauderizer.mcp_server as ms

    monkeypatch.setenv("CLAUDERIZER_REPO", "/preexisting/should/be/overwritten")
    seen: dict[str, str | None] = {}

    class _Stub:
        def run(self):  # what build_server().run() would be
            seen["repo"] = os.environ.get("CLAUDERIZER_REPO")

    monkeypatch.setattr(ms, "build_server", lambda: _Stub())
    rc = ms.main(["--repo", str(temp_repo)])
    assert rc == 0
    assert seen["repo"] == str(temp_repo)


def test_no_flag_leaves_env_untouched(monkeypatch, temp_repo):
    """Without --repo, main() does not clobber an inherited $CLAUDERIZER_REPO."""
    pytest.importorskip("mcp")
    import clauderizer.mcp_server as ms

    monkeypatch.setenv("CLAUDERIZER_REPO", str(temp_repo))
    seen: dict[str, str | None] = {}

    class _Stub:
        def run(self):
            seen["repo"] = os.environ.get("CLAUDERIZER_REPO")

    monkeypatch.setattr(ms, "build_server", lambda: _Stub())
    rc = ms.main([])
    assert rc == 0
    assert seen["repo"] == str(temp_repo)


def test_version_and_help_fastpath_still_exit_0(capsys, monkeypatch):
    """The deterministic probe path (D3) survives --repo: --version/--help exit 0
    without touching the SDK or stdin, and --help now documents --repo."""
    monkeypatch.delenv("CLAUDERIZER_REPO", raising=False)
    import clauderizer.mcp_server as ms

    assert ms.main(["--version"]) == 0
    assert "clauderizer" in capsys.readouterr().out
    assert ms.main(["--help"]) == 0
    help_out = capsys.readouterr().out
    assert "--repo" in help_out
