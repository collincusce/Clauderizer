---
id: subsys.tools-list
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Tools List

One list — `TOOL_NAMES` — naming every `cz_*` tool the MCP server exposes.

## Why a module for a list

The SessionStart digest advertises the tool surface to the agent, and the MCP server registers it. Those are two different code paths in two different processes, and if each spelled the list itself they would drift the moment a tool was added — the digest promising a tool that does not exist, or omitting one that does. Keeping the names in one place means the digest advertises exactly what the server exposes, by construction rather than by discipline.

There are no functions here. The module is a single list, and that is the whole point: a shared constant cannot disagree with itself.

## The drift this class of thing invites

Independent surfaces that must stay in agreement drift **silently**, and README's MCP tool list proved it — at 1.12.0 it listed 24 tools against `TOOL_NAMES`' 31, missing the entire listing-ops contract, and read as current the whole time. Nothing failed, because prose has no test.

The fix was not a sweep but an **executable seam**: a test that diffs the README's backticked tool names and its count line against `TOOL_NAMES`. Prose that enumerates a code-owned surface gets pinned to that surface, or it rots. This module is the source of truth that pin diffs against, which makes it worth documenting despite having no API at all.

## DAG position

Depends on nothing. Consumed by `mcp_server` (registration), the hook handlers (the digest's tool line), and `cli`. Pinned by the README parity test.
