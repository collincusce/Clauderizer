"""Scan the docs tree into a graph of entities; cache to ``index.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..model import Entity

# Directories under the repo root we never scan for entities.
_SKIP_DIRS = {".git", ".venv", "node_modules", ".clauderizer", "__pycache__"}


@dataclass
class Graph:
    entities: dict[str, Entity] = field(default_factory=dict)
    root: Path | None = None

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
        entity = Entity.from_file(path)
        if entity is not None:
            graph.entities[entity.id] = entity
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
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


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
