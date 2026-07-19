"""The monotonic memory revision — the near-free change signal (O-03, §6.4).

``.clauderizer/revision.json`` is CONTRACT SURFACE, not a private cache: it is
the one engine artifact external clients are blessed to read directly, because
its whole point is that polling it must not cost a process spawn. Shape:

    {"schema_version": "1.0", "epoch": "<hex>", "revision": N}

``revision`` increments on every engine write that changes memory bytes
(markdown mutations, cascade reports, handoffs, the focus flip). ``epoch`` is
minted when the file is (re)created, so a deleted/reset file never replays a
counter value a client has already seen: pollers treat ``(epoch, revision)``
as the change key, both opaque. The file is written atomically (temp +
``os.replace``) so readers see old-or-new, never torn.

Bumps happen inside the H-05 advisory write lock for all locked mutation
paths; the rare unlocked writers (init scaffolding) may lose an increment
under concurrency, which is harmless — the counter is a change signal, not an
audit log.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from pathlib import Path

from .contract import CONTRACT_SCHEMA_VERSION

FILENAME = "revision.json"


def revision_file(clauderizer_dir: Path) -> Path:
    return clauderizer_dir / FILENAME


def read(clauderizer_dir: Path) -> dict | None:
    """The current ``{schema_version, epoch, revision}``, or ``None`` when absent
    or unreadable (a torn/corrupt file reads as absent, never raises)."""
    try:
        data = json.loads(revision_file(clauderizer_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or "revision" not in data:
        return None
    return data


def bump(clauderizer_dir: Path) -> dict | None:
    """Increment the counter (creating the file, and a fresh epoch, if needed).

    Returns the new record, or ``None`` when ``clauderizer_dir`` does not exist —
    a write landing outside any clauderized repo has no revision to bump.
    """
    if not clauderizer_dir.is_dir():
        return None
    current = read(clauderizer_dir)
    if current is None:
        current = {"epoch": secrets.token_hex(8), "revision": 0}
    record = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "epoch": current["epoch"],
        "revision": int(current["revision"]) + 1,
    }
    payload = json.dumps(record) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=".revision-", dir=str(clauderizer_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, revision_file(clauderizer_dir))
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return None
    return record


def bump_for(written_path: Path) -> dict | None:
    """Bump the revision of whichever clauderized repo contains ``written_path``.

    Walks up from the written file to the nearest ``.clauderizer`` directory;
    a path outside any clauderized repo is a silent no-op. This is the hook
    the byte-writers call — they know the file they touched, not the repo.
    """
    try:
        p = written_path.resolve()
    except OSError:
        p = written_path
    # Writes landing inside .clauderizer/ itself (caches, telemetry, this very
    # file) never bump — the counter tracks memory, and bumping for revision.json
    # would recurse. Deliberate .clauderizer-resident signals (the focus flip)
    # call bump() directly instead of routing through here.
    if any(part == ".clauderizer" for part in p.parts):
        return None
    for parent in p.parents:
        cz = parent / ".clauderizer"
        if cz.is_dir():
            return bump(cz)
    return None
