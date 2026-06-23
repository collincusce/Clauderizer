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

from .markdown.writer import refuse_if_symlink

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


# The default native host: claude-code keeps the original .mcp.json + .claude
# hook wiring (INVARIANT-07). Every other id routes through the per-host
# emitters below — reachable through `clauderize init --host` since P8 (A-001).
CLAUDE_CODE = "claude-code"


class HostTargetError(ValueError):
    """An unknown ``--host`` value, carrying the valid list. Raised by
    :func:`parse_host_target` so init fails friendly (no bare KeyError, P8)."""


def valid_host_targets() -> list[str]:
    """Every host id ``init --host`` accepts: claude-code (native wiring) plus
    each per-host emitter (auto-write and guide-only)."""
    return [CLAUDE_CODE, *HOST_EMITTERS]


def parse_host_target(value: str | None) -> str:
    """Validate a ``--host`` value → the canonical host id.

    Unset (or ``claude-code``) is the default native path; everything else must
    be a known emitter. Raises :class:`HostTargetError` listing the valid hosts
    on an unknown name — the friendly error P8 requires instead of a KeyError
    deep inside ``HOST_EMITTERS[...]``.
    """
    v = (value or CLAUDE_CODE).strip()
    valid = valid_host_targets()
    if v in valid:
        return v
    raise HostTargetError(
        f"unknown host '{v}' — valid hosts: {', '.join(valid)}"
    )


def detect_host_target(repo_root: Path) -> str:
    """Cheap, side-effect-free auto-detection when ``--host`` is omitted and the
    config records nothing yet.

    Adopt the single non-claude host whose project config ALREADY carries a
    ``clauderizer`` registration (a prior per-host init); default to
    ``claude-code`` otherwise. Deliberately conservative: it keys on an existing
    clauderizer entry, never on an unrelated ``.vscode/`` dir, and refuses to
    guess when two hosts are wired (returns the default so init nudges).
    """
    found: list[str] = []
    for host_id, em in HOST_EMITTERS.items():
        if not em.auto_write:
            continue
        path = repo_root / em.config_path
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        servers = data.get(em.servers_key)
        if isinstance(servers, dict) and "clauderizer" in servers:
            found.append(host_id)
    return found[0] if len(found) == 1 else CLAUDE_CODE


def is_path_safe(argv: list[str]) -> bool:
    """A command is safe to COMMIT only when it carries no machine-specific absolute
    path: no POSIX '/...', no 'X:\\' drive path, no wsl.exe shim (D-031). The
    portable uvx form passes; the local dogfood absolute venv path does not."""
    for tok in argv:
        low = tok.lower()
        if tok.startswith("/") or tok.startswith("\\\\") or tok.startswith("//"):
            return False                       # POSIX absolute or UNC path
        if len(tok) > 1 and tok[1] == ":":
            return False                       # Windows drive path (C:\...)
        if "wsl.exe" in low or low == "wsl":
            return False                       # the WSL shim, with or without .exe
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
    refuse_if_symlink(path)
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
    refuse_if_symlink(path)
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
    refuse_if_symlink(path)
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


def _is_git_ignored(repo_root: Path, rel: str) -> bool:
    """True if ``rel`` is gitignored (and thus NOT a committed config). Best-effort
    — if git is unreachable or this is no repo, returns False so the file is still
    audited (fail safe toward MORE scanning, never less)."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(repo_root), "check-ignore", "-q", rel],
                           capture_output=True, stdin=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def path_safety_audit(repo_root: Path) -> list[str]:
    """Scan a repo's COMMITTED host MCP configs for a machine-specific absolute
    path (the O-06 leak). Returns offending 'path: argv' strings — empty is clean.
    A committable config must carry only a portable command (D-031).

    Gitignored configs are skipped: a dogfood repo deliberately keeps a LOCAL
    machine-specific .mcp.json (pointing at its editable engine build) that is
    gitignored, not committed — auditing it would be a false alarm (O-06: 'the
    dogfood .mcp.json is gitignored or portable')."""
    offenders: list[str] = []
    rels = [".mcp.json", *(em.config_path for em in HOST_EMITTERS.values() if em.auto_write)]
    # derive the JSON keys to inspect from the emitter table, not a hardcoded list,
    # so a newly-added host is audited automatically.
    keys = {"mcpServers"} | {em.servers_key for em in HOST_EMITTERS.values()
                             if em.auto_write and em.servers_key}
    for rel in rels:
        p = repo_root / rel
        if not p.exists():
            continue
        if _is_git_ignored(repo_root, rel):
            continue                           # local-only config — not committed
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for key in keys:
            entry = (data.get(key) or {}).get("clauderizer")
            if isinstance(entry, dict):
                argv = [entry.get("command", ""), *entry.get("args", [])]
                if not is_path_safe(argv):
                    offenders.append(f"{rel}: {argv}")
    return offenders


# --- P8: route a non-claude host's full wiring through init ----------------------

def mcp_setup_guide(host_id: str) -> str:
    """The MCP-registration guide for a guide-only host (TOML or global config —
    no stdlib auto-writer, O-04/D-031). Names the host's config location and the
    PORTABLE command to register by hand, so the host still reaches the cz_*
    tools. Non-destructive: written under the repo's .clauderizer/, never the
    host's own global config."""
    em = HOST_EMITTERS[host_id]
    cmd = " ".join(PORTABLE_COMMAND)
    why = em.note or "guide-only — not auto-written"
    return (
        f"# Clauderizer MCP setup for {host_id}\n\n"
        f"{host_id}'s MCP config lives at `{em.config_path}` ({why}). Clauderizer "
        f"does not edit it automatically; register the server yourself with the "
        f"portable command:\n\n"
        f"```\n{cmd}\n```\n\n"
        f"Add a `clauderizer` MCP server entry pointing at that command. Once "
        f"registered you have the cz_* tools; the AGENTS.md floor already tells "
        f"the agent to call `cz_status` first.\n"
    )


@dataclass(frozen=True)
class EmitResult:
    """One file init's host-target branch wrote (or left unchanged). ``changed``
    lets init report honestly and preserves the 'second run = zero diffs'
    invariant for every host, even though the low-level emitters rewrite."""
    label: str   # mcp | mcp-guide | instructions | hook-guide
    path: Path
    changed: bool


def _write_text_if_changed(path: Path, content: str) -> bool:
    prior = path.read_text(encoding="utf-8") if path.exists() else None
    if prior == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _emit_idempotent(path: Path, emit: "callable") -> bool:
    """Run a low-level emitter (which rewrites unconditionally) and report
    whether the target file's bytes actually changed."""
    before = path.read_text(encoding="utf-8") if path.exists() else None
    emit()
    after = path.read_text(encoding="utf-8")
    return before != after


def emit_host_wiring(host_id: str, repo_root: Path) -> list[EmitResult]:
    """Emit everything a non-claude host needs, reached through ``init`` (P8).

    Three pieces, each idempotent and reported:

    1. **MCP registration** — auto-write hosts get a real per-host config
       (``emit_mcp``); guide-only hosts (TOML/global) get a setup guide so they
       still reach the tools by hand.
    2. **Native floor** — hosts that do NOT read AGENTS.md (Continue, Gemini) get
       the floor in their own rules file (``emit_instructions``); the rest already
       have it via the AGENTS.md stanza init writes host-agnostically.
    3. **Hook setup guide** — hosts with a lifecycle hook system get the Tier-1
       guided-wiring guide (``hook_setup_guide``).

    The AGENTS.md floor, skills, and docs are host-agnostic and written by init
    itself — this is strictly the per-host last mile.
    """
    em = HOST_EMITTERS[host_id]
    results: list[EmitResult] = []

    if em.auto_write:
        path = repo_root / em.config_path
        results.append(EmitResult(
            "mcp", path, _emit_idempotent(path, lambda: emit_mcp(host_id, repo_root))))
    else:
        path = repo_root / ".clauderizer" / f"{host_id}-mcp-setup.md"
        results.append(EmitResult(
            "mcp-guide", path, _write_text_if_changed(path, mcp_setup_guide(host_id))))

    rel = NATIVE_INSTRUCTIONS.get(host_id)
    if rel is not None:
        path = repo_root / rel
        results.append(EmitResult(
            "instructions", path,
            _emit_idempotent(path, lambda: emit_instructions(host_id, repo_root))))

    guide = hook_setup_guide(host_id)
    if guide is not None:
        path = repo_root / ".clauderizer" / f"{host_id}-hook-setup.md"
        results.append(EmitResult(
            "hook-guide", path, _write_text_if_changed(path, guide)))

    return results
