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
# The MCP server needs the optional `mcp` extra (H-14/H-15); without [mcp] the
# process exits with a missing-package notice and never serves. The local
# dogfood .mcp.json may use an absolute path; an emitted one may not.
PORTABLE_COMMAND = ["uvx", "--from", "clauderizer[mcp]", "clauderizer-mcp"]


@dataclass(frozen=True)
class HostEmitter:
    id: str
    config_path: str   # relative to repo root (or ~/ for global -> guide-only)
    servers_key: str   # the JSON object key that holds MCP servers
    auto_write: bool   # False -> guide-only (global config, or non-JSON format)
    note: str = ""


# Verified against each host's own docs 2026-06-21 (docs/CROSS-HOST.md §3);
# grok row verified 2026-07-09 (gameplan 2026-07-09-grok-build-tui-host-support).
# Exact key/path is locked by the golden tests; confirm live when each host is
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
    # Grok Build TUI: loads project .mcp.json (portable auto-write) + optional
    # .grok/config.toml (TOML guide-only). Governance hooks under .grok/hooks/
    # (Hook→ctx=no — never claim Tier-1). Shares .mcp.json path with claude-code
    # wiring; detect_host_target must not treat .mcp.json alone as grok.
    "grok":       HostEmitter("grok", ".mcp.json", "mcpServers", True,
                              "Grok loads project .mcp.json; hooks under .grok/hooks/; "
                              "optional .grok/config.toml is guide-only TOML"),
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

# Multi-host default (D-046): enabled_hosts = ["*"] means every known project-
# level host. Concrete lists scope the footprint; --host is a one-shot filter.
ALL_HOSTS = "*"


def all_host_ids() -> list[str]:
    """Concrete host ids wired by the multi-host default (claude-code + emitters)."""
    return [CLAUDE_CODE, *HOST_EMITTERS]


def expand_enabled_hosts(enabled: list[str] | None) -> list[str]:
    """Resolve config enabled_hosts → concrete host ids (order stable)."""
    if not enabled or ALL_HOSTS in enabled:
        return all_host_ids()
    out: list[str] = []
    for h in enabled:
        hid = parse_host_target(h)
        if hid not in out:
            out.append(hid)
    return out


def hosts_to_wire(
    *,
    host_flag: str | None,
    enabled_hosts: list[str] | None,
) -> list[str]:
    """Which hosts this init run should touch (D-046).

    - ``--host X`` → scope filter: only X (regardless of enabled_hosts).
    - bare init → expand enabled_hosts (default ``["*"]`` = all).
    """
    if host_flag is not None and str(host_flag).strip():
        return [parse_host_target(host_flag)]
    return expand_enabled_hosts(enabled_hosts)


def configure_hints(host_id: str) -> list[str]:
    """Configure-on-demand steps when a host is enabled but incomplete (D-048).
    Advisory only — never hard-blocks (INVARIANT-05)."""
    hints: dict[str, list[str]] = {
        "grok": [
            "Grant folder trust: `/hooks-trust` or launch with `--trust` "
            "(gates project MCP + .grok/hooks).",
            "SessionStart stdout is NOT model context — call cz_status "
            "(AGENTS.md floor + P7 bootstrap).",
        ],
        "amp": [
            "After wiring, run `amp mcp approve clauderizer` so Amp loads the server.",
        ],
        "codex": [
            "TOML is guide-only — merge the portable command from "
            "`.clauderizer/codex-mcp-setup.md` into `.codex/config.toml`.",
        ],
        "kimi": [
            "Global TOML is guide-only — merge hooks/MCP from "
            "`.clauderizer/kimi-setup.md` or `kimi-mcp-setup.md` into `~/.kimi/config.toml`.",
        ],
        "windsurf": [
            "MCP config is global — see `.clauderizer/windsurf-mcp-setup.md` "
            "(never auto-edited, D-031).",
        ],
        "claude-code": [
            "Open a Claude Code session in this repo — SessionStart injects the digest.",
        ],
    }
    return list(hints.get(host_id, [
        f"Open {host_id} on this repo; AGENTS.md floor tells the agent to call cz_status first.",
    ]))

# Paths that claude-code init also writes — auto-detect must not treat these
# alone as evidence of a non-claude host (dogfood .mcp.json is claude-code).
_SHARED_WITH_CLAUDE_CODE = frozenset({".mcp.json"})

# Grok governance hooks (D1): SessionStart/UserPromptSubmit fire for scrollback
# side-effects; stdout is NOT model context (best_tier=4 + P7 bootstrap).
GROK_HOOKS_REL = ".grok/hooks/clauderizer.json"
GROK_HOOK_EVENTS = ("SessionStart", "UserPromptSubmit")
# Portable, native-safe hook command — no wsl.exe, no absolute repo path (D3).
# Grok expands env vars in command strings; GROK_WORKSPACE_ROOT is runner-injected.
PORTABLE_HOOK_COMMAND = (
    'cd "${GROK_WORKSPACE_ROOT}" && uvx --from clauderizer clauderizer-hook'
)


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

    Grok is detected via its unique ``.grok/hooks/clauderizer.json`` (not
    ``.mcp.json`` alone — that path is shared with claude-code dogfood wiring).
    """
    grok_hooks = repo_root / GROK_HOOKS_REL
    if grok_hooks.is_file():
        try:
            data = json.loads(grok_hooks.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        if isinstance(data.get("hooks"), dict):
            return "grok"

    found: list[str] = []
    for host_id, em in HOST_EMITTERS.items():
        if not em.auto_write:
            continue
        if em.config_path in _SHARED_WITH_CLAUDE_CODE:
            continue  # .mcp.json alone is not evidence of a non-claude host
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
# Grok is intentionally ABSENT: its hooks are auto-written as governance-only
# JSON under .grok/hooks/ (Hook→ctx=no); a Tier-1 guide would be dishonest (D1).
HOOK_GUIDE_HOSTS: dict[str, tuple[str, list[str]]] = {
    "copilot":    (".github/hooks/*.json", ["SessionStart", "UserPromptSubmit"]),
    "codex":      ("~/.codex/config.toml or .codex/hooks.json",
                   ["SessionStart", "UserPromptSubmit"]),
    "gemini-cli": (".gemini/settings.json (hooks)", ["SessionStart", "BeforeAgent"]),
    "windsurf":   (".windsurf/hooks.json", ["pre_user_prompt"]),
    "cline":      (".clinerules/hooks/ (POSIX only)", ["TaskStart", "UserPromptSubmit"]),
    "amp":        (".amp/plugins/*.ts", ["session.start", "agent.start"]),
}


def grok_hooks_payload(hook_command: str | None = None) -> dict:
    """Native Grok hook JSON (``.grok/hooks/*.json`` format). Governance only —
    passive events ignore stdout, so this never claims digest→context (D1)."""
    cmd = hook_command or PORTABLE_HOOK_COMMAND
    entry = {"hooks": [{"type": "command", "command": cmd, "timeout": 30}]}
    return {"hooks": {event: [entry] for event in GROK_HOOK_EVENTS}}


def emit_grok_hooks(repo_root: Path, hook_command: str | None = None) -> Path:
    """Auto-write ``.grok/hooks/clauderizer.json`` with a native-safe command (D2/D3).
    Idempotent: only rewrites when content differs. Never touches ``.claude/``."""
    path = repo_root / GROK_HOOKS_REL
    refuse_if_symlink(path)
    text = json.dumps(grok_hooks_payload(hook_command), indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return path
    path.write_text(text, encoding="utf-8")
    return path


def remove_grok_hooks(repo_root: Path) -> bool:
    """Uninstall: remove Clauderizer's Grok hook file only. Returns True if removed."""
    path = repo_root / GROK_HOOKS_REL
    if not path.exists():
        return False
    path.unlink()
    # Best-effort empty-dir cleanup (.grok/hooks then .grok)
    for parent in (path.parent, path.parent.parent):
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            break
    return True


def grok_setup_guide() -> str:
    """Honest setup notes for Grok: portable MCP, governance hooks, folder-trust,
    and NO Tier-1 SessionStart claim (best_tier=4 + P7 bootstrap)."""
    mcp = " ".join(PORTABLE_COMMAND)
    return f"""# Clauderizer × Grok Build TUI setup

Generated by `clauderize init --host grok`. Safe to delete; re-created on re-init.

## What is auto-written

1. **Portable `.mcp.json`** — `clauderizer` server via `{mcp}` (path-safe; no
   `wsl.exe`, no absolute venv path). Grok merges project `.mcp.json` natively.
2. **Governance hooks** — `.grok/hooks/clauderizer.json` on SessionStart +
   UserPromptSubmit. Grok **ignores passive-hook stdout** (Hook→ctx = no), so
   these do **not** inject the status digest into model context. They still run
   for scrollback annotations / side-effects.
3. **AGENTS.md floor** — already written host-agnostically; Grok loads it natively.

## What is NOT automatic (best_tier = 4 + P7)

- **No Tier-1 SessionStart digest.** Cold orientation is: AGENTS.md floor
  ("call `cz_status` first") + MCP tools + server-side bootstrap on the first
  non-status tool result.
- **MCP prompts are not slash commands** on Grok (builtins + skills only). The
  server still exposes `cz-status` for hosts that surface prompts; do not expect
  `/cz-status` here.

## Folder trust (required for project hooks + project MCP)

The first time you open this repo in Grok, grant trust:

```
/hooks-trust
```

or launch with `--trust`. Trust is stored in `~/.grok/trusted_folders.toml` and
gates project hooks, project MCP, and LSP together. Global `~/.grok/hooks/` needs
no trust.

## Optional: project `.grok/config.toml` (guide-only)

Grok also reads TOML MCP config. Clauderizer does not rewrite TOML (no stdlib
writer). If you prefer TOML over `.mcp.json`, add:

```toml
[mcp_servers.clauderizer]
command = "uvx"
args = ["--from", "clauderizer", "clauderizer-mcp"]
enabled = true
```

`.mcp.json` alone is enough for most installs.

## Dual Claude Code + Grok machines

- Claude keeps `.claude/settings.json` + its session_host composition (may use
  `wsl.exe` on Windows→WSL).
- Grok uses `.grok/hooks/` with a **native-safe** command (no `wsl.exe`).
- Do **not** commit machine-specific `wsl.exe` MCP args (D-031). Prefer the
  portable uvx form Clauderizer emits for `init --host grok`.
"""


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
       guided-wiring guide (``hook_setup_guide``). Grok instead gets auto-written
       governance hooks + an honesty guide (never a Tier-1 claim).

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

    if host_id == "grok":
        hooks_path = repo_root / GROK_HOOKS_REL
        results.append(EmitResult(
            "hooks", hooks_path,
            _emit_idempotent(hooks_path, lambda: emit_grok_hooks(repo_root))))
        guide_path = repo_root / ".clauderizer" / "grok-mcp-setup.md"
        results.append(EmitResult(
            "mcp-guide", guide_path,
            _write_text_if_changed(guide_path, grok_setup_guide())))
    else:
        guide = hook_setup_guide(host_id)
        if guide is not None:
            path = repo_root / ".clauderizer" / f"{host_id}-hook-setup.md"
            results.append(EmitResult(
                "hook-guide", path, _write_text_if_changed(path, guide)))

    return results
