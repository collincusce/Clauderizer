from clauderizer.graph import index, query


def test_build_finds_all_entities(sample_repo):
    g = index.build(sample_repo / "docs")
    ids = set(g.entities)
    assert ids == {
        "subsys.calc-engine",
        "subsys.auth",
        "feat.login",
        "feat.legacy",
    }
    assert g.get("subsys.auth").version == "1.0.0"
    assert g.by_type("feature") and len(g.by_type("feature")) == 2


def test_dependencies_and_dependents(sample_repo):
    g = index.build(sample_repo / "docs")
    assert query.dependencies(g, "subsys.auth") == ["subsys.calc-engine"]
    assert query.dependents(g, "subsys.calc-engine") == ["feat.legacy", "subsys.auth"]
    assert query.dependents(g, "subsys.auth") == ["feat.login"]


def test_transitive_dependents(sample_repo):
    g = index.build(sample_repo / "docs")
    assert query.transitive_dependents(g, "subsys.calc-engine") == [
        "feat.legacy",
        "feat.login",
        "subsys.auth",
    ]


def test_pin_violations_flags_tilde_break_only(sample_repo):
    g = index.build(sample_repo / "docs")
    violations = query.pin_violations(g)
    # feat.legacy pins calc-engine ~1.0.0 but it's at 1.2.0 -> violation.
    # subsys.auth pins ^1.0.0 -> satisfied. feat.login pins auth ^1.0.0 -> ok.
    assert len(violations) == 1
    v = violations[0]
    assert v.dependent == "feat.legacy"
    assert v.target == "subsys.calc-engine"


def test_cache_roundtrip(temp_repo):
    docs = temp_repo / "docs"
    cache = temp_repo / ".clauderizer" / "index.json"
    g1 = index.load_or_rebuild(docs, cache)
    assert cache.exists()
    g2 = index.load_or_rebuild(docs, cache)
    assert set(g1.entities) == set(g2.entities)
