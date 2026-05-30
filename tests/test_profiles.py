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
