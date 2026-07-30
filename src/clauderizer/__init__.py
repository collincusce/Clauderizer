"""Clauderizer — drop-in, MCP-native working memory for AI agents.

Markdown is the source of truth. Everything else (the graph index, the MCP
server, the rituals) is derived from it and can be rebuilt at any time.
"""

__version__ = "2.0.0"

# The version of the gameplan procedure this engine was built against. The
# engine ships GAMEPLAN-PROCEDURE.md verbatim; `clauderize doctor` warns if a
# host repo's procedure has drifted to a different MAJOR version, and
# `clauderize upgrade` modernizes a corpus stamped with an older version.
PROCEDURE_VERSION = "2.0.0"


def is_prerelease(version: str | None = None) -> bool:
    """PEP 440 pre/dev segment test for OUR version strings (aN/bN/rcN/.devN).

    Post-releases are releases, not pre-releases."""
    import re
    v = __version__ if version is None else version
    return bool(re.search(r"(?:a|b|rc)\d+$|\.dev\d+$", v))


def portable_from_spec(extra: str = "") -> str:
    """The ``--from`` spec for portable/committable wiring.

    Bare ``clauderizer[...]`` on stable releases; ``==``-pinned on
    pre-releases — an unpinned ``uvx`` resolve only ever sees the latest
    STABLE, so a pre-release engine emitting the bare form silently hands the
    repo to a different (older) serving engine: the 2.0.0a1 alpha caveat,
    same family as H-30's serving-vs-tree split."""
    name = f"clauderizer[{extra}]" if extra else "clauderizer"
    return f"{name}=={__version__}" if is_prerelease() else name
