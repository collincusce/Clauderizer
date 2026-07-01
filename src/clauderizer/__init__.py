"""Clauderizer — drop-in, MCP-native working memory for AI agents.

Markdown is the source of truth. Everything else (the graph index, the MCP
server, the rituals) is derived from it and can be rebuilt at any time.
"""

__version__ = "1.4.0"

# The version of the gameplan procedure this engine was built against. The
# engine ships GAMEPLAN-PROCEDURE.md verbatim; `clauderize doctor` warns if a
# host repo's procedure has drifted to a different MAJOR version, and
# `clauderize upgrade` modernizes a corpus stamped with an older version.
PROCEDURE_VERSION = "1.5.0"
