from clauderizer.markdown import frontmatter as fm

DOC = """---
id: subsys.auth
type: subsystem
version: 1.0.0
status: active
depends_on:
  - subsys.calc-engine@^1.0.0
  - subsys.game-data
count: 3
enabled: true
note: null
documented_in: docs/subsystems/auth.md
---

# Auth subsystem

Body text here.
"""


def test_parse_basic():
    data, body = fm.parse(DOC)
    assert data["id"] == "subsys.auth"
    assert data["type"] == "subsystem"
    assert data["version"] == "1.0.0"
    assert data["depends_on"] == ["subsys.calc-engine@^1.0.0", "subsys.game-data"]
    assert data["count"] == 3
    assert data["enabled"] is True
    assert data["note"] is None
    assert body.startswith("# Auth subsystem")


def test_round_trip_data_equality():
    data1, body1 = fm.parse(DOC)
    rendered = fm.serialize(data1, body1)
    data2, body2 = fm.parse(rendered)
    assert data1 == data2
    assert body1.strip() == body2.strip()


def test_serialize_is_idempotent():
    data, body = fm.parse(DOC)
    once = fm.serialize(data, body)
    twice = fm.serialize(*fm.parse(once))
    assert once == twice


def test_no_frontmatter_passthrough():
    text = "# Just a doc\n\nNo frontmatter.\n"
    data, body = fm.parse(text)
    assert data == {}
    assert body == text


def test_quoting_roundtrip_for_special_values():
    data = {"title": "A: tricky value", "id": "x"}
    out = fm.serialize(data, "body\n")
    back, _ = fm.parse(out)
    assert back["title"] == "A: tricky value"
    assert back["id"] == "x"
