---
id: feat.legacy
type: feature
version: 0.1.0
status: deferred
tier: internal
depends_on:
  - subsys.calc-engine@~1.0.0
introduced_by: D-001
documented_in: docs/features/legacy.md
last_verified: 2026-05-01
---

# Legacy feature

Pins an old calc-engine minor on purpose — used to exercise pin-violation
detection (calc-engine has since moved to 1.2.0).
