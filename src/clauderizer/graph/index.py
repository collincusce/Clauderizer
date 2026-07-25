"""Scan the docs tree into a graph of entities; cache to ``index.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..model import Drop, Entity

# Directories under the repo root we never scan for entities.
_SKIP_DIRS = {".git", ".venv", "node_modules", ".clauderizer", "__pycache__"}


@dataclass(frozen=True)
class Collision:
    """Two entity docs declaring the same ``id``. Last one wins (unchanged), but
    the loser is no longer silent: an id collision makes one of the two files
    invisible to every graph consumer with nothing anywhere reporting it."""

    id: str
    kept: Path
    shadowed: Path

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "kept": str(self.kept), "shadowed": str(self.shadowed)}

    def describe(self) -> str:
        return f"{self.id}: {self.shadowed} is shadowed by {self.kept}"


@dataclass
class Graph:
    entities: dict[str, Entity] = field(default_factory=dict)
    root: Path | None = None
    #: Entity-shaped files that could not be indexed (D-018/D-065). A graph that
    #: cannot say what it FAILED to load is asserting a DAG from evidence it
    #: never read.
    drops: list[Drop] = field(default_factory=list)
    #: Duplicate-id shadowings observed during the scan.
    collisions: list[Collision] = field(default_factory=list)

    @property
    def entity_files_seen(self) -> int:
        """Every file that intended to be an entity: indexed + dropped +
        shadowed. The accounting identity a caller can check."""
        return len(self.entities) + len(self.drops) + len(self.collisions)

    def integrity(self) -> dict:
        """The scan's own honesty report — what was indexed, and what was not."""
        return {
            "entities_indexed": len(self.entities),
            "dropped": len(self.drops),
            "collisions": len(self.collisions),
            "entities_on_disk": self.entity_files_seen,
            "drops": [d.to_dict() for d in self.drops],
            "collision_details": [c.to_dict() for c in self.collisions],
            "ok": not self.drops and not self.collisions,
        }

    def get(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def all(self) -> list[Entity]:
        return list(self.entities.values())

    def by_type(self, type_: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == type_]

    def to_cache(self) -> dict:
        return {
            "version": 1,
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
        }


def build(docs_dir: Path) -> Graph:
    """Build a graph by scanning every ``*.md`` under ``docs_dir`` for frontmatter."""
    graph = Graph(root=docs_dir)
    if not docs_dir.exists():
        return graph
    for path in sorted(docs_dir.rglob("*.md")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        loaded = Entity.from_file(path)
        if loaded is None:
            continue                      # ordinary prose — never was an entity
        if isinstance(loaded, Drop):
            graph.drops.append(loaded)
            continue
        prior = graph.entities.get(loaded.id)
        if prior is not None:
            # Last-wins is preserved so no existing graph changes shape; the
            # shadowed file is simply no longer invisible.
            graph.collisions.append(Collision(loaded.id, loaded.path, prior.path))
        graph.entities[loaded.id] = loaded
    return graph


def _latest_mtime(docs_dir: Path) -> float:
    latest = 0.0
    if not docs_dir.exists():
        return latest
    for path in docs_dir.rglob("*.md"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest


def write_cache(graph: Graph, cache_file: Path, docs_dir: Path) -> None:
    cache = graph.to_cache()
    cache["docs_mtime"] = _latest_mtime(docs_dir)
    from ..markdown import writer
    writer.write_atomic(cache_file, json.dumps(cache, indent=2, sort_keys=True))


def load_or_rebuild(docs_dir: Path, cache_file: Path) -> Graph:
    """Return a fresh graph, rebuilding the cache if markdown changed.

    This is the freshness guarantee: every consumer that calls this gets a graph
    consistent with what's on disk, regardless of out-of-band edits.
    """
    current_mtime = _latest_mtime(docs_dir)
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if abs(float(cached.get("docs_mtime", -1)) - current_mtime) < 1e-6:
                # Cache is fresh, but we still rebuild from markdown because it's
                # cheap and guarantees correctness. The mtime check just lets us
                # skip the cache *write*.
                return build(docs_dir)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    graph = build(docs_dir)
    write_cache(graph, cache_file, docs_dir)
    return graph
