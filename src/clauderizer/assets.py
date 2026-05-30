"""Access to packaged template / profile / skill assets.

Assets ship inside the wheel (see pyproject force-include). At runtime we read
them straight off disk relative to this module — simple and import-light.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

_PKG = Path(__file__).parent
TEMPLATES = _PKG / "templates"
SKILLS = _PKG / "skills"


def template_text(rel: str) -> str:
    """Read a template by path relative to the templates dir."""
    return (TEMPLATES / rel).read_text(encoding="utf-8")


def render(rel: str, /, **vars: str) -> str:
    """Read a ``$placeholder`` template and substitute ``vars``.

    Uses ``safe_substitute`` so a stray ``$`` in a template never crashes a write.
    """
    return Template(template_text(rel)).safe_substitute(**vars)


def doc_template(name: str) -> str | None:
    """Template text for a named living doc (e.g. 'DECISIONS'), or None."""
    p = TEMPLATES / "docs" / f"{name}.md"
    return p.read_text(encoding="utf-8") if p.exists() else None


def procedure_text() -> str:
    return template_text("GAMEPLAN-PROCEDURE.md")


def skill_dirs() -> list[Path]:
    if not SKILLS.exists():
        return []
    return [d for d in sorted(SKILLS.iterdir()) if d.is_dir()]
