"""Markdown manipulation layer.

Three modules, in dependency order:

- ``frontmatter`` — parse/serialize the YAML-subset frontmatter block.
- ``sections`` — locate, append to, and replace ``## Heading`` blocks and
  ``<!-- marker:start/end -->`` regions in a document body.
- ``writer`` — the *only* sanctioned mutation path. Every structured edit
  goes through here so that edits stay idempotent and frontmatter stays valid.
"""
