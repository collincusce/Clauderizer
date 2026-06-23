"""F5: preflight nudges re-detection when a 'generic' profile (empty test/build)
masks a now-detectable language, instead of silently skipping. Advisory only —
it reads the detector, never rewrites profile.lock."""

from clauderizer.rituals import preflight


def test_generic_hint_silent_on_a_truly_generic_dir(tmp_path):
    # nothing to detect -> no nudge (a genuinely language-less repo)
    assert preflight._generic_profile_hint(tmp_path, "test") is None


def test_generic_hint_fires_for_a_detectable_python_repo(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    hint = preflight._generic_profile_hint(tmp_path, "test")
    assert hint is not None
    assert "python" in hint                      # names the detected language
    assert "profile.lock" in hint                # points at the fix
    # and it did NOT write anything (advisory only)
    assert not (tmp_path / ".clauderizer").exists()
