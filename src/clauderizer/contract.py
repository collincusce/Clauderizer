"""The external read-contract version stamp (PhaseKeep m0 ask, O-05).

Every ops-registry result — and therefore every ``--json`` CLI output and MCP
tool result, since both transports execute the same registry — carries an
explicit ``schema_version`` so external clients can gate rendering on it
instead of guessing. Compatibility rules (phasekeep proposal §6.2): additive
changes bump the minor, breaking changes bump the major, clients ignore
unknown fields and degrade explicitly on a major they don't support.

Distinct from ``graph.abstract_index.SCHEMA_VERSION`` (an internal cache
format) and from ``config.CONFIG_VERSION`` — this constant versions the
*emitted JSON surface only*.
"""

from __future__ import annotations

CONTRACT_SCHEMA_VERSION = "1.0"


def stamp(result):
    """Stamp ``schema_version`` onto a dict result (idempotent, non-dict passthrough)."""
    if isinstance(result, dict) and "schema_version" not in result:
        result["schema_version"] = CONTRACT_SCHEMA_VERSION
    return result
