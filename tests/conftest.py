import shutil
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture
def sample_repo() -> Path:
    """Read-only path to the canonical fixture tree. Do not mutate."""
    return FIXTURE


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """A throwaway copy of the fixture tree, safe to mutate in a test.

    Stamped with the engine's CURRENT procedure version (exactly what
    init/upgrade would do), so a temp repo models an up-to-date corpus and
    modernization staleness never leaks into unrelated digest assertions;
    staleness tests remove the stamp themselves."""
    dest = tmp_path / "repo"
    shutil.copytree(FIXTURE, dest)
    from clauderizer import PROCEDURE_VERSION

    cfgf = dest / ".clauderizer" / "config.toml"
    if cfgf.exists():
        text = cfgf.read_text(encoding="utf-8")
        if "procedure_version" not in text:
            text = text.replace(
                "[clauderizer]",
                f'[clauderizer]\nprocedure_version = "{PROCEDURE_VERSION}"', 1)
            cfgf.write_text(text, encoding="utf-8")
    return dest


@pytest.fixture
def empty_node_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "node_app"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "package.json").write_text('{"name":"x","version":"1.0.0"}\n', encoding="utf-8")
    return repo


@pytest.fixture
def empty_python_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "py_app"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    return repo


@pytest.fixture(autouse=True)
def _no_real_kimi_desktop(monkeypatch):
    """Never touch a real per-user daimon (Kimi desktop) config during tests (L-29).
    init() calls kimidesktop.wire() with the real environment; this env guard makes
    detect_config() return None there. Tests that exercise the desktop host pass
    their own environ (unaffected) or monkeypatch detect_config directly."""
    from clauderizer import kimidesktop
    monkeypatch.setenv(kimidesktop.DISABLE_ENV, "1")
