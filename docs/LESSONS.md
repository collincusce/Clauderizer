# LESSONS — moved

> **This file has moved to `docs/clauderizer/LESSONS.md`.**
>
> Clauderizer now keeps its own memory in `docs/clauderizer/` and leaves
> `docs/` to you (D-080). Nothing was lost — the content is at the path above.
>
> If your tooling brought you here expecting content, the install reading this
> repo is older than the layout. Upgrade it:
>
> ```
> uv tool install "clauderizer[mcp]" --force
> ```
>
> This placeholder is inert and can be deleted once every install that touches
> this repo is on 3.0.0 or newer.

### L-900000 — SENTINEL: do not write below this line

An install too old to know about `docs/clauderizer/` will resolve *this* file
when it records a LESSONS entry, and append here. This deliberately-high id
exists so such a write cannot collide with a real one — anything numbered above
`L-900000` in this file is an orphan that belongs in the real register.
`clauderize doctor` reports them; move them and delete this file.
