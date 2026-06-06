"""Load and write ``.clauderizer/config.toml`` — the size/profile dial.

Reading uses stdlib ``tomllib``. Writing uses a tiny emitter (stdlib has no
TOML writer) that covers exactly the shapes we store: tables of strings, bools,
and lists of strings. Keeping the config in TOML avoids YAML's ambiguity for
machine-edited settings; frontmatter inside docs stays YAML per the procedure.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_VERSION = "1"

# Default module/ritual manifests per size. Mirrors the procedure's sizing
# matrix, but as a real dial instead of prose advice.
SIZE_MANIFESTS: dict[str, dict[str, Any]] = {
    "pet": {
        "modules": ["VISION"],
        "rituals": {"preflight": True, "cascade": False, "amendments": False},
        "preflight_checks": ["clean_tree", "tests"],
    },
    "standard": {
        "modules": [
            "VISION",
            "ARCHITECTURE",
            "DECISIONS",
            "INVARIANTS",
            "TESTING",
            "HARDENING",
        ],
        "rituals": {"preflight": True, "cascade": True, "amendments": False},
        "preflight_checks": [
            "branch_base",
            "clean_tree",
            "tests",
            "build",
            "deps_spotcheck",
            "branch_creation",
            "cascade_hygiene",
        ],
    },
    "saas": {
        "modules": [
            "VISION",
            "REQUIREMENTS",
            "ARCHITECTURE",
            "ENGINEERING-PRINCIPLES",
            "DEPLOYMENT",
            "DATASOURCES",
            "SCHEMA",
            "SECURITY",
            "TESTING",
            "HARDENING",
            "INCIDENTS",
            "DECISIONS",
            "INVARIANTS",
            "GLOSSARY",
        ],
        "rituals": {"preflight": True, "cascade": True, "amendments": True},
        "preflight_checks": [
            "branch_base",
            "clean_tree",
            "tests",
            "build",
            "deps_spotcheck",
            "branch_creation",
            "cascade_hygiene",
        ],
    },
}


@dataclass
class Config:
    version: str = CONFIG_VERSION
    size: str = "standard"
    host_profile: str = "generic"
    docs: str = "docs"
    gameplans: str = "docs/gameplans"
    modules: list[str] = field(default_factory=list)
    rituals: dict[str, bool] = field(default_factory=dict)
    preflight_checks: list[str] = field(default_factory=list)
    preflight_advisory: list[str] = field(default_factory=list)
    active_gameplan: str | None = None

    @classmethod
    def for_size(cls, size: str, host_profile: str = "generic") -> "Config":
        manifest = SIZE_MANIFESTS.get(size, SIZE_MANIFESTS["standard"])
        return cls(
            size=size,
            host_profile=host_profile,
            modules=list(manifest["modules"]),
            rituals=dict(manifest["rituals"]),
            preflight_checks=list(manifest["preflight_checks"]),
        )

    def ritual_enabled(self, name: str) -> bool:
        return bool(self.rituals.get(name, False))

    @classmethod
    def load(cls, path: Path) -> "Config":
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        cz = raw.get("clauderizer", {})
        host = raw.get("host", {})
        paths = raw.get("paths", {})
        modules = raw.get("modules", {})
        rituals = raw.get("rituals", {})
        active = raw.get("active_gameplan", {})
        return cls(
            version=str(cz.get("version", CONFIG_VERSION)),
            size=str(cz.get("size", "standard")),
            host_profile=str(host.get("profile", "generic")),
            docs=str(paths.get("docs", "docs")),
            gameplans=str(paths.get("gameplans", "docs/gameplans")),
            modules=list(modules.get("enabled", [])),
            rituals={k: bool(v) for k, v in rituals.items()},
            preflight_checks=list(cz.get("preflight_checks", [])),
            preflight_advisory=list(cz.get("preflight_advisory", [])),
            active_gameplan=(active.get("id") or None),
        )

    def to_toml(self) -> str:
        lines = [
            "[clauderizer]",
            f'version = "{self.version}"',
            f'size = "{self.size}"',
            _toml_kv("preflight_checks", self.preflight_checks),
            _toml_kv("preflight_advisory", self.preflight_advisory),
            "",
            "[host]",
            f'profile = "{self.host_profile}"',
            "",
            "[paths]",
            f'docs = "{self.docs}"',
            f'gameplans = "{self.gameplans}"',
            "",
            "[modules]",
            _toml_kv("enabled", self.modules),
            "",
            "[rituals]",
        ]
        for k, v in self.rituals.items():
            lines.append(f"{k} = {'true' if v else 'false'}")
        lines += ["", "[active_gameplan]", f'id = "{self.active_gameplan or ""}"', ""]
        return "\n".join(lines)


def _toml_kv(key: str, value: Any) -> str:
    if isinstance(value, list):
        inner = ", ".join(f'"{v}"' for v in value)
        return f"{key} = [{inner}]"
    if isinstance(value, bool):
        return f"{key} = {'true' if value else 'false'}"
    return f'{key} = "{value}"'


def merge_missing(existing: Config, defaults: Config) -> Config:
    """Return ``existing`` with any empty fields filled from ``defaults``.

    Used by ``init`` re-runs so user edits are never overwritten — only gaps are
    filled in.
    """
    return Config(
        version=existing.version or defaults.version,
        size=existing.size or defaults.size,
        host_profile=existing.host_profile or defaults.host_profile,
        docs=existing.docs or defaults.docs,
        gameplans=existing.gameplans or defaults.gameplans,
        modules=existing.modules or defaults.modules,
        rituals=existing.rituals or defaults.rituals,
        preflight_checks=existing.preflight_checks or defaults.preflight_checks,
        preflight_advisory=existing.preflight_advisory or defaults.preflight_advisory,
        active_gameplan=existing.active_gameplan or defaults.active_gameplan,
    )
