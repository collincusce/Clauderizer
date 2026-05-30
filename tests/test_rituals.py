from pathlib import Path

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.profiles.detect import Profile
from clauderizer.rituals import handoff, preflight, status_bundle


def _paths_and_config(repo: Path):
    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    return paths, config


def test_status_bundle_identifies_current_phase(sample_repo):
    paths, config = _paths_and_config(sample_repo)
    bundle = status_bundle.compute(paths, config)
    assert bundle["active_gameplan"] == "2026-05-01-bootstrap"
    assert bundle["current_phase"]["number"] == "1"
    assert bundle["current_phase"]["name"] == "Wire it up"
    assert len(bundle["phases"]) == 2
    assert bundle["pending_cascades"] == []
    assert "IN PROGRESS" in bundle["summary"]


def test_status_digest_render(sample_repo):
    paths, config = _paths_and_config(sample_repo)
    bundle = status_bundle.compute(paths, config)
    digest = status_bundle.render_digest(bundle, tools=["cz_status", "cz_preflight"])
    assert digest.startswith("[Clauderizer]")
    assert "cz_status" in digest


def test_handoff_rolls_up_lessons(temp_repo):
    paths, config = _paths_and_config(temp_repo)
    result = handoff.assemble(paths, config, "2026-05-01-bootstrap", "1")
    out = Path(result["path"])
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    # All three non-obsolete lessons carried forward.
    assert result["lessons_rolled_up"] == 3
    assert "Markdown is canonical" in text
    assert "Cascade is post-hoc" in text


def test_handoff_prunes_obsolete_lessons(temp_repo):
    # Add an obsolete lesson and confirm it's dropped.
    paths, config = _paths_and_config(temp_repo)
    idx = paths.gameplan_dir("2026-05-01-bootstrap") / "CHAT-HANDOFF-INDEX.md"
    text = idx.read_text(encoding="utf-8")
    text = text.replace(
        "**3.** Keep fixtures small and hand-verifiable.",
        "**3.** Keep fixtures small and hand-verifiable.\n\n**4.** (obsolete) old advice.",
    )
    idx.write_text(text, encoding="utf-8")
    result = handoff.assemble(paths, config, "2026-05-01-bootstrap", "2")
    assert result["lessons_rolled_up"] == 3  # obsolete one pruned
    assert "old advice" not in Path(result["path"]).read_text(encoding="utf-8")


def _fake_runner(responses):
    def run(cmd, cwd):
        for key, val in responses.items():
            if key in cmd:
                return val
        return (0, "")
    return run


def test_preflight_passes_with_clean_tree_and_green_tests(sample_repo):
    paths, config = _paths_and_config(sample_repo)
    profile = Profile(
        name="python",
        commands={"test": "pytest -q"},
        baseline_test_regex=r"(\d+) passed",
    )
    runner = _fake_runner({
        "git status --porcelain": (0, ""),
        "pytest": (0, "5 passed in 0.1s"),
    })
    result = preflight.run(paths, config, profile, runner=runner)
    assert result.passed is True
    assert result.baseline_tests == "5"
    names = {c.name: c.status for c in result.checks}
    assert names["clean_tree"] == "pass"
    assert names["tests"] == "pass"


def test_preflight_fails_on_dirty_tree(sample_repo):
    paths, config = _paths_and_config(sample_repo)
    profile = Profile(name="python", commands={"test": "pytest -q"})
    runner = _fake_runner({
        "git status --porcelain": (0, " M somefile.py"),
        "pytest": (0, "5 passed"),
    })
    result = preflight.run(paths, config, profile, runner=runner)
    assert result.passed is False
    assert any(c.name == "clean_tree" and c.status == "fail" for c in result.checks)


def test_preflight_skips_when_no_test_command(sample_repo):
    paths, config = _paths_and_config(sample_repo)
    profile = Profile(name="generic", commands={})
    runner = _fake_runner({"git status --porcelain": (0, "")})
    result = preflight.run(paths, config, profile, runner=runner)
    assert any(c.name == "tests" and c.status == "skip" for c in result.checks)
