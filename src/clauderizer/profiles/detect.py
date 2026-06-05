"""Load profiles and auto-detect the host project's language."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_PROFILES_DIR = Path(__file__).parent


@dataclass
class Profile:
    name: str
    detect_files: list[str] = field(default_factory=list)
    weight: int = 0
    commands: dict[str, str] = field(default_factory=dict)
    baseline_test_regex: str = ""

    @classmethod
    def from_toml(cls, path: Path) -> "Profile":
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        detect = raw.get("detect", {})
        return cls(
            name=str(raw.get("name", path.stem)),
            detect_files=list(detect.get("files", [])),
            weight=int(detect.get("weight", 0)),
            commands={k: str(v) for k, v in raw.get("commands", {}).items()},
            baseline_test_regex=str(raw.get("preflight", {}).get("baseline_test_regex", "")),
        )

    def command(self, kind: str) -> str:
        return self.commands.get(kind, "").strip()

    def to_lock_toml(self) -> str:
        lines = [f'profile = "{self.name}"', "", "[commands]"]
        for kind in ("test", "build", "lint", "typecheck"):
            lines.append(f'{kind} = "{self.command(kind)}"')
        lines += ["", "[preflight]", f'baseline_test_regex = "{self.baseline_test_regex}"', ""]
        return "\n".join(lines)


def load_all() -> dict[str, Profile]:
    out: dict[str, Profile] = {}
    for p in sorted(_PROFILES_DIR.glob("*.toml")):
        prof = Profile.from_toml(p)
        out[prof.name] = prof
    return out


def load(name: str) -> Profile:
    profiles = load_all()
    return profiles.get(name) or profiles["generic"]


def load_for_repo(name: str, lock_path: Path | None = None) -> Profile:
    """Load the packaged profile, then overlay a project-local ``profile.lock.toml``.

    The lock file (written by ``init``) is the project's authoritative source for
    commands, so a team can pin per-project ``test``/``build``/``lint``/``typecheck``
    by editing it. Previously the lock was write-only and overrides silently did
    nothing. Only non-empty values override the packaged defaults.
    """
    base = load(name)
    if lock_path is None or not lock_path.exists():
        return base
    try:
        with lock_path.open("rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return base
    merged = dict(base.commands)
    merged.update(
        {k: str(v) for k, v in raw.get("commands", {}).items() if str(v).strip()}
    )
    regex = str(raw.get("preflight", {}).get("baseline_test_regex", "")) or base.baseline_test_regex
    return Profile(
        name=str(raw.get("profile", base.name)),
        detect_files=base.detect_files,
        weight=base.weight,
        commands=merged,
        baseline_test_regex=regex,
    )


def detect(repo_root: Path) -> tuple[Profile, list[str]]:
    """Return ``(best_profile, alternatives)`` for a host repo.

    Scores each profile by the count of its marker files present in the repo
    root, scaled by weight. Ties and zero-score fall back to ``generic``.
    """
    profiles = load_all()
    scored: list[tuple[int, Profile]] = []
    for prof in profiles.values():
        hits = sum(1 for f in prof.detect_files if (repo_root / f).exists())
        score = hits * prof.weight
        if score > 0:
            scored.append((score, prof))
    scored.sort(key=lambda t: t[0], reverse=True)
    if not scored:
        return profiles["generic"], []
    best = scored[0][1]
    alternatives = [p.name for _, p in scored[1:]]
    return best, alternatives
