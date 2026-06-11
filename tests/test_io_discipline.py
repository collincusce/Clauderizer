"""beta-flip Phase 0 (D2): the bare-IO tripwire.

B2's cp1252 class: 35 bare ``read_text()`` calls in tests decoded
engine-written UTF-8 as the Windows locale — wrongly green on Linux, wrongly
red on win32 — while every platform claim passed. Encodings and newlines are
content here (L-01), so every text-mode IO call must pin ``encoding=``.

This is a tripwire, not a parser: a regex walk over the source text with an
explicit allowlist (binary modes, os.open-style flag calls). Imperfect by
design — it exists to make the *class* impossible to reintroduce silently.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THIS_FILE = Path(__file__).name

# No \s* before the paren: prose like "status: open (2026-06-05)" inside
# string literals would match, and this codebase never writes `open (`.
_CALL = re.compile(r"(?:(?<![\w.])open|\.open|\.read_text|\.write_text)\(")
_BINARY_MODES = ('"rb"', "'rb'", '"wb"', "'wb'", '"ab"', "'ab'", '"xb"', "'xb'")


def _violations(source: str, name: str = "<src>") -> list[str]:
    """Every text-mode IO call in ``source`` that does not pin encoding."""
    out = []
    for m in _CALL.finditer(source):
        depth, i = 1, m.end()
        while i < len(source) and depth:
            if source[i] == "(":
                depth += 1
            elif source[i] == ")":
                depth -= 1
            i += 1
        args = source[m.end():i - 1]
        if "encoding" in args:
            continue
        if any(mode in args for mode in _BINARY_MODES):
            continue
        if re.search(r"\bO_[A-Z]", args):  # os.open(path, os.O_…): no encoding concept
            continue
        line = source.count("\n", 0, m.start()) + 1
        out.append(f"{name}:{line}: {m.group(0).strip()}{args[:50]!r}")
    return out


def test_tripwire_fires_on_synthetic_violations():
    # the guard must fire on the failure it exists for (L-10)
    assert _violations("x = p.read_text()\n")
    assert _violations('p.write_text(content)\n')
    assert _violations('with open(path) as fh:\n    pass\n')
    # …and stay green on health
    assert not _violations('p.read_text(encoding="utf-8")\n')
    assert not _violations('p.write_text(t, encoding="utf-8")\n')
    assert not _violations('with open(path, "rb") as fh:\n    pass\n')
    assert not _violations('os.open(str(p), os.O_CREAT | os.O_EXCL)\n')
    assert not _violations('urlopen(url)\n')  # not builtin open


def test_src_and_tests_pin_every_text_io_call():
    offenders: list[str] = []
    for base in (ROOT / "src" / "clauderizer", ROOT / "tests"):
        for py in sorted(base.rglob("*.py")):
            if "__pycache__" in py.parts or py.name == THIS_FILE:
                continue
            offenders += _violations(py.read_text(encoding="utf-8"),
                                     str(py.relative_to(ROOT)))
    assert offenders == [], "bare text-mode IO (pin encoding=):\n" + "\n".join(offenders)
