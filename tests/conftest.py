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


# --- L-24 adversarial input matrix (shared; consumed by Phase 5) ---------------
#
# L-24: "a 'degrades gracefully' claim is only as strong as the input diversity
# it was tested against… guard the file DECODE before the parse and the SHAPE
# after it." The measured cost of not having this: init.py's
# `except JSONDecodeError: data = {}` then rewrites the whole file, so a
# PowerShell-authored .mcp.json (BOM by default) silently deletes every
# co-resident MCP server. One promoted lesson, written in June, would have
# killed that and the BOM'd-entity-doc drop — and it is one of the six lessons
# cz_corpus_health reports as NEVER SURFACED to any phase.
#
# Each case is (label, encoder) where encoder(text) -> bytes.
ADVERSARIAL_ENCODINGS = [
    ("utf8", lambda s: s.encode("utf-8")),
    ("utf8-bom", lambda s: s.encode("utf-8-sig")),
    ("crlf", lambda s: s.replace("\n", "\r\n").encode("utf-8")),
    ("crlf-bom", lambda s: s.replace("\n", "\r\n").encode("utf-8-sig")),
    ("unicode", lambda s: (s + "\n<!-- ✓ café — 日本語 -->\n").encode("utf-8")),
    ("trailing-ws", lambda s: (s + "   \n\n").encode("utf-8")),
]

#: Byte payloads a JSON reader must survive without destroying the file.
ADVERSARIAL_JSON = [
    ("empty", b""),
    ("whitespace", b"   \n\t\n"),
    ("valid-non-dict", b'["not", "an", "object"]'),
    ("valid-scalar", b'"just a string"'),
    ("truncated", b'{"mcpServers": {"github": {'),
    ("bom-valid", '{"mcpServers": {"github": {"command": "x"}}}'.encode("utf-8-sig")),
    ("nul-byte", b'{"mcpServers": {}}\x00'),
    ("latin1-bytes", b'{"note": "caf\xe9"}'),
]


@pytest.fixture(params=ADVERSARIAL_ENCODINGS, ids=[c[0] for c in ADVERSARIAL_ENCODINGS])
def adversarial_encoding(request):
    """(label, encoder) over the L-24 matrix — parametrize a text-file reader."""
    return request.param


@pytest.fixture(params=ADVERSARIAL_JSON, ids=[c[0] for c in ADVERSARIAL_JSON])
def adversarial_json_bytes(request):
    """(label, raw_bytes) an engine JSON reader must not destroy the file over."""
    return request.param


@pytest.fixture(autouse=True)
def _no_spawn_probe(monkeypatch):
    """Unit tests must not spawn a real MCP server.

    doctor now verifies engine IDENTITY by handshake rather than presence
    (H-20/D-060), which means the default path spawns. In-process tests would
    otherwise shell out to `uvx` — slow, network-dependent, and not what they
    measure. Mirrors init(spawn_test=False) and the _no_real_kimi_desktop guard.
    Tests that WANT the probe unset it explicitly.
    """
    monkeypatch.setenv("CLAUDERIZER_NO_SPAWN_PROBE", "1")
    monkeypatch.setenv("CLAUDERIZER_NO_NETWORK", "1")
