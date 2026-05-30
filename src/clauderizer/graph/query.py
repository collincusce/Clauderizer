"""Queries over the Project DAG: lookup, dependents, dependencies, pin checks."""

from __future__ import annotations

from dataclasses import dataclass

from ..model import constraint_satisfied
from .index import Graph


@dataclass
class PinViolation:
    dependent: str
    target: str
    constraint: str
    actual_version: str | None
    reason: str


def lookup(graph: Graph, entity_id: str):
    return graph.get(entity_id)


def dependencies(graph: Graph, entity_id: str) -> list[str]:
    entity = graph.get(entity_id)
    if entity is None:
        return []
    return [p.target for p in entity.depends_on]


def dependents(graph: Graph, entity_id: str) -> list[str]:
    """Direct dependents: entities that declare ``entity_id`` in ``depends_on``."""
    out = []
    for e in graph.all():
        if any(p.target == entity_id for p in e.depends_on):
            out.append(e.id)
    return sorted(out)


def transitive_dependents(graph: Graph, entity_id: str) -> list[str]:
    seen: set[str] = set()
    frontier = [entity_id]
    while frontier:
        current = frontier.pop()
        for dep in dependents(graph, current):
            if dep not in seen:
                seen.add(dep)
                frontier.append(dep)
    return sorted(seen)


def pin_violations(graph: Graph) -> list[PinViolation]:
    """Find dependents whose semver pin is no longer satisfied by the target.

    Only flags genuine MAJOR-style breaks (caret/tilde/exact); unknown or
    unparseable versions are treated as non-violations (the procedure says
    cascade should not flag what it can't verify).
    """
    out: list[PinViolation] = []
    for e in graph.all():
        for pin in e.depends_on:
            if not pin.constraint:
                continue
            target = graph.get(pin.target)
            if target is None:
                continue
            ok = constraint_satisfied(target.version, pin.constraint)
            if ok is False:
                out.append(
                    PinViolation(
                        dependent=e.id,
                        target=pin.target,
                        constraint=pin.constraint,
                        actual_version=target.version,
                        reason=f"{target.version} does not satisfy {pin.constraint}",
                    )
                )
    return out
