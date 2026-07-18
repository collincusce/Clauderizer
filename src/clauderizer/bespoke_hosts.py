"""Framework for **bespoke auto-write MCP hosts** (D-056).

A *bespoke auto-write host* is one whose MCP servers load ONLY from a per-user config
the app owns (and often regenerates) — never this repo's project config, and with no
hook surface — so clauderizer must AUTO-WRITE that per-user config. This is the single
sanctioned exception to "global config → guide-only" (D-031), justified by UX (D-053),
kept narrow by three mitigations that live HERE so every such host inherits them:

- **detected-only** — write only when the app's config dir already exists;
- **non-destructive + atomic + idempotent** — merge only the clauderizer server, via
  temp-write + ``os.replace``, skipping the write when already current;
- **self-healing** — re-applied on every write-permitted entry point (the app may
  regenerate its config), never from a hook (INVARIANT-06) or an MCP read op (L-03).

A new host is a :class:`BespokeHost` subclass supplying only the VARIABLE parts
(config discovery, topology-aware command composition, setup guide, optional
"can't-serve-this-repo" guidance) + a registry entry — the detect/merge/self-heal
lifecycle and the ``mcp_probe`` handshake verification are inherited, not re-written
(kimi-desktop is the first implementation — ``kimidesktop.KimiDesktopHost``).

Everything is pure/injectable (``home``/``platform``/``environ``/``exists``/``which``)
so tests exercise it against a temp home, never a real per-user config (L-29).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Callable

from .markdown.writer import refuse_if_symlink

# From inside WSL, a Windows desktop host's per-user config is under
# ``/mnt/<drive>/Users/<user>/...`` — generic to any WSL vantage, not host-specific.
WSL_USERS_DIR = Path("/mnt/c/Users")

# The MCP server name clauderizer registers under a host's servers key. Constant across
# hosts (they all serve the same server); the JSON servers KEY varies (BespokeHost.servers_key).
SERVER_NAME = "clauderizer"


def _atomic_write_json(path: Path, data: dict) -> None:
    refuse_if_symlink(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)                             # atomic on POSIX and Windows


def merge_entry(cfg: Path, entry: dict, *, servers_key: str = "mcpServers",
                server_name: str = SERVER_NAME) -> tuple[Path, bool]:
    """Non-destructively add/replace only the clauderizer server in ``cfg``, preserving
    every other server and top-level key. Atomic + idempotent: returns ``(cfg, changed)``
    and skips the write when already current."""
    data: dict = {}
    if cfg.exists():
        try:
            loaded = json.loads(cfg.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except json.JSONDecodeError:
            data = {}
    servers = data.get(servers_key)
    if not isinstance(servers, dict):
        servers = data[servers_key] = {}
    if servers.get(server_name) == entry:
        return cfg, False                             # already current — no write
    servers[server_name] = entry
    _atomic_write_json(cfg, data)
    return cfg, True


def remove_entry(cfg: Path, *, servers_key: str = "mcpServers",
                 server_name: str = SERVER_NAME) -> bool:
    """Uninstall: remove ONLY the clauderizer server from ``cfg``. True if it removed."""
    if not cfg.exists():
        return False
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get(servers_key)
    if not isinstance(servers, dict) or server_name not in servers:
        return False
    del servers[server_name]
    _atomic_write_json(cfg, data)
    return True


class BespokeHost:
    """Base for an auto-write MCP host. Subclasses set ``id``/``opt_out_env`` and
    override the variable-part methods; the base supplies the shared lifecycle."""

    id: str = ""
    opt_out_env: str = ""
    servers_key: str = "mcpServers"
    server_name: str = SERVER_NAME

    # --- variable parts: subclasses override -------------------------------------
    def candidate_configs(self, *, home: Path, platform: str, environ: dict,
                          in_wsl: bool, users_dir: Path) -> list[Path]:
        """Ordered candidate per-user config paths (pure path construction)."""
        raise NotImplementedError

    def compose_entry(self, cfg: Path, *, in_wsl: bool, platform: str | None,
                      home: Path | None, users_dir: Path,
                      exists: Callable[[Path], bool] | None,
                      which: Callable[[str], str | None]) -> tuple[dict | None, list[str]]:
        """The ``{command, args}`` server entry (or ``None`` = unregistrable) + warnings,
        composed host-topology-aware."""
        raise NotImplementedError

    def setup_guide(self) -> str:
        """The fallback/recovery guide written to ``.clauderizer/<id>-mcp-setup.md``."""
        raise NotImplementedError

    def unservable_reason(self, cfg: Path, *, in_wsl: bool, users_dir: Path) -> str | None:
        """When the app is detected but can't actually serve THIS repo (e.g. a WSL repo
        under a Windows desktop's UNC-cwd spawn limit, D-054), the guidance to surface
        instead of pretending the registration serves it. Default: always servable."""
        return None

    # --- shared lifecycle: inherited ---------------------------------------------
    def detect_config(self, *, home: Path | None = None, platform: str | None = None,
                      environ: dict | None = None, in_wsl: bool | None = None,
                      users_dir: Path | None = None) -> Path | None:
        """The per-user config if the app is installed (its config dir already exists),
        else ``None`` — detected-only, never creating anything. ``None`` when the host's
        opt-out env var is set."""
        home = home or Path.home()
        platform = platform or sys.platform
        environ = environ if environ is not None else os.environ
        users_dir = users_dir or WSL_USERS_DIR
        if self.opt_out_env and environ.get(self.opt_out_env):
            return None
        if in_wsl is None:
            in_wsl = bool(environ.get("WSL_DISTRO_NAME"))
        for cfg in self.candidate_configs(home=home, platform=platform, environ=environ,
                                          in_wsl=in_wsl, users_dir=users_dir):
            if cfg.parent.is_dir():
                return cfg
        return None

    def wire(self, *, home: Path | None = None, platform: str | None = None,
             environ: dict | None = None, in_wsl: bool | None = None,
             users_dir: Path | None = None, exists: Callable[[Path], bool] | None = None,
             which: Callable[[str], str | None] = shutil.which) -> dict:
        """Detect + compose + non-destructive merge → a status dict ``{status, path,
        entry, changed, unservable, warnings}``. ``status`` is ``not_detected`` |
        ``wired`` | ``unregistrable`` (detected but no launchable command) | ``failed``
        (unwritable). Never raises on a detected-but-unwritable config."""
        environ = environ if environ is not None else os.environ
        users_dir = users_dir or WSL_USERS_DIR
        if in_wsl is None:
            in_wsl = bool(environ.get("WSL_DISTRO_NAME"))
        cfg = self.detect_config(home=home, platform=platform, environ=environ,
                                 in_wsl=in_wsl, users_dir=users_dir)
        if cfg is None:
            return {"status": "not_detected", "path": None, "entry": None, "warnings": []}
        unservable = self.unservable_reason(cfg, in_wsl=in_wsl, users_dir=users_dir)
        entry, warnings = self.compose_entry(cfg, in_wsl=in_wsl, platform=platform,
                                             home=home, users_dir=users_dir,
                                             exists=exists, which=which)
        if entry is None:
            return {"status": "unregistrable", "path": cfg, "entry": None,
                    "unservable": unservable, "warnings": warnings}
        try:
            _, changed = merge_entry(cfg, entry, servers_key=self.servers_key,
                                     server_name=self.server_name)
        except OSError as exc:
            return {"status": "failed", "path": cfg, "entry": entry, "unservable": unservable,
                    "warnings": warnings + [f"could not write {cfg}: {exc}"]}
        return {"status": "wired", "path": cfg, "entry": entry, "changed": changed,
                "unservable": unservable, "warnings": warnings}

    def self_heal(self, **kw) -> dict:
        """Best-effort re-apply for the write-permitted CLI entry points (init/doctor/
        status) — the app may regenerate its config. Idempotent (a no-op when current);
        never raises; honors the opt-out. Not from a hook (INVARIANT-06) or read op (L-03)."""
        try:
            return self.wire(**kw)
        except Exception as exc:                      # a self-heal must never break its caller
            return {"status": "failed", "path": None, "entry": None, "warnings": [str(exc)]}

    def remove_registration(self, cfg: Path) -> bool:
        """Uninstall: remove only the clauderizer server from this host's ``cfg``."""
        return remove_entry(cfg, servers_key=self.servers_key, server_name=self.server_name)


# The registry: init/doctor/status/uninstall iterate this. A new host registers itself
# (see kimidesktop.KimiDesktopHost) — a plain dict, no plugin/entry-point machinery.
BESPOKE_HOSTS: dict[str, BespokeHost] = {}


def register(host: BespokeHost) -> BespokeHost:
    """Register a bespoke host in the global registry (idempotent by id). Returns it so
    a module can ``_HOST = register(KimiDesktopHost())`` in one line."""
    BESPOKE_HOSTS[host.id] = host
    return host


def all_hosts() -> dict[str, BespokeHost]:
    """The registered bespoke hosts. Imports the host implementation modules on first
    use so their registration side-effects run regardless of who imported what — a
    top-level import here would cycle (kimidesktop imports this module), and relying on
    some other caller to have imported the host first is a latent bug (a real
    ``clauderize doctor`` does not import kimidesktop otherwise). Entry points
    (init/doctor/status/uninstall) MUST iterate via this accessor, not the raw dict.
    Add a new host's module to the import list below."""
    from . import kimidesktop  # noqa: F401 — importing registers KimiDesktopHost
    return BESPOKE_HOSTS
