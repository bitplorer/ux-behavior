# AGENTS.md — ux-behavior

Orientation for humans and agents continuing this package.

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md).

Read [DESIGN.md](DESIGN.md) (binding) then [START_HERE.md](START_HERE.md) then
[docs/INDEX.md](docs/INDEX.md). Public names: `src/ux_behavior/__init__.py` `__all__`.

## Layer ownership (hard cut)

The UX stack is a **layered system of specialists**, not a monolith.

| Layer | Owns | Must **not** own |
|-------|------|------------------|
| **ux-dom** | HTML/CSS/JS trees, `Document`, serialize, pure discovery, `uxdom` | Intent, Cap, Result ops, MorphState, motion IR, product CLI |
| **ux-channel** | Intent / Result / Cap / wire / peers / host runtime | HTML trees, CSS |
| **ux-behavior** (this repo) | Product behavior, Morph/Ref, `@action`, validation | Raw HTML construction, wire codecs |
| **ux-motion** | Presence / transition plans as data (IR v1) | Product behavior, DOM construction |
| **ux-compose** | Author composition + product CLI (`uxcompose`) | Re-implementing any specialist |

One-sentence contract (DESIGN.md): **Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.**

Do not invent a sixth product. Do not resurrect `ux-app` as a product. Do not
export `compose` / `lower` on top-level `__all__`.

## Isolation Law

- Only modules under the wire/door may import `ux_channel` or `cek_*`.
- Cold `import ux_behavior` loads no Channel, CEK, or wire codecs.
- Application modules never import cores. Doctor fails the build if they do.

## Public surface (frozen)

Day-1 (top-level `__all__`): `Behavior`, `Component`, `ComponentProtocol`,
`MorphState`, `RefState`, `action`, `bind`, `update`, `notify`, `go`,
`open`, `close`, `select`, `confirm`, `Op`, `follow_up`, plus error types
and extra field types already on `__all__`.

Progressive door (not on top-level `__all__`):

```python
from ux_behavior.wire import compose, lower, Conflict, Result
```

Do not invent synonyms for Glue / Bridge / Adapter / Contribution / `reply`.

## What not to invent

- Host-local `glue.js` or a second compositor
- Teaching Channel `transition.*` (motion stays droppable)
- Dual finish API (`reply`, effects catalogs)
- Importing Channel from application modules
- Merging visual `id=` with trust `data-channel-id`
- A sixth stack product

## Tests

```bash
pip install -e ".[dev]"
pytest -q --ignore=tests/test_live_channel.py
pytest tests/test_examples_matrix.py tests/test_online_matrix.py \
       tests/test_parity_extra.py tests/test_every_mode.py -q
uxbehavior doctor --fail
```

## Docs

- Tutorial lives in `docs/tutorial/` (one story per file).
- Patterns live in `docs/patterns/`.
- Do not put current teaching only in `KILL_UX_APP.md` (history) or CHANGELOG.
- Map: [docs/INDEX.md](docs/INDEX.md).
