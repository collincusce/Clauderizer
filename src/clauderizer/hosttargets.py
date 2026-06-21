"""Per-host wiring emitters (P4): write Clauderizer's MCP registration into each
host's own project config, non-destructively, with a PORTABLE command.

The cross-host substrate (D-029) already gives every host the cz_* tools over MCP
and the AGENTS.md floor (P2); this module is the last mile — telling each host WHERE
its MCP-server registration lives and writing it there without clobbering the user's
other servers (the top config-safety risk, D-031). JSON project configs are
auto-written; global-config and TOML hosts are guide-only (D-031, O-04).

The emitted command is machine-INDEPENDENT (uvx resolves clauderizer from PyPI) — a
committable config must never carry an absolute venv path or a wsl.exe username shim,
which is exactly what the local dogfood .mcp.json carries and what must NOT ship.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# The portable launch command for a COMMITTABLE config — no absolute path, no shim.
# Matches the project's drop-in identity ("uvx --from clauderizer … needs nothing
# else"). The local .mcp.json may use an absolute path; an emitted one may not.
PORTABLE_COMMAND = ["uvx", "--from", "clauderizer", "clauderizer-mcp"]


@dataclass(frozen=True)
class HostEmitter:
    id: str
    config_path: str   # relative to repo root (or ~/ for global -> guide-only)
    servers_key: str   # the JSON object key that holds MCP servers
    auto_write: bool   # False -> guide-only (global config, or non-JSON format)
    note: str = ""


# Verified against each host's own docs 2026-06-21 (docs/CROSS-HOST.md §3). Exact
# key/path is locked by the golden tests; confirm live when each host is
# integration-tested (O-02 residual).
HOST_EMITTERS: dict[str, HostEmitter] = {
    "cursor":     HostEmitter("cursor", ".cursor/mcp.json", "mcpServers", True),
    "copilot":    HostEmitter("copilot", ".vscode/mcp.json", "servers", True,
                              "VS Code agent mode uses the 'servers' key"),
    "continue":   HostEmitter("continue", ".continue/mcpServers/clauderizer.json",
                              "mcpServers", True),
    "zed":        HostEmitter("zed", ".zed/settings.json", "context_servers", True,
                              "Zed uses 'context_servers', not 'mcpServers'"),
    "gemini-cli": HostEmitter("gemini-cli", ".gemini/settings.json", "mcpServers", True),
    "cline":      HostEmitter("cline", ".cline/mcp.json", "mcpServers", True,
                              "Cline CLI; the VS Code extension is global-UI only"),
    "amp":        HostEmitter("amp", ".amp/settings.json", "amp.mcpServers", True,
                              "run `amp mcp approve clauderizer` afterwards"),
    # guide-only — TOML (no stdlib writer, O-04) or global config (D-031):
    "codex":      HostEmitter("codex", ".codex/config.toml", "", False,
                              "TOML config -> guide-only (O-04)"),
    "windsurf":   HostEmitter("windsurf", "~/.codeium/windsurf/mcp_config.json", "",
                              False, "global MCP config -> guide-only (D-031)"),
    "kimi":       HostEmitter("kimi", "~/.kimi/config.toml", "", False,
                              "global TOML -> guide-only (see .clauderizer/kimi-setup.md)"),
}


def is_path_safe(argv: list[str]) -> bool:
    """A command is safe to COMMIT only when it carries no machine-specific absolute
    path: no POSIX '/...', no 'X:\\' drive path, no wsl.exe shim (D-031). The
    portable uvx form passes; the local dogfood absolute venv path does not."""
    for tok in argv:
        if tok.startswith("/") or (len(tok) > 1 and tok[1] == ":"):
            return False
        if "wsl.exe" in tok.lower():
            return False
    return True


def _entry(argv: list[str]) -> dict:
    return {"command": argv[0], "args": list(argv[1:])}


def emit_mcp(host_id: str, repo_root: Path, argv: list[str] | None = None) -> Path | None:
    """Write/merge the clauderizer MCP registration into the host's project config,
    preserving every OTHER server and key (non-destructive). Returns the path
    written, or None for guide-only hosts. Raises on a path-unsafe command — a
    committable config must be machine-independent (D-031)."""
    em = HOST_EMITTERS[host_id]
    argv = argv or PORTABLE_COMMAND
    if not em.auto_write:
        return None
    if not is_path_safe(argv):
        raise ValueError(
            f"refusing to emit a machine-specific command into {em.config_path}: "
            f"{argv!r} — use the portable uvx form (D-031 path-safety)"
        )
    path = repo_root / em.config_path
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    servers = data.setdefault(em.servers_key, {})
    servers["clauderizer"] = _entry(argv)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def remove_mcp(host_id: str, repo_root: Path) -> bool:
    """Uninstall: remove ONLY the clauderizer server from the host's config, leaving
    every other server and key intact. Returns True if something was removed."""
    em = HOST_EMITTERS[host_id]
    if not em.auto_write:
        return False
    path = repo_root / em.config_path
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get(em.servers_key)
    if not isinstance(servers, dict) or "clauderizer" not in servers:
        return False
    del servers["clauderizer"]
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True
