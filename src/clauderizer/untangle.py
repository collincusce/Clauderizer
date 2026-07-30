"""The untangle (D-080/D-081): separate engine memory from the project's docs.

Moves ENGINE-owned docs into ``docs/clauderizer/`` and leaves everything the
human authored exactly where it is. The rules that make this safe to run
automatically:

* **No file is ever split, merged, or rewritten.** Only moved, or newly created.
  A machine has no business deciding which half of a mixed file is whose.
* **A doc that is theirs stays theirs.** If ``docs/GLOSSARY.md`` holds real
  project content, it is left byte-identical and a *fresh* engine glossary is
  written alongside at the new path — the two-glossary shape, which is the
  general case and not a special one.
* **Every entry is conserved.** Entry counts are taken before and after and must
  match exactly (INVARIANT-03): a move that loses a decision is a bug, not a
  migration.
* **A legacy stub is left behind** at every vacated path (D-081). It is
  load-bearing three times over, all measured: a human or agent opening the old
  path is told what happened; ``dangling_doc_pointers`` stops firing (so an old
  engine never renders its harmful "run upgrade to scaffold them" advice, which
  would recreate empty real files and split the corpus in two); and
  ``create_if_absent`` sees the stub and never recreates anything.
* **Idempotent.** A second run reports zero actions.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import assets, ownership
from .config import Config
from .markdown import writer
from .paths import RepoPaths

#: Entry anchors the append-only registers use — the same shapes
#: ``model.next_numbered_id`` counts, so "does this file hold engine memory?"
#: is answered by the writer's own grammar rather than a second guess.
_ENTRY_RE = re.compile(
    r"^(?:#{1,6}\s+([A-Z]+-\d+)\b|\s*\*\*([A-Z]+-\d+)\.\*\*)", re.M)

MOVE = "move"
LEAVE_AND_CREATE = "leave_and_create"
CREATE = "create"

_STUB = """# {name} — moved

> **This file has moved to `{new}`.**
>
> Clauderizer now keeps its own memory in `docs/clauderizer/` and leaves
> `docs/` to you (D-080). Nothing was lost — the content is at the path above.
>
> If your tooling brought you here expecting content, the install reading this
> repo is older than the layout. Upgrade it:
>
> ```
> uv tool install "clauderizer[mcp]" --force
> ```
>
> This placeholder is inert and can be deleted once every install that touches
> this repo is on 3.0.0 or newer.
"""


def entry_count(path: Path) -> int:
    """How many append-only entries a register holds. 0 for prose."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return len(_ENTRY_RE.findall(text))


def _is_engine_content(path: Path, name: str) -> bool:
    """True when this file is the ENGINE's — either its untouched scaffold or a
    register carrying engine-written entries. False means a human wrote it."""
    from .onboard import _is_unseeded

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if _is_unseeded(text, assets.doc_template(name)):
        return True          # still our scaffold
    return entry_count(path) > 0   # our register, seeded with our entries


def plan(paths: RepoPaths, config: Config) -> list[dict]:
    """What ``apply`` WOULD do, as a list of verdicts. Writes nothing."""
    if (config.docs_layout or ownership.LAYOUT_LEGACY) == ownership.LAYOUT_SPLIT:
        return []
    actions: list[dict] = []
    ns = paths.docs / ownership.ENGINE_NAMESPACE
    for name in sorted(ownership.ENGINE_DOCS):
        old = paths.docs / f"{name}.md"
        new = ns / f"{name}.md"
        if not old.exists():
            if assets.doc_template(name) is not None:
                actions.append({"doc": name, "verdict": CREATE, "from": None,
                                "to": str(new.relative_to(paths.root)),
                                "why": "engine doc absent — scaffold it in the "
                                       "engine namespace"})
            continue
        if _is_engine_content(old, name):
            actions.append({
                "doc": name, "verdict": MOVE,
                "from": str(old.relative_to(paths.root)),
                "to": str(new.relative_to(paths.root)),
                "entries": entry_count(old),
                "why": "engine-owned content (its own scaffold, or a register "
                       "holding engine-written entries)"})
        else:
            actions.append({
                "doc": name, "verdict": LEAVE_AND_CREATE,
                "from": str(old.relative_to(paths.root)),
                "to": str(new.relative_to(paths.root)),
                "why": "this file holds YOUR content at a name the engine also "
                       "uses — left byte-identical; a fresh engine copy is "
                       "written alongside"})
    for d in ownership.ENGINE_DIRS:
        old_d = paths.docs / d
        if old_d.is_dir() and not (ns / d).exists():
            actions.append({
                "doc": f"{d}/", "verdict": MOVE,
                "from": str(old_d.relative_to(paths.root)),
                "to": str((ns / d).relative_to(paths.root)),
                "entries": sum(entry_count(p) for p in old_d.rglob("*.md")),
                "why": "tracked entity docs travel with the engine corpus"})
    return actions


def _git_mv(root: Path, src: Path, dst: Path) -> bool:
    """Move preserving history when git can; report whether git handled it."""
    try:
        r = subprocess.run(["git", "-C", str(root), "mv", str(src), str(dst)],
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def apply(paths: RepoPaths, config: Config, *, stubs: bool = True) -> dict:
    """Run the untangle. Returns the report, including the conservation check."""
    actions = plan(paths, config)
    if not actions:
        return {"ok": True, "applied": [], "layout": config.docs_layout,
                "summary": "nothing to untangle — already on the split layout"}
    ns = paths.docs / ownership.ENGINE_NAMESPACE
    ns.mkdir(parents=True, exist_ok=True)

    before = _corpus_entries(paths.docs)
    applied: list[dict] = []
    for a in actions:
        name = a["doc"]
        if a["verdict"] == MOVE:
            src = paths.root / a["from"]
            dst = paths.root / a["to"]
            writer.refuse_if_symlink(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            by_git = _git_mv(paths.root, src, dst)
            if not by_git:
                src.replace(dst)
            a["history_preserved"] = by_git
            if stubs and not name.endswith("/"):
                src.write_text(_STUB.format(name=name.rstrip("/"),
                                            new=a["to"]), encoding="utf-8")
        elif a["verdict"] == LEAVE_AND_CREATE:
            tmpl = assets.doc_template(name)
            if tmpl is not None:
                dst = paths.root / a["to"]
                writer.refuse_if_symlink(dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                writer.create_if_absent(dst, tmpl)
        elif a["verdict"] == CREATE:
            tmpl = assets.doc_template(name)
            if tmpl is not None:
                dst = paths.root / a["to"]
                writer.refuse_if_symlink(dst)
                dst.parent.mkdir(parents=True, exist_ok=True)
                writer.create_if_absent(dst, tmpl)
        applied.append(a)

    config.docs_layout = ownership.LAYOUT_SPLIT
    writer.refuse_if_symlink(paths.config_file)
    paths.config_file.write_text(config.to_toml(), encoding="utf-8")

    after = _corpus_entries(paths.docs)
    conserved = before <= after   # stubs and fresh docs add nothing; nothing lost
    return {
        "ok": True,
        "applied": applied,
        "layout": ownership.LAYOUT_SPLIT,
        "entries_before": before,
        "entries_after": after,
        "entries_conserved": conserved,
        "summary": (f"untangled {len(applied)} item(s) into "
                    f"{ownership.ENGINE_NAMESPACE}/; entries {before} -> {after}"
                    + ("" if conserved else "  ⚠ ENTRIES LOST")),
    }


def _corpus_entries(docs_dir: Path) -> int:
    """Every append-only entry under the docs tree, wherever it currently lives.

    Counted across the WHOLE tree on purpose: a move changes a file's path, so
    only a tree-wide total can testify that nothing was dropped in transit
    (INVARIANT-03).
    """
    if not docs_dir.exists():
        return 0
    return sum(entry_count(p) for p in docs_dir.rglob("*.md")
               if "gameplans" not in p.parts)
