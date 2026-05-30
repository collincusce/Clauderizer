"""The Project DAG: a graph of frontmatter-tracked entities.

- ``index`` scans the docs tree into an in-memory graph (cached to index.json).
- ``query`` answers lookup / dependents / dependencies / pin-violation questions.
- ``cascade`` does the post-hoc forward walk and renders a cascade report.

The cache is never authoritative. If it is stale or missing it is rebuilt from
the markdown — markdown always wins.
"""
