"""Structural integrity checks over the Project DAG: dangling edges + cycles.

Deterministic, stdlib-only, and pure — no I/O, no mutation, no raising. The
engine surfaces these findings advisorily through the existing drift channel
(status_bundle); the agent decides what to do. Per INVARIANT-05 the discipline
gates never block a write or a session and carry no enable/disable flag, and per
INVARIANT-06 the hook handlers that print this stay read-only and exit 0.

``pin_violations`` deliberately skips edges whose target is unknown (it cannot
verify a semver it can't find), so dangling edges fall through there silently —
``dangling_edges`` is the companion that names exactly those.
"""

from __future__ import annotations

from dataclasses import dataclass

from .index import Graph


@dataclass(frozen=True)
class DagIssues:
    """The structural findings for a graph.

    ``dangling`` is sorted ``(src, missing_target)`` pairs — a ``depends_on``
    target that is not a known entity. ``cycles`` is a sorted list of cycles,
    each the sorted membership of one ``depends_on`` cycle (e.g. ``["a", "b"]``
    for ``a -> b -> a``).
    """

    dangling: list[tuple[str, str]]
    cycles: list[list[str]]


def dangling_edges(graph: Graph) -> list[tuple[str, str]]:
    """``(src, missing_target)`` for every ``depends_on`` edge whose target is
    not a known entity. Sorted and deduplicated for deterministic output."""
    out: set[tuple[str, str]] = set()
    for entity in graph.all():
        for pin in entity.depends_on:
            if graph.get(pin.target) is None:
                out.add((entity.id, pin.target))
    return sorted(out)


def cycles(graph: Graph) -> list[list[str]]:
    """Sorted list of ``depends_on`` cycles (only edges among known entities).

    Uses Tarjan's strongly-connected-components algorithm (iterative, so deep
    graphs can't blow the stack). Each SCC with more than one node is a cycle;
    a single node is reported only when it depends on itself. Membership within
    each cycle and the list of cycles are both sorted for determinism.
    """
    # Adjacency restricted to edges whose target exists — a dangling target is
    # not a cycle, it's reported separately by dangling_edges.
    adj: dict[str, list[str]] = {}
    for entity in graph.all():
        targets = sorted(
            {p.target for p in entity.depends_on if graph.get(p.target) is not None}
        )
        adj[entity.id] = targets

    index_of: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    counter = 0
    found: list[list[str]] = []

    for root in sorted(adj):
        if root in index_of:
            continue
        # Iterative DFS: work items are (node, next_child_index).
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, child_i = work[-1]
            if child_i == 0:
                index_of[node] = lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            neighbors = adj[node]
            if child_i < len(neighbors):
                work[-1] = (node, child_i + 1)
                nxt = neighbors[child_i]
                if nxt not in index_of:
                    work.append((nxt, 0))
                elif nxt in on_stack:
                    lowlink[node] = min(lowlink[node], index_of[nxt])
                continue
            # All children visited: settle this node.
            if lowlink[node] == index_of[node]:
                comp: list[str] = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                if len(comp) > 1 or node in adj.get(node, ()):
                    found.append(sorted(comp))
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

    return sorted(found)


def validate(graph: Graph) -> DagIssues:
    """Run both structural checks and return the combined, deterministic result."""
    return DagIssues(dangling=dangling_edges(graph), cycles=cycles(graph))
