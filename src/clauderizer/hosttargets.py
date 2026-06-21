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
import re
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


# --- P5: bespoke hosts — native instructions floor + hook setup guides ----------

# The Tier-4 floor, condensed for a host's NATIVE instructions file (Continue,
# Gemini) which do not read AGENTS.md. Same intent as the AGENTS.md floor (P2),
# host-neutral: load memory first.
FLOOR_INSTRUCTION = (
    "## Clauderizer\n\n"
    "This repo uses Clauderizer for durable, cross-session memory (an MCP server "
    "exposes it as cz_* tools). **At the start of every session, call `cz_status` "
    "first** — it loads the gameplan, phase, baseline, and open items. To begin or "
    "continue work, call `cz_next_phase_context` then `cz_preflight`. Never hand-edit "
    "tracked docs; use the cz_* tools.\n"
)

# Hosts that do NOT read AGENTS.md -> the floor must go in their native rules file.
NATIVE_INSTRUCTIONS: dict[str, str] = {
    "continue": ".continue/rules/clauderizer.md",
    "gemini-cli": "GEMINI.md",
}

_MARK = re.compile(r"<!-- clauderizer:start -->.*?<!-- clauderizer:end -->\n?", re.S)


def emit_instructions(host_id: str, repo_root: Path) -> Path | None:
    """Write the Tier-4 floor into a host's NATIVE instructions file (Continue,
    Gemini — they do not read AGENTS.md). Marker-block upsert preserves the user's
    own content. Returns None for hosts that already read AGENTS.md (floor already
    there, P2)."""
    rel = NATIVE_INSTRUCTIONS.get(host_id)
    if rel is None:
        return None
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    block = f"<!-- clauderizer:start -->\n{FLOOR_INSTRUCTION}<!-- clauderizer:end -->\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if _MARK.search(existing):
        new = _MARK.sub(block, existing)                       # replace in place
    else:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        new = existing + sep + block                            # append, preserve rest
    path.write_text(new, encoding="utf-8")
    return path


# Bespoke hosts have lifecycle hooks (Tier 1) but each uses a different config
# format; rather than emit an unverified schema we ship a setup guide (the kimi
# pattern, D-031). Event names verified 2026-06-21 (docs/CROSS-HOST.md §3); the exact
# config shape is confirmed at integration (O-02 residual).
HOOK_GUIDE_HOSTS: dict[str, tuple[str, list[str]]] = {
    "copilot":    (".github/hooks/*.json", ["SessionStart", "UserPromptSubmit"]),
    "codex":      ("~/.codex/config.toml or .codex/hooks.json",
                   ["SessionStart", "UserPromptSubmit"]),
    "gemini-cli": (".gemini/settings.json (hooks)", ["SessionStart", "BeforeAgent"]),
    "windsurf":   (".windsurf/hooks.json", ["pre_user_prompt"]),
    "cline":      (".clinerules/hooks/ (POSIX only)", ["TaskStart", "UserPromptSubmit"]),
    "amp":        (".amp/plugins/*.ts", ["session.start", "agent.start"]),
}


def hook_setup_guide(host_id: str, hook_argv: list[str] | None = None) -> str | None:
    """A per-host hook setup guide (the kimi pattern): wire `clauderizer-hook` to the
    host's session-start-equivalent events for Tier-1 automatic status injection.
    Returns None for hosts with no hook system (the floor + prompt still apply)."""
    spec = HOOK_GUIDE_HOSTS.get(host_id)
    if spec is None:
        return None
    location, events = spec
    cmd = " ".join(hook_argv or ["uvx", "--from", "clauderizer", "clauderizer-hook"])
    return (
        f"# Clauderizer hook setup for {host_id}\n\n"
        f"For Tier-1 automatic status injection, wire this command to {host_id}'s "
        f"session hook ({location}) on these events: {', '.join(events)}.\n\n"
        f"Command: `{cmd}`\n\n"
        f"The hook prints the `[Clauderizer]` digest, which {host_id} injects into "
        f"context. Without it you still have the floor (Tier 4) and /cz-status "
        f"(Tier 3).\n"
    )


# --- P6: wiring-contract verification — the in-process host-simulator (D-032) ----

def verify_emitted_wiring(host_id: str, repo_root: Path) -> tuple[bool, str]:
    """Wiring-contract check (D-032): emit the host's config, read it back, and
    confirm the clauderizer entry is well-formed (command + args), path-safe, and
    launches clauderizer-mcp. The 'does the real host actually read it' consumption
    proof is irreducibly manual (D-032) — not this."""
    em = HOST_EMITTERS[host_id]
    if not em.auto_write:
        return True, "guide-only (nothing auto-written to verify)"
    path = emit_mcp(host_id, repo_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"emitted config is not valid JSON: {exc}"
    entry = (data.get(em.servers_key) or {}).get("clauderizer")
    if not isinstance(entry, dict) or "command" not in entry:
        return False, "missing or malformed clauderizer entry"
    argv = [entry["command"], *entry.get("args", [])]
    if not is_path_safe(argv):
        return False, f"path-unsafe (machine-specific) command: {argv}"
    if not any("clauderizer-mcp" in tok for tok in argv):
        return False, "command does not launch clauderizer-mcp"
    return True, "wiring contract OK"


def wiring_contract_sweep(repo_root: Path) -> dict[str, tuple[bool, str]]:
    """The release gate (D-032): run the wiring-contract check for every auto-write
    host. Green only when every host's emitted config passes. Runs in CI via the
    test suite; consumption proof (a real host reading it) is a manual spot-check."""
    return {h: verify_emitted_wiring(h, repo_root)
            for h, em in HOST_EMITTERS.items() if em.auto_write}


def path_safety_audit(repo_root: Path) -> list[str]:
    """Scan a repo's committed host MCP configs for a machine-specific absolute path
    (the O-06 leak). Returns offending 'path: argv' strings — empty is clean. A
    committable config must carry only a portable command (D-031)."""
    offenders: list[str] = []
    rels = [".mcp.json", *(em.config_path for em in HOST_EMITTERS.values() if em.auto_write)]
    for rel in rels:
        p = repo_root / rel
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for key in ("mcpServers", "servers", "context_servers", "amp.mcpServers"):
            entry = (data.get(key) or {}).get("clauderizer")
            if isinstance(entry, dict):
                argv = [entry.get("command", ""), *entry.get("args", [])]
                if not is_path_safe(argv):
                    offenders.append(f"{rel}: {argv}")
    return offenders
