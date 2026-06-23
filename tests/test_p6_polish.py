"""P6 front-door + rendering polish: the `clauderizer` console alias (F1), the
placeholder-replacement on first append (F12.1), and amendment rendering (F12.2/3)."""

import pathlib
import tomllib

from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.markdown import sections, writer

_PYPROJECT = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_clauderizer_console_alias_declared():
    # F1: `uvx clauderizer <cmd>` works because the package ships a `clauderizer`
    # script alongside the canonical `clauderize`.
    scripts = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["scripts"]
    assert scripts.get("clauderizer") == "clauderizer.cli:main"
    assert scripts.get("clauderize") == "clauderizer.cli:main"  # canonical still present


def test_first_append_replaces_scaffold_placeholder():
    # F12.1: a section that holds only a `_(…)_` placeholder is replaced by the
    # first real entry, not stacked beneath it. (Second entry then appends.)
    doc = "## Decisions\n\n_(Add entries with cz_add_decision.)_\n"
    one = sections.append_to_section(doc, "Decisions", "### D-001 — first\n\nbody")
    assert "Add entries with cz_add_decision" not in one
    assert "D-001 — first" in one
    two = sections.append_to_section(one, "Decisions", "### D-002 — second\n\nbody")
    assert "D-001 — first" in two and "D-002 — second" in two


def test_amendment_renders_lists_readably_and_no_false_pending(temp_repo):
    # F12.2: list args render as a readable inline list, not a Python literal.
    # F12.3: the cascade line is a conditional prompt, not a perpetual "pending".
    paths = P.resolve(temp_repo)
    gid = M.create_gameplan(paths, "Amend Test", today="2026-06-23")["gameplan_id"]
    M.add_amendment(
        paths, gameplan_id=gid, title="scope shift",
        affected_sections=["Phase Breakdown", "Subsystems Touched"],
        affected_phases=["0", "1"], triggered_by="user", what="added a task",
        why="new requirement", amendments_ritual=True,
    )
    gp = writer.full_text(paths.gameplan_dir(gid) / "GAMEPLAN.md")
    assert "Phase Breakdown, Subsystems Touched" in gp
    assert "['Phase Breakdown'" not in gp        # not a python list literal
    assert "_pending — run" not in gp            # no false "pending" TODO
