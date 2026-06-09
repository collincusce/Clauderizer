from clauderizer.profiles import detect


def test_load_all_profiles_present():
    profiles = detect.load_all()
    assert {"node", "python", "go", "ruby", "generic"} <= set(profiles)
    assert profiles["python"].command("test") == "pytest -q"
    assert profiles["go"].command("test") == "go test ./..."


def test_detect_node(empty_node_repo):
    prof, _alts = detect.detect(empty_node_repo)
    assert prof.name == "node"


def test_detect_python(empty_python_repo):
    prof, _alts = detect.detect(empty_python_repo)
    assert prof.name == "python"


def test_detect_falls_back_to_generic(tmp_path):
    (tmp_path / ".git").mkdir()
    prof, alts = detect.detect(tmp_path)
    assert prof.name == "generic"
    assert alts == []


def test_lock_toml_roundtrip():
    prof = detect.load("ruby")
    lock = prof.to_lock_toml()
    assert 'profile = "ruby"' in lock
    assert "bundle exec rspec" in lock


def test_lock_toml_is_valid_toml_for_every_profile(tmp_path):
    """Regression: regex backslashes in lock values were emitted unescaped,
    making the whole lock unparseable — and silently ignored on load."""
    import tomllib

    for name, prof in detect.load_all().items():
        lock_text = prof.to_lock_toml()
        parsed = tomllib.loads(lock_text)  # must not raise
        assert parsed["preflight"]["baseline_test_regex"] == prof.baseline_test_regex
        # and the full write -> load_for_repo round trip preserves the profile
        lock_path = tmp_path / f"{name}.lock.toml"
        lock_path.write_text(lock_text, encoding="utf-8")
        loaded = detect.load_for_repo(name, lock_path)
        assert loaded.baseline_test_regex == prof.baseline_test_regex
        assert loaded.command("test") == prof.command("test")


def test_load_for_repo_applies_regex_override(tmp_path):
    lock = tmp_path / "profile.lock.toml"
    lock.write_text(
        'profile = "python"\n[commands]\ntest = "pytest"\n'
        '[preflight]\nbaseline_test_regex = "(\\\\d+) tests ok"\n',
        encoding="utf-8",
    )
    prof = detect.load_for_repo("python", lock)
    assert prof.command("test") == "pytest"
    assert prof.baseline_test_regex == r"(\d+) tests ok"
