"""Skill discovery (skill-awareness Phase 1) -- read-only, propose-confirm.

Scans the well-known local skill locations for Agent Skills (a ``SKILL.md`` with
``name`` + ``description`` frontmatter), diffs them against what is already
registered in ``docs/SKILLS.md``, and PROPOSES the unregistered ones for the
agent to confirm via ``cz_register_skill``. Never writes (INVARIANT-05), never
fetches over the network (D3: no external ingestion). Degrades gracefully on
malformed frontmatter / non-UTF-8 bytes (L-24): the whole read is wrapped and a
bad file is skipped or falls back to its directory name, never crashes the scan.
"""

from __future__ import annotations

from pathlib import Path

from . import assets
from .markdown import frontmatter, sections, skill_state
from .paths import RepoPaths


def default_roots(paths: RepoPaths) -> list[tuple[str, Path]]:
    """The skill locations scanned by default, as ``(label, dir)`` pairs.

    - ``.claude/skills`` in the repo (project skills, in-repo and portable)
    - ``~/.claude/skills`` (the host user's skills)
    - Clauderizer's shipped skills (the ``clauderizer-*`` helpers)

    Named residual (O-01): plugin skill directories and non-Claude hosts
    (kimi / codex skill locations) are not yet scanned.
    """
    return [
        (".claude/skills", paths.root / ".claude" / "skills"),
        ("~/.claude/skills", Path.home() / ".claude" / "skills"),
        ("clauderizer-shipped", assets.SKILLS),
    ]


def _read_skill_md(skill_md: Path) -> dict | None:
    """Parse a ``SKILL.md`` into ``{name, description}`` or ``None``.

    Degrades gracefully: an unreadable file yields ``None``; missing/blank
    frontmatter falls back to the directory name with an empty description, so
    a real skill directory is never silently dropped.
    """
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    fm, _ = frontmatter.parse(text)
    name = fm.get("name")
    desc = fm.get("description")
    if not isinstance(name, str) or not name.strip():
        name = skill_md.parent.name  # dir-name fallback
    if not isinstance(desc, str):
        desc = ""
    name = name.strip()
    if not name:
        return None
    return {"name": name, "description": desc.strip()}


def _registered_names(paths: RepoPaths) -> set[str]:
    """The lowercased names of currently-active registered skills."""
    sdoc = paths.doc("SKILLS")
    if not sdoc.exists():
        return set()
    body = sections.get_section(sdoc.read_text(encoding="utf-8"), "Skills") or ""
    names: set[str] = set()
    for ln in body.splitlines():
        e = skill_state.parse_entry(ln)
        if e and e["state"] == skill_state.ACTIVE:
            names.add(e["name"].lower())
    return names


def discover(paths: RepoPaths,
             roots: list[tuple[str, Path]] | None = None,
             max_proposals: int = 200) -> dict:
    """Propose unregistered Agent Skills found under ``roots`` (read-only)."""
    pairs = roots if roots is not None else default_roots(paths)
    registered = _registered_names(paths)
    seen: set[str] = set()
    proposals: list[dict] = []
    scanned: list[str] = []
    present = 0
    for label, root in pairs:
        scanned.append(label)
        if not (root.exists() and root.is_dir()):
            continue
        present += 1
        for skill_md in sorted(root.glob("*/SKILL.md")):
            fm = _read_skill_md(skill_md)
            if not fm:
                continue
            key = fm["name"].lower()
            if key in seen:          # dedup across roots: first occurrence wins
                continue
            seen.add(key)
            if key in registered:    # already registered -> not a proposal
                continue
            sdir = skill_md.parent
            try:
                src = str(sdir.relative_to(paths.root))
            except ValueError:
                src = str(sdir)
            proposals.append({
                "name": fm["name"],
                "description": fm["description"],
                "source": src,
                "root": label,
            })
    capped = proposals[:max_proposals]
    return {
        "ok": True,
        "scanned_roots": scanned,
        "present_roots": present,
        "registered_count": len(registered),
        "proposal_count": len(proposals),
        "shown": len(capped),
        "proposals": capped,
        "prompt": ("Each proposal is a DRAFT, not a write. For skills genuinely "
                   "relevant to this project, confirm via cz_register_skill(name, "
                   "description, source); discard the rest. The engine proposes; "
                   "you decide (INVARIANT-05)."),
        "summary": (f"discovered {len(proposals)} unregistered skill(s) across "
                    f"{present} present root(s); {len(registered)} already registered"
                    + ("" if len(capped) == len(proposals)
                       else f"; showing {len(capped)}")),
    }
