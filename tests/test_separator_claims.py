"""A `/` inside an asserted string literal is a platform claim, or it is not (L-51).

1.14.2 shipped with three Windows cells red on `assert "uv/archive-v0" in
m["serving_path"]`. `serving_path` is `str(Path)` — Windows renders it with
backslashes, so the literal could never match. L-51 already carried the rule
("assert the FILE, not the slash") and had already been *surfaced* to the
session that wrote the line. Surfacing was not enough. This module is the
machine check at the point of the mistake.

WHAT THIS CATCHES, stated honestly rather than implied. Whether a string is a
native-separator render is not statically decidable, so this does not try to
decide it. It flags the two shapes where the source itself supplies the
evidence:

  Rule A — the compared-against value ANNOUNCES itself as a path: its trailing
    identifier is `path`/`dir`/`file`/`root`/`home` (`m["serving_path"]`), or
    the expression is a bare `str(...)` coercion. A value that declares itself
    a path and is matched against a literal containing `/` is a platform claim.

  Rule B — the literal is a FRAGMENT of a real absolute-path literal in the
    same module. `"uv/archive-v0"` is a slice of that file's `UVX_LIKE`
    fixture, which is how the *second* red line — `assert "uv/archive-v0" in
    digest` — is caught even though `digest` announces nothing.

WHAT IT DOES NOT CATCH: a path-valued expression that neither declares itself
nor traces to a path literal (`assert "a/b" in some_opaque_string`). No
mechanical check distinguishes that from prose, and pretending otherwise is
the false green this line of work exists to end. The inventory ratchet below
is the backstop: it cannot classify a new site, but it can refuse to let one
appear unclassified.

THE ESCAPE HATCH is the fix, not a suppression: assert the separator-agnostic
token (`"archive-v0"`), or normalize the value with `.as_posix()` — Rule A
exempts `.as_posix()` calls by design.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("src", "tests", "scripts")
BASELINE = Path(__file__).parent / "fixtures" / "separator_claims_baseline.json"

#: A trailing identifier that declares its value to be a filesystem path.
_DECLARES_A_PATH = re.compile(r"(^|_)(path|paths|dir|dirs|file|files|root|home)$", re.I)

#: A string literal that looks like a real absolute filesystem path: rooted,
#: no whitespace, and deep enough that prose cannot reach it by accident.
_ABSOLUTE_PATH_LITERAL = re.compile(r"^(/|[A-Za-z]:[\\/])\S*$")
_MIN_PATH_SEGMENTS = 3


# --- the scanner ---------------------------------------------------------------


def _py_files() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if base.exists():
            out += [p for p in sorted(base.rglob("*.py")) if "__pycache__" not in p.parts]
    return out


def _tail_identifier(node: ast.expr) -> str | None:
    """The name a value goes by at its point of use, or None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
        return _tail_identifier(node.value)  # `offenders[0]` -> "offenders"
    return None


def _rule_a(right: ast.expr) -> str | None:
    """The compared-against value announces itself as a path."""
    if isinstance(right, ast.Call):
        func = right.func
        if isinstance(func, ast.Attribute) and func.attr == "as_posix":
            return None  # explicitly normalized — the sanctioned fix
        if isinstance(func, ast.Name) and func.id == "str":
            return "right-hand side is a bare `str(...)` coercion"
        return None
    name = _tail_identifier(right)
    if name and _DECLARES_A_PATH.search(name):
        return f"right-hand side `{name}` declares itself a filesystem path"
    return None


def _path_literals(tree: ast.AST) -> set[str]:
    """Every string constant in the module that looks like a real absolute path."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if (_ABSOLUTE_PATH_LITERAL.match(value)
                    and value.count("/") + value.count("\\") >= _MIN_PATH_SEGMENTS):
                found.add(value)
    return found


def _rule_b(literal: str, path_literals: set[str]) -> str | None:
    """The literal is a fragment of a real path literal in the same module."""
    if " " in literal:
        return None
    for candidate in sorted(path_literals):
        if literal != candidate and literal in candidate:
            return f"literal is a fragment of the path literal {candidate!r}"
    return None


def scan_source(source: str, rel: str) -> list[dict]:
    """Every `assert <str literal containing "/"> in|not in|== <expr>` in a module.

    AST, not grep: the pattern `assert "…/…" in …` that scoped this work found
    24 sites and this finds 40. Grep cannot see single-quoted literals, a
    second literal on one line, the arms of an `or` chain, or a literal whose
    line differs from the `assert` keyword's.
    """
    tree = ast.parse(source)
    path_literals = _path_literals(tree)
    rows: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        for cmp in (n for n in ast.walk(node.test) if isinstance(n, ast.Compare)):
            for op, right in zip(cmp.ops, cmp.comparators):
                if not isinstance(op, (ast.In, ast.NotIn, ast.Eq)):
                    continue
                left = cmp.left
                if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
                    continue
                if "/" not in left.value:
                    continue
                rows.append({
                    "file": rel,
                    "line": cmp.lineno,
                    "literal": left.value,
                    "rhs": ast.unparse(right),
                    "flag": _rule_a(right) or _rule_b(left.value, path_literals),
                })
    return rows


def scan_tree() -> list[dict]:
    rows: list[dict] = []
    for f in _py_files():
        try:
            rows += scan_source(f.read_text(encoding="utf-8"), f.relative_to(ROOT).as_posix())
        except (OSError, SyntaxError):
            continue
    return rows


def site_key(row: dict) -> str:
    """Line numbers move; a file and a literal do not."""
    return f"{row['file']}::{row['literal']}"


# --- the class is rejected ------------------------------------------------------


def test_no_assertion_makes_an_unnormalized_platform_claim():
    """The check itself. Zero, and it stays zero."""
    flagged = [r for r in scan_tree() if r["flag"]]
    assert not flagged, "separator-shaped platform claim(s):\n" + "\n".join(
        f"  {r['file']}:{r['line']}  {r['literal']!r} in {r['rhs']}\n"
        f"      {r['flag']}\n"
        f"      fix: assert the separator-agnostic token, or normalize with .as_posix()"
        for r in flagged)


#: The exact source that shipped three Windows cells red in 1.14.2, reconstructed
#: from the blob at f9f8343^ — BOTH assertions the fix commit had to change.
REGRESSION_1_14_2 = '''
UVX_LIKE = "/home/u/.cache/uv/archive-v0/FCYnO1Z/lib/python3.12/site-packages/clauderizer/__init__.py"


def test_uvx_serving_path_is_reported():
    m = engine_identity.mismatch(UVX_LIKE)
    assert "uv/archive-v0" in m["serving_path"]
    assert "uv/archive-v0" in digest
'''

#: The same file after fix commit f9f8343 — what the check must call clean.
FIXED_1_14_2 = '''
UVX_LIKE = "/home/u/.cache/uv/archive-v0/FCYnO1Z/lib/python3.12/site-packages/clauderizer/__init__.py"


def test_uvx_serving_path_is_reported():
    m = engine_identity.mismatch(UVX_LIKE)
    assert "archive-v0" in m["serving_path"], "separator-agnostic (L-51)"
    assert "archive-v0" in digest
'''


def test_the_check_fires_on_the_line_that_shipped_1_14_2_red():
    """If it would not have caught that, it is the wrong check.

    Both red lines, by different rules: `m["serving_path"]` declares itself
    (Rule A); `digest` does not, and is caught only because the literal is a
    slice of the module's own UVX_LIKE fixture (Rule B).
    """
    rows = scan_source(REGRESSION_1_14_2, "<1.14.2>")
    assert len(rows) == 2, f"expected both red assertions, saw {rows}"
    assert all(r["flag"] for r in rows), f"missed: {[r for r in rows if not r['flag']]}"
    by_rhs = {r["rhs"]: r["flag"] for r in rows}
    assert "declares itself" in by_rhs["m['serving_path']"]
    assert "fragment of the path literal" in by_rhs["digest"]


def test_the_shipped_fix_is_clean():
    """The escape hatch has to actually work, or the check is unactionable:
    the real f9f8343 fix leaves nothing for the scanner to see."""
    assert scan_source(FIXED_1_14_2, "<fixed>") == []


def test_as_posix_is_an_accepted_normalization():
    """The other sanctioned fix: normalize the value instead of the literal."""
    normalized = 'def t():\n    assert "docs/VISION.md" in target_path.as_posix()\n'
    rows = scan_source(normalized, "<normalized>")
    assert len(rows) == 1 and rows[0]["flag"] is None


# --- the false-positive floor ---------------------------------------------------

#: Every shape in this repo where a `/` inside an asserted literal is NOT a
#: separator, or is a separator the producer guarantees on every OS. If the
#: check flags any of these it earns its way into the ignore list.
MESSAGE_ASSERTION_SHAPES = [
    ('assert "Deliverables: 1/2 shipped." in digest', "a fraction"),
    ('assert "(handoff n/a: gameplan complete)." in digest', "prose 'n/a'"),
    ('assert "already obsolete/promoted" in c["summary"]', "prose alternation"),
    ('assert "exit /b 0" in text', "a cmd.exe flag"),
    (r'''assert 'cd /d "C:\\repo" 2>nul' in text''',
     "a cmd.exe flag beside a backslashed path"),
    ('assert "/clauderizer-dream right now" in out', "a slash command"),
    ('assert "</text>" not in idx', "an XML closing tag"),
    ('assert ".clauderizer/index.json" in gi', "an authored .gitignore line"),
    ('assert ".cursor/mcp.json" in out', "an authored HostEmitter constant"),
    ('assert "docs/VISION.md" in onboard.unseeded_docs(paths)', "an f-string literal slash"),
    ('assert "docs/studio.md" in got', "a producer that calls .as_posix()"),
]


@pytest.mark.parametrize("source,why", MESSAGE_ASSERTION_SHAPES)
def test_message_assertions_are_not_flagged(source, why):
    rows = scan_source(f"def t():\n    {source}\n", "<shape>")
    assert len(rows) == 1, f"scanner failed to parse the {why} shape: {rows}"
    assert rows[0]["flag"] is None, f"false positive on {why}: {rows[0]['flag']}"


def test_the_floor_is_measured_against_the_real_corpus_not_only_samples():
    """The samples above are illustrative; this is the actual claim. Every one
    of the repo's real separator-shaped assertions is classified `message` in
    the baseline, and the check flags none of them."""
    recorded = _classified()
    rows = scan_tree()
    assert rows, "scanner found nothing — it has stopped working"
    for row in rows:
        entry = recorded.get(site_key(row))
        if entry and entry["class"] == "message":
            assert row["flag"] is None, (
                f"false positive on a site triaged as a message assertion: "
                f"{row['file']}:{row['line']} {row['literal']!r} — {row['flag']}")


# --- the inventory ratchet ------------------------------------------------------


def _baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _classified() -> dict[str, dict]:
    return _baseline()["classified"]


def _actual_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in scan_tree():
        counts[site_key(row)] = counts.get(site_key(row), 0) + 1
    return counts


def test_no_new_separator_shaped_assertion_appears_untriaged():
    """The class, not the instances.

    A new `assert "a/b" in x` has to be a DECISION: classify it in the
    baseline as a platform claim (and then fix it) or as a message assertion
    (and say why the slash holds on Windows). What it can no longer be is
    unnoticed — which is exactly what 1.14.2 was.
    """
    recorded, actual = _classified(), _actual_counts()
    new = sorted(k for k in actual if k not in recorded)
    grown = sorted(f"{k} ({actual[k]} > {recorded[k]['count']})"
                   for k in actual if k in recorded and actual[k] > recorded[k]["count"])
    assert not new, (
        f"untriaged separator-shaped assertion(s): {new}. Classify each in "
        f"{BASELINE.name} as 'platform' (the right-hand side is a real filesystem "
        f"path — then fix it, per L-51: assert the FILE, not the slash) or "
        f"'message' (a rendered string — say why the slash holds on Windows).")
    assert not grown, f"more occurrences than triaged: {grown}"


def test_the_inventory_ratchet_tightens_when_a_site_goes_away():
    """The other direction, which is what makes it a ratchet rather than a cap:
    removing a site must lower the baseline, or the slack silently becomes room
    for the next unclassified one to hide in."""
    recorded, actual = _classified(), _actual_counts()
    gone = sorted(k for k in recorded if k not in actual)
    shrunk = sorted(f"{k} ({actual[k]} < {recorded[k]['count']})"
                    for k in recorded if k in actual and actual[k] < recorded[k]["count"])
    assert not gone, f"triaged sites that no longer exist — remove them: {gone}"
    assert not shrunk, f"fewer occurrences than recorded — lower the baseline: {shrunk}"


def test_every_triaged_site_carries_a_written_classification():
    """A count is not a triage."""
    bad = []
    for key, entry in _classified().items():
        if entry.get("class") not in ("message", "platform"):
            bad.append(f"{key}: class={entry.get('class')!r}")
        elif len((entry.get("why") or "").strip()) < 20:
            bad.append(f"{key}: why= too thin to be a classification")
    assert not bad, "\n".join(bad)


def test_anything_triaged_as_a_platform_claim_is_actually_flagged():
    """The baseline cannot disagree with the checker. A site recorded as a
    platform claim that the checker calls clean means one of them is wrong."""
    recorded = _classified()
    rows = {site_key(r): r for r in scan_tree()}
    unflagged = sorted(k for k, e in recorded.items()
                       if e["class"] == "platform" and k in rows and not rows[k]["flag"])
    assert not unflagged, (
        f"triaged as platform claims but the checker does not flag them: {unflagged}")


def test_the_recorded_total_matches_the_classified_entries():
    """A stale total would silently widen the ratchet."""
    baseline = _baseline()
    assert baseline["total"] == sum(e["count"] for e in baseline["classified"].values())
