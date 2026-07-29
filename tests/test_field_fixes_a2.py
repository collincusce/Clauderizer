"""2.0.0a2 field fixes — O-05 self-explaining proposals, O-06 zero-baseline
suspicion, and the $HOME-init warning. All three were earned by the first
real 2.0.0a1 deployments (docs/gameplans/2026-07-24-workflow-critique-.../
O-05, O-06; the HOME hazard is dream-sourced)."""

from pathlib import Path

from clauderizer import modernize, proposals
from clauderizer.config import Config
from clauderizer.paths import resolve
from clauderizer.rituals import status_bundle
from clauderizer.scaffold import init as scaffold_init


def _ctx(repo):
    paths = resolve(repo)
    return paths, Config.load(paths.config_file)


# --- O-05: proposals explain themselves ---------------------------------------

def test_every_generated_proposal_kind_has_a_what_line():
    """The WHAT map covers every kind modernize can generate — a new kind
    without an explanation fails here, not in the field."""
    src = Path(modernize.__file__).read_text(encoding="utf-8")
    import re
    kinds = set(re.findall(r'"kind": "([a-z_]+)"', src))
    assert kinds, "no proposal kinds found — parser broke"
    missing = kinds - set(proposals.WHAT)
    assert not missing, f"proposal kind(s) without a WHAT line: {sorted(missing)}"
    assert all(proposals.WHAT[k].strip() for k in kinds)


def test_modernize_report_carries_triage_semantics_and_what(temp_repo):
    paths, config = _ctx(temp_repo)
    rep = modernize.report(paths, config)
    assert rep["triage"] == proposals.TRIAGE_SEMANTICS
    assert "dismiss" in rep["triage"] and "returns" in rep["triage"]
    for p in rep["proposals"]:
        assert p.get("what", "").strip(), f"unexplained proposal: {p}"


def test_dream_blocked_state_carries_triage_semantics(temp_repo, monkeypatch):
    from clauderizer import dreams
    paths, _ = _ctx(temp_repo)
    monkeypatch.setattr(dreams, "pending_proposals",
                        lambda *a, **k: [{"id": "dreamprop:abc123"}])
    out = dreams.assemble(paths)
    assert out["state"] == "blocked_on_triage"
    assert out["triage"] == proposals.TRIAGE_SEMANTICS


# --- O-06: zero baseline is anomaly-shaped ------------------------------------

def test_digest_flags_a_zero_baseline_and_stays_silent_otherwise(temp_repo):
    paths, config = _ctx(temp_repo)
    bundle = status_bundle.compute(paths, config)
    bundle["baseline_tests"] = "0"
    text = status_bundle.render_digest(bundle)
    assert "Baseline: 0 tests." in text
    assert status_bundle.ZERO_BASELINE_SUSPICION in text
    bundle["baseline_tests"] = "283"
    text = status_bundle.render_digest(bundle)
    assert "Baseline: 283 tests." in text
    assert status_bundle.ZERO_BASELINE_SUSPICION not in text


def test_preflight_warns_one_voice_on_measured_zero(temp_repo):
    """Exit 0 + zero collected -> warn (never fail), sharing the digest's
    wording (L-55 one voice)."""
    from clauderizer.profiles.detect import load_for_repo
    paths, config = _ctx(temp_repo)
    profile = load_for_repo(config.host_profile, paths.profile_lock)

    def fake_runner(cmd, cwd):
        if cmd.lstrip().startswith("git"):
            return 0, ""                 # clean tree; only the test gate is faked
        return 0, "0 passed in 0.01s"

    result = __import__("clauderizer.rituals.preflight", fromlist=["run"]).run(
        paths, config, profile, runner=fake_runner)
    tests = next(c for c in result.checks if c.name == "tests")
    if tests.status == "skip":          # profile without a test command
        return
    assert tests.status == "warn"
    assert status_bundle.ZERO_BASELINE_SUSPICION in tests.detail
    assert result.passed                 # warn never fails preflight


# --- $HOME init warning --------------------------------------------------------

def test_init_warns_when_target_is_home(tmp_path, monkeypatch, capsys):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / "pyproject.toml").write_text('[project]\nname = "x"\n',
                                              encoding="utf-8")
    (fake_home / ".git").mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    scaffold_init.init(fake_home, size="pet", spawn_test=False)
    out = capsys.readouterr().out
    assert "HOME directory" in out and "EVERY session" in out


def test_init_stays_quiet_on_a_normal_repo(empty_python_repo, capsys):
    scaffold_init.init(empty_python_repo, size="pet", spawn_test=False)
    out = capsys.readouterr().out
    assert "HOME directory" not in out
