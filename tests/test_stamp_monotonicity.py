"""H-30: version stamps never ratchet backward (modernize monotonicity).

Observed live 2026-07-28: the session's MCP server was the published engine
(procedure 1.9.0) while the repo's stamp read 1.11.0 — cz_modernize(apply)
restamped the config BACKWARD to 1.9.0. A stale serving engine must refuse the
downward stamp and surface an advisory instead; only the equal-or-newer engine
stamps. Report-only on the downward arm (INVARIANT-05: advisory, no flags).
"""

from clauderizer import PROCEDURE_VERSION
from clauderizer import modernize
from clauderizer.config import Config
from clauderizer.paths import resolve


def _bump(version: str) -> str:
    parts = version.split(".")
    return ".".join([str(int(parts[0]) + 1)] + parts[1:])


def _ctx(repo):
    paths = resolve(repo)
    return paths, Config.load(paths.config_file)


def _stamp_config(paths, value: str) -> None:
    text = paths.config_file.read_text(encoding="utf-8")
    if "procedure_version" in text:
        import re
        text = re.sub(r'procedure_version = "[^"]*"',
                      f'procedure_version = "{value}"', text)
    else:
        text = text.replace("[clauderizer]",
                            f'[clauderizer]\nprocedure_version = "{value}"', 1)
    paths.config_file.write_text(text, encoding="utf-8")


def test_downward_stamp_refused_and_surfaced(temp_repo):
    """A repo stamped AHEAD of this engine: no mechanical stamp action, an
    advisory proposal names the skew, and apply() leaves the stamp untouched."""
    paths, _ = _ctx(temp_repo)
    ahead = _bump(PROCEDURE_VERSION)
    _stamp_config(paths, ahead)
    config = Config.load(paths.config_file)

    rep = modernize.report(paths, config)
    assert not any(m["action"] == "stamp_procedure_version"
                   for m in rep["mechanical"]), \
        "a stale engine must not propose stamping the repo backward"
    skew = [p for p in rep["proposals"] if "older than" in p.get("detail", "")]
    assert skew, "the downward skew must surface as an advisory proposal"
    assert ahead in skew[0]["detail"] and PROCEDURE_VERSION in skew[0]["detail"]

    modernize.apply(paths, config)
    after = Config.load(paths.config_file)
    assert after.procedure_version == ahead, \
        "apply() must never move the stamp downward"


def test_upward_stamp_still_applies(temp_repo):
    """The normal path is untouched: a repo stamped BEHIND stamps forward."""
    paths, _ = _ctx(temp_repo)
    _stamp_config(paths, "0.1.0")
    config = Config.load(paths.config_file)

    rep = modernize.report(paths, config)
    assert any(m["action"] == "stamp_procedure_version"
               for m in rep["mechanical"])
    modernize.apply(paths, config)
    after = Config.load(paths.config_file)
    assert after.procedure_version == PROCEDURE_VERSION


def test_unparseable_stamp_treated_as_legacy_forward(temp_repo):
    """Junk in the stamp is a legacy corpus, not a newer engine: stamp forward
    (never crash, never refuse)."""
    paths, _ = _ctx(temp_repo)
    _stamp_config(paths, "not-a-version")
    config = Config.load(paths.config_file)

    rep = modernize.report(paths, config)
    assert any(m["action"] == "stamp_procedure_version"
               for m in rep["mechanical"])
    modernize.apply(paths, config)
    assert Config.load(paths.config_file).procedure_version == PROCEDURE_VERSION
