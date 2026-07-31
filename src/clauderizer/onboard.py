"""Onboarding an existing project (D-044): the engine detects, the agent seeds.

`clauderize init` on a repo that already has real documentation scaffolds
placeholder VISION/ARCHITECTURE next to it and, before this module, nothing
prompted seeding them. The engine is deterministic and never synthesizes prose —
distilling specs into memory is judgment work — so onboarding is the established
assemble-and-prompt shape (D-016/D-019): this module finds the repo's SPEC
CANDIDATES (paths and sizes only, never contents) and the Clauderizer docs that
are still UNSEEDED scaffolds; ``cz_onboard`` returns both plus a seeding prompt;
the packaged ``clauderizer-onboard`` skill walks the agent through reading the
sources and recording what they hold via the normal blessed writes. Advisory
everywhere — nothing here ever writes a doc.
"""

from __future__ import annotations

from pathlib import Path

from . import assets
from .markdown import sections
from .paths import RepoPaths

# Bounded surfacing: a candidate list is a menu, not an inventory.
CANDIDATE_CAP = 25
MAX_CANDIDATE_BYTES = 2 * 1024 * 1024

# Root-level markdown that usually holds project knowledge.
_ROOT_CANDIDATES = (
    "README.md", "ARCHITECTURE.md", "DESIGN.md", "DESIGN-DOC.md",
    "SPEC.md", "SPECIFICATION.md", "CONTRIBUTING.md", "NOTES.md",
)

# docs/ subdirectories the engine owns (tracked entities + gameplans + plans).
_OWNED_DIRS = frozenset({
    "gameplans", "features", "subsystems", "datasources",
    "capabilities", "entities", "plans",
})

# The prose docs onboarding can seed. The append-only logs (DECISIONS,
# INVARIANTS, LESSONS, HARDENING, INCIDENTS) are excluded on purpose — they are
# seeded through their blessed writes, entry by entry, with provenance.
_PROSE_DOCS = (
    "VISION", "ARCHITECTURE", "REQUIREMENTS", "ENGINEERING-PRINCIPLES",
    "DEPLOYMENT", "DATASOURCES", "SCHEMA", "SECURITY", "TESTING", "GLOSSARY",
)


def _owned_doc_names() -> set[str]:
    """The scaffold template set IS the owned list — single-sourced from the
    packaged assets, plus the procedure doc the engine also owns."""
    owned = {p.name for p in (assets.TEMPLATES / "docs").glob("*.md")}
    owned.add("GAMEPLAN-PROCEDURE.md")
    return owned


def spec_candidates(paths: RepoPaths) -> list[dict]:
    """Existing docs that likely hold project knowledge.

    Well-known root files, plus every ``*.md`` under the project's docs tree that
    is not an untouched Clauderizer scaffold. Paths and sizes only (the agent
    reads contents itself); empty and oversized files skipped; capped at
    :data:`CANDIDATE_CAP`.

    H-34: this used to exclude any file whose NAME matched a shipped template,
    which silently hid the ten most valuable documents in a mature repo —
    ARCHITECTURE, VISION, REQUIREMENTS, SECURITY and their siblings are declared
    PROJECT-owned (``ownership.PROJECT_DOCS``) and are exactly what onboarding
    exists to surface. A name cannot distinguish an untouched scaffold from 800
    lines the project wrote; ``_is_unseeded`` can, and already did for
    ``unseeded_docs``. Ownership is now judged from the CONTENT.
    """
    root = paths.root
    out: list[dict] = []
    seen: set[Path] = set()

    def add(p: Path) -> None:
        if len(out) >= CANDIDATE_CAP or p in seen:
            return
        try:
            size = p.stat().st_size
        except OSError:
            return
        if size == 0 or size > MAX_CANDIDATE_BYTES:
            return
        seen.add(p)
        out.append({"path": p.relative_to(root).as_posix(), "bytes": size})

    for name in _ROOT_CANDIDATES:
        p = root / name
        if p.is_file():
            add(p)

    # Scan the engine's docs root AND the conventional docs/ directory. When
    # [paths] docs is pointed elsewhere so the engine's corpus cannot collide
    # with the project's (the attago case), the project's own documentation
    # lives outside the engine root and would otherwise be invisible.
    roots = [paths.docs]
    conventional = root / "docs"
    if conventional.is_dir() and conventional != paths.docs:
        roots.append(conventional)

    for docs in roots:
        if not docs.exists():
            continue
        for p in sorted(docs.rglob("*.md")):
            try:
                rel = p.relative_to(docs)
            except ValueError:  # pragma: no cover - defensive
                continue
            if rel.parts and rel.parts[0] in _OWNED_DIRS:
                continue
            if _is_engine_scaffold(p):
                continue
            add(p)
    return out


def _is_engine_scaffold(p: Path) -> bool:
    """True only for a file that IS the engine's untouched scaffold.

    A name match alone is not enough (H-34): the project may own a document at
    that name and fill it with real content. Compared against the shipped
    template by the same structural test ``unseeded_docs`` uses, so a seeded doc
    reads as the project's however much the template's wording later evolves.
    """
    template = assets.doc_template(p.stem)
    if template is None:
        return False
    try:
        return _is_unseeded(p.read_text(encoding="utf-8"), template)
    except OSError:
        return False


def _meaningful_lines(text: str) -> set[str]:
    """The lines that would indicate real authored content: not blank, not a
    heading, not a scaffold placeholder."""
    out: set[str] = set()
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        if sections.is_placeholder(ln):
            continue
        out.add(ln)
    return out


def _is_unseeded(text: str, template_text: str | None) -> bool:
    """A doc is unseeded when it carries no authored content: every meaningful
    line it has also appears in its shipped template (boilerplate), or it has
    none at all. Structure-based on purpose — byte-identity would false-read a
    doc as seeded the moment the template's wording evolved."""
    mine = _meaningful_lines(text)
    if not mine:
        return True
    tmpl = _meaningful_lines(template_text or "")
    return mine <= tmpl


def unseeded_docs(paths: RepoPaths) -> list[str]:
    """The prose docs on disk that are still scaffold placeholders."""
    out: list[str] = []
    for name in _PROSE_DOCS:
        p = paths.doc(name)
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if _is_unseeded(text, assets.doc_template(name)):
            out.append(f"{paths.docs.name}/{name}.md")
    return out


_PROMPT = (
    "Seed this project's memory from its existing documentation. Read each "
    "candidate file (the list carries paths, not contents), then record what "
    "it holds through the normal writes: rewrite the unseeded docs' prose "
    "directly (VISION/ARCHITECTURE and their siblings are living documents, "
    "not append-only logs); record the real subsystems and features with "
    "cz_upsert_entity; record decisions the project already made with "
    "cz_add_decision and standing rules with cz_add_invariant, citing the "
    "source file as evidence. Re-run cz_onboard when done — seeded docs drop "
    "out of the list. The engine never seeds anything for you."
)


def report(paths: RepoPaths) -> dict:
    """The read-only onboarding bundle (cz_onboard's whole result)."""
    unseeded = unseeded_docs(paths)
    candidates = spec_candidates(paths)
    present = [n for n in _PROSE_DOCS if paths.doc(n).exists()]
    return {
        "ok": True,
        "unseeded": unseeded,
        "candidates": candidates,
        "seeded_count": len(present) - len(unseeded),
        "prompt": _PROMPT,
        "summary": (f"{len(unseeded)} unseeded doc(s), {len(candidates)} spec "
                    f"candidate(s), {len(present) - len(unseeded)} doc(s) already seeded"),
    }
