"""``clauderize`` — the human/agent command line.

Subcommands:
    init      drop Clauderizer into the current repo (idempotent)
    status    print the current gameplan digest
    reindex   rebuild the disposable graph cache from markdown
    doctor    verify the install and report drift
    mcp       launch the MCP server (stdio)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

from . import PROCEDURE_VERSION, __version__
from .config import Config
from .graph import index
from .paths import find_repo_root, resolve
from .rituals import status_bundle
from .scaffold.init import init as run_init
from .tools_list import TOOL_NAMES


def _load(root: Path | None = None):
    paths = resolve(find_repo_root(root or Path.cwd()))
    if not paths.config_file.exists():
        return paths, None
    return paths, Config.load(paths.config_file)


def cmd_init(args: argparse.Namespace) -> int:
    run_cmd = args.run_cmd.split() if args.run_cmd else None
    report = run_init(
        Path(args.path).resolve(),
        size=args.size,
        profile=args.profile,
        gameplan=args.gameplan,
        run_cmd=run_cmd,
        workflow=args.workflow,
    )
    print(f"Clauderized {report.repo}")
    print(f"  size={report.size}  host profile={report.host_profile}")
    n_changed = len(report.changed)
    print(f"  {n_changed} file(s) written/updated, {len(report.actions) - n_changed} kept as-is")
    if args.verbose:
        for a in report.actions:
            print(f"    {a}")
    print("\nNext: open a Claude Code session here — the SessionStart hook will show status.")
    print("Or run `clauderize status`.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    bundle = status_bundle.compute(paths, config)
    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(status_bundle.render_digest(bundle, tools=TOOL_NAMES))
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("Not a clauderized repo. Run `clauderize init`.")
        return 1
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)
    print(f"Reindexed {len(graph.entities)} entities -> {paths.index_file}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    paths, config = _load()
    if config is None:
        print("✗ Not a clauderized repo (no .clauderizer/config.toml). Run `clauderize init`.")
        return 1
    ok = True

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ok
        mark = "✓" if condition else "✗"
        print(f"{mark} {label}" + (f" — {detail}" if detail and not condition else ""))
        if not condition:
            ok = False

    check("config.toml present", paths.config_file.exists())
    check("procedure shipped", paths.procedure_file.exists())
    check("CLAUDE.md stanza", _has_marker(paths.claude_md, "clauderizer"))
    check(".mcp.json registers clauderizer", _mcp_registered(paths.mcp_json))
    # Fidelity: registration present is not enough — the command must be launchable.
    mcp_ok, mcp_detail = _command_runnable(_mcp_command(paths.mcp_json))
    check("MCP server command runnable", mcp_ok, mcp_detail)
    settings = paths.root / ".claude" / "settings.json"
    check("SessionStart hook registered", _hook_registered(settings))
    hook_ok, hook_detail = _command_runnable(_hook_command(settings))
    check("SessionStart hook command runnable", hook_ok, hook_detail)
    check("index cache present", paths.index_file.exists())
    # A lock that doesn't parse is silently ignored by load_for_repo — surface it.
    lock_err = _lock_parse_error(paths.profile_lock)
    check("profile.lock.toml parses", lock_err is None, lock_err or "")
    # procedure version drift (MAJOR)
    drift = _procedure_drift(paths.procedure_file)
    check("procedure version compatible", drift is None, drift or "")
    if config.active_gameplan:
        gp = paths.gameplan_dir(config.active_gameplan) / "GAMEPLAN.md"
        check(f"active gameplan {config.active_gameplan} on disk", gp.exists())
    print("\nOK" if ok else "\nDrift detected — re-run `clauderize init` to repair.")
    return 0 if ok else 2


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main

    return mcp_main()


# --- doctor helpers -----------------------------------------------------------


def _has_marker(path: Path, name: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return f"<!-- {name}:start -->" in text


def _mcp_registered(mcp_json: Path) -> bool:
    if not mcp_json.exists():
        return False
    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return "clauderizer" in data.get("mcpServers", {})


def _hook_registered(settings: Path) -> bool:
    if not settings.exists():
        return False
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    for group in data.get("hooks", {}).get("SessionStart", []):
        for h in group.get("hooks", []):
            if "clauderizer-hook" in h.get("command", ""):
                return True
    return False


def _mcp_command(mcp_json: Path) -> list[str] | None:
    if not mcp_json.exists():
        return None
    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    entry = data.get("mcpServers", {}).get("clauderizer")
    if not entry:
        return None
    return [entry.get("command", ""), *entry.get("args", [])]


def _hook_command(settings: Path) -> list[str] | None:
    if not settings.exists():
        return None
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for group in data.get("hooks", {}).get("SessionStart", []):
        for h in group.get("hooks", []):
            cmd = h.get("command", "")
            if "clauderizer-hook" in cmd:
                return cmd.split()
    return None


def _command_runnable(argv: list[str] | None) -> tuple[bool, str]:
    """Can the configured launch command actually be executed on this machine?

    Guards against a green health check on a setup that can't launch (e.g. a
    ``.mcp.json`` pointing at ``uvx`` that isn't installed, or a dev path that
    doesn't exist) — a check that's green while the server can't start is worse
    than no check.
    """
    if not argv or not argv[0]:
        return False, "no clauderizer command registered"
    exe = argv[0]
    if shutil.which(exe):
        return True, exe
    p = Path(exe)
    if p.is_file() and os.access(p, os.X_OK):
        return True, str(p)
    return False, f"'{exe}' not found on PATH or not executable"


def _lock_parse_error(lock_path: Path) -> str | None:
    """Return a description of why the profile lock can't parse, else None."""
    if not lock_path.exists():
        return None  # no lock is fine — packaged defaults apply
    import tomllib

    try:
        with lock_path.open("rb") as fh:
            tomllib.load(fh)
    except tomllib.TOMLDecodeError as e:
        return f"invalid TOML ({e}) — overrides are being ignored; fix or delete it"
    except OSError as e:
        return str(e)
    return None


def _procedure_drift(procedure_file: Path) -> str | None:
    if not procedure_file.exists():
        return "procedure file missing"
    m = re.search(r"Procedure version\**:?\s*([0-9]+)\.([0-9]+)\.([0-9]+)",
                  procedure_file.read_text(encoding="utf-8"))
    if not m:
        return None
    host_major = int(m.group(1))
    engine_major = int(PROCEDURE_VERSION.split(".")[0])
    if host_major != engine_major:
        return f"host procedure v{m.group(0)} vs engine v{PROCEDURE_VERSION} (MAJOR mismatch)"
    return None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="clauderize", description="Drop-in working memory for AI agents.")
    p.add_argument("--version", action="version", version=f"clauderizer {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("init", help="drop Clauderizer into this repo")
    pi.add_argument("path", nargs="?", default=".", help="repo path (default: cwd)")
    pi.add_argument("--size", choices=["pet", "standard", "saas"], default="standard")
    pi.add_argument("--profile", default="auto", help="host language profile (default: auto-detect)")
    pi.add_argument("--gameplan", default=None, help="also create a first gameplan with this name")
    pi.add_argument("--run-cmd", default=None,
                    help="how the repo invokes the engine (default: 'uvx --from clauderizer')")
    pi.add_argument("--workflow", choices=["code", "docs", "audit"], default="code",
                    help="docs/audit make clean_tree (and test) checks advisory, not fatal")
    pi.add_argument("-v", "--verbose", action="store_true")
    pi.set_defaults(func=cmd_init)

    ps = sub.add_parser("status", help="print current gameplan status")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(func=cmd_status)

    pr = sub.add_parser("reindex", help="rebuild the graph cache from markdown")
    pr.set_defaults(func=cmd_reindex)

    pd = sub.add_parser("doctor", help="verify the install and report drift")
    pd.set_defaults(func=cmd_doctor)

    pm = sub.add_parser("mcp", help="launch the MCP server (stdio)")
    pm.set_defaults(func=cmd_mcp)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
