"""Back-compatibility harness for the concurrent-multi-axis-gameplans feature.

This is the Phase-0 gate (gameplan 2026-06-27-concurrent-multi-axis-gameplans,
D-decision "back-compat is proven by a golden snapshot, not asserted"). It freezes
the EXACT single-gameplan behavior of the status digest + bundle BEFORE any focus /
portfolio / kind code lands, so every later phase proves zero drift for the
single-gameplan path: a repo with one open gameplan must render byte-identically to
today (the portfolio view expands only when >1 gameplan is open).

If a legitimate later change alters the single-gameplan surface, update the frozen
values here deliberately — never loosen the assertion to make a diff pass quietly.
"""

from __future__ import annotations

from pathlib import Path

from clauderizer import config as cfg
from clauderizer import paths as P
from clauderizer.rituals import status_bundle as S


def _paths_and_config(repo: Path):
    paths = P.resolve(repo)
    config = cfg.Config.load(paths.config_file)
    return paths, config


# The exact digest the single-gameplan fixture renders today (v1.1.1, pre-feature).
# Captured live from status_bundle.render_digest on tests/fixtures/sample_repo.
_GOLDEN_DIGEST = (
    '[Clauderizer] Gameplan 2026-05-01-bootstrap: phase 1/2 IN PROGRESS — '
    '"Wire it up". (size=standard, profile=python)\n'
    "Memory: 3 active lessons, 0 project (~350 tok handoff).\n"
    "Pending cascades: 0.\n"
    "⚠ Drift: 1 entity still 'planned' while 1 phase(s) complete (feat.login) "
    "— cz_transition_status to reconcile.\n"
    "Next: cz_preflight, then execute the phase tasks.\n"
    "Tools: cz_status, cz_preflight"
)


def test_single_gameplan_digest_is_byte_identical(sample_repo):
    """The rendered digest for a one-gameplan repo is frozen. A focus/portfolio/
    kind change that touches this string must be an intentional golden update."""
    paths, config = _paths_and_config(sample_repo)
    bundle = S.compute(paths, config)
    digest = S.render_digest(bundle, tools=["cz_status", "cz_preflight"])
    assert digest == _GOLDEN_DIGEST


def test_single_gameplan_bundle_stable_fields(sample_repo):
    """The structural bundle fields the single-gameplan path returns are frozen."""
    paths, config = _paths_and_config(sample_repo)
    b = S.compute(paths, config)
    assert b["ok"] is True
    assert b["active_gameplan"] == "2026-05-01-bootstrap"
    assert b["summary"] == (
        'Gameplan 2026-05-01-bootstrap: phase 1/2 IN PROGRESS — "Wire it up".'
    )
    assert b["next_action"] == "cz_preflight, then execute the phase tasks."
    assert b["current_phase"] == {"number": "1", "name": "Wire it up"}
    assert b["next_phase"] is None
    assert b["phases"] == [
        {"number": "0", "name": "Skeleton", "status": "complete"},
        {"number": "1", "name": "Wire it up", "status": "in_progress"},
    ]
    assert b["pending_cascades"] == []
    assert b["open_items"] == []
    assert b["blockers"] == []
    assert b["memory"]["active_lessons"] == 3
    assert b["memory"]["project_lessons"] == 0
    assert b["memory"]["handoff_est_tokens"] == 350


# --- migration round-trip stub (extended in Phase 1) --------------------------
# Phase 1 adds Config.focus with a [focus] section that read-falls-back to the
# legacy [active_gameplan] pointer. These stubs lock the legacy shape now so the
# migration can be proven (not just claimed) when focus lands.


def _write_config(repo: Path, body: str) -> Path:
    d = repo / ".clauderizer"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "config.toml"
    p.write_text(body, encoding="utf-8")
    return p


_LEGACY_ACTIVE_ONLY = """\
[clauderizer]
version = "1"
size = "standard"

[host]
profile = "python"

[paths]
docs = "docs"
gameplans = "docs/gameplans"

[active_gameplan]
id = "2026-05-01-bootstrap"
"""


def test_legacy_active_gameplan_config_loads(tmp_path):
    """A config carrying only the legacy [active_gameplan] pointer loads and
    resolves the target via BOTH the new focus field and the back-compat alias."""
    p = _write_config(tmp_path, _LEGACY_ACTIVE_ONLY)
    config = cfg.Config.load(p)
    assert config.focus == "2026-05-01-bootstrap"
    assert config.active_gameplan == "2026-05-01-bootstrap"  # alias


def test_config_rewrite_migrates_active_to_focus(tmp_path):
    """Loading a legacy [active_gameplan] config then re-emitting it migrates the
    section to [focus] while round-tripping the pointer — the migration itself."""
    p = _write_config(tmp_path, _LEGACY_ACTIVE_ONLY)
    config = cfg.Config.load(p)
    out = config.to_toml()
    assert "[focus]" in out
    assert "[active_gameplan]" not in out  # migrated away, not duplicated
    p.write_text(out, encoding="utf-8")
    reloaded = cfg.Config.load(p)
    assert reloaded.focus == "2026-05-01-bootstrap"
    assert reloaded.active_gameplan == "2026-05-01-bootstrap"


def test_focus_native_config_loads(tmp_path):
    """A config already written with [focus] loads directly."""
    body = _LEGACY_ACTIVE_ONLY.replace("[active_gameplan]", "[focus]")
    p = _write_config(tmp_path, body)
    assert cfg.Config.load(p).focus == "2026-05-01-bootstrap"


def test_focus_wins_when_both_sections_present(tmp_path):
    """A half-migrated file with both sections resolves to [focus]."""
    body = _LEGACY_ACTIVE_ONLY + '\n[focus]\nid = "2026-06-01-newer"\n'
    p = _write_config(tmp_path, body)
    assert cfg.Config.load(p).focus == "2026-06-01-newer"


def test_active_gameplan_setter_writes_focus(tmp_path):
    """config.active_gameplan = gid (used across the codebase + tests) updates focus."""
    config = cfg.Config()
    config.active_gameplan = "2026-05-01-bootstrap"
    assert config.focus == "2026-05-01-bootstrap"
