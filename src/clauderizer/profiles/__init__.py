"""Host-language profiles: data, not code.

A profile is a TOML file describing how to run a host project's test / build /
lint / typecheck commands, plus how to parse a test count from output. The
engine itself never hardcodes a language command — it reads these. Adding a new
language is a new ``<lang>.toml`` here, nothing more.
"""
