"""MCP ``initialize``-handshake verification — a host-agnostic capability probe (D-056).

Extracted from the kimi-desktop wiring (D-055) so any host whose registered MCP
command we want to verify can be checked for CAPABILITY, not mere presence (L-25):
spawn the composed ``{command, args}`` from a non-repo cwd (the way an MCP client
does), complete an MCP ``initialize`` over stdio, and assert
``serverInfo.name == "clauderizer"``. Mirrors ``hosts.spawn_probe``/``verify_wiring``
(which probe the SessionStart hook), but for an MCP server command.

Key facts (verified 2026-07-17): MCP stdio is **newline-delimited JSON-RPC** (not
Content-Length framed), and a Windows ``clauderizer-mcp.exe`` registered for a desktop
host is spawnable from WSL by translating its ``C:\\`` path to the ``/mnt/<drive>``
interop path — so a cross-OS command is a real green, not ``unverifiable``.

``run`` is injectable so tests never spawn a real process.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from . import winhost

PROTOCOL_VERSION = "2024-11-05"
HANDSHAKE_TIMEOUT = 20.0


def init_request() -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                       "clientInfo": {"name": "clauderize-doctor", "version": "1"}}}


def spawn_target(entry: dict, *, platform: str,
                 mnt_root: Path = Path("/mnt")) -> tuple[list[str] | None, str | None]:
    """``(argv, unreachable_reason)``. ``argv`` is what THIS host can spawn to reach
    the registered command; ``unreachable_reason`` is set (argv None) only when the
    command targets a host we genuinely cannot reach → an honest ``unverifiable``
    (never a false pass, never a false fail — L-25). A command whose target is
    reachable-but-absent returns an argv so the spawn fails loudly."""
    command = str(entry.get("command", ""))
    args = [str(a) for a in entry.get("args", [])]
    if not command:
        return None, None
    if Path(command).name.lower() == "wsl.exe":
        if platform != "win32" and shutil.which("wsl.exe") is None:
            return None, "command launches via wsl.exe but Windows interop is unreachable here"
        return [command, *args], None
    is_win = bool(re.match(r"^[A-Za-z]:[\\/]", command)) or command.lower().endswith(".exe")
    if is_win and platform != "win32":
        mnt = winhost.win_path_to_wsl(command, mnt_root=mnt_root)
        if mnt is None:
            return None, f"cannot map Windows command '{command}' to a reachable path"
        return [str(mnt), *args], None                # absent → spawn fails loudly (real fault)
    return [command, *args], None


def server_info(stdout: bytes) -> dict | None:
    """The ``result.serverInfo`` from the first JSON-RPC line that carries it."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith(b"{"):
            continue
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        info = msg.get("result", {}).get("serverInfo") if isinstance(msg, dict) else None
        if isinstance(info, dict):
            return info
    return None


def default_run(argv: list[str], cwd: str | None, stdin: bytes,
                timeout: float) -> tuple[int, bytes, bytes]:
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, cwd=cwd)
    try:
        out, err = p.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise
    return p.returncode or 0, out, err


def handshake_probe(entry: dict, *, cwd: str | None = None, platform: str | None = None,
                    mnt_root: Path = Path("/mnt"), timeout: float = HANDSHAKE_TIMEOUT,
                    run: Callable[..., tuple[int, bytes, bytes]] | None = None) -> dict:
    """Spawn the registered command from ``cwd`` (a NON-repo dir, the way an MCP client
    spawns) and complete an MCP ``initialize`` handshake, asserting
    ``serverInfo.name == 'clauderizer'``. Returns ``{status: ok|fail|unverifiable,
    detail, server_name, server_version}``. Never raises. ``run`` is injectable for
    tests: ``run(argv, cwd, stdin_bytes, timeout) -> (rc, stdout, stderr)``."""
    platform = platform or sys.platform
    base = {"server_name": None, "server_version": None}
    if not entry or not entry.get("command"):
        return {**base, "status": "fail", "detail": "no command registered in mcp.json"}
    argv, unreachable = spawn_target(entry, platform=platform, mnt_root=mnt_root)
    if unreachable:
        return {**base, "status": "unverifiable",
                "detail": f"{unreachable} — verify from the session host: `{entry['command']}`"}
    run = run or default_run
    shown = " ".join(argv)
    try:
        _rc, out, err = run(argv, cwd, (json.dumps(init_request()) + "\n").encode(), timeout)
    except FileNotFoundError:
        return {**base, "status": "fail",
                "detail": f"'{argv[0]}' not found or not executable — cannot spawn it"}
    except subprocess.TimeoutExpired:
        return {**base, "status": "fail",
                "detail": f"initialize handshake timed out after {timeout:.0f}s: `{shown}`"}
    except OSError as exc:
        return {**base, "status": "fail", "detail": f"spawn failed for `{shown}`: {exc}"}
    info = server_info(out)
    if info is None:
        tail = (err or out).decode("utf-8", "replace").strip()[-300:]
        return {**base, "status": "fail",
                "detail": f"no serverInfo from the initialize handshake (`{shown}`)"
                          + (f" — {tail}" if tail else "")}
    name, ver = info.get("name"), info.get("version")
    if name != "clauderizer":
        return {"server_name": name, "server_version": ver, "status": "fail",
                "detail": f"handshake returned serverInfo.name={name!r}, expected 'clauderizer' (`{shown}`)"}
    return {"server_name": name, "server_version": ver, "status": "ok",
            "detail": f"initialize → serverInfo clauderizer {ver}"}
