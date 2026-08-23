# ux-behavior

**Standard Channel interface for product behavior.**
`Component` + actions + Morph/Ref state → verified `list[Op]`.
Optional live Caps via [`ux-channel`](https://github.com/bitplorer/ux-channel).

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

> **New here?** [START_HERE.md](START_HERE.md) (5 minutes). Also: [START.md](START.md).
> **Map:** [docs/INDEX.md](docs/INDEX.md)
> **Binding design:** [DESIGN.md](DESIGN.md)
> **Contributor / agent:** [CONTRIBUTING.md](CONTRIBUTING.md) · [AGENTS.md](AGENTS.md)

This layer **owns product behavior**. It does not own raw HTML construction or
wire codecs. Markup stays in ux-dom. Caps/wire stay in ux-channel.

```python
from ux_behavior import Behavior, Component, MorphState, action, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return f"<div id='cart'>{self.count}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify("Added")]

app = Behavior.boot("Shop", strict_caps=True)
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")   # public
# app.dispatch("orders.place", ...)          # Cap-protected → AuthorityError offline
# with app.trust(): ...                      # tests only
# await app.async_dispatch(...)              # first-class async
```

## Install

```bash
pip install ux-behavior
pip install "ux-behavior[channel]"   # optional live Caps
uxbehavior doctor --fail
```

## Mental model

```text
Signal  →  Verb (@action)  →  Unit (Component)  →  Root (Behavior)  →  Wire (Channel)
MorphState = must repaint · RefState = silent · Ops = result instructions
```

| Concept | Role |
|---------|------|
| **Behavior** | Composition root: boot, add, dispatch, attach, control, emit |
| **Component** | Named unit with fields + actions |
| **MorphState / RefState** | Dirty projection vs silent |
| **@action(caps=...)** | Verb; empty caps = public |
| **follow_up / emit** | Continuations |
| **control()** | Button attrs (+ Cap when Channel attached) |

### Ownership

| Owns | Does **not** own |
|------|------------------|
| Product meaning → verified `list[Op]` | Raw HTML / Document (`ux-dom`) |
| MorphState / RefState / `@action` / validation | Wire codecs, Cap crypto (`ux-channel`) |
| Chrome verbs (`open` / `close` / `select` / `confirm`) | Motion IR (`ux-motion`) |
| Isolation Law (cold import loads no Channel) | Product CLI / serve (`ux-compose`) |

### Audience

| You are… | Start |
|----------|--------|
| **New** | [START_HERE.md](START_HERE.md) |
| **Tutorial** | [docs/tutorial/](docs/tutorial/README.md) |
| **UI patterns** | [docs/patterns/](docs/patterns/README.md) |
| **Maintainer** | [DESIGN.md](DESIGN.md) · [AGENTS.md](AGENTS.md) |
| **Need a map** | [docs/INDEX.md](docs/INDEX.md) |

## Documentation

| Topic | Link |
|-------|------|
| **Start (5 min)** | [START_HERE.md](START_HERE.md) |
| Short start (kept) | [START.md](START.md) |
| Tutorial | [docs/tutorial/](docs/tutorial/README.md) |
| Docs index | [docs/INDEX.md](docs/INDEX.md) · [docs/README.md](docs/README.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| API | [docs/API.md](docs/API.md) |
| State | [docs/STATE_DEEP.md](docs/STATE_DEEP.md) |
| **UI patterns** | [docs/patterns/](docs/patterns/README.md) |
| Nested systems | [docs/patterns/COMPLEX_NESTED.md](docs/patterns/COMPLEX_NESTED.md) |
| Mode matrix (offline/online × Caps × async) | [docs/examples/EVERY_MODE.md](docs/examples/EVERY_MODE.md) |
| Offline ↔ online parity | [docs/examples/OFFLINE_ONLINE.md](docs/examples/OFFLINE_ONLINE.md) |
| Migration from ux-app | [MIGRATION.md](MIGRATION.md) |

## Tests

```bash
pip install -e ".[dev]"
pytest -q --ignore=tests/test_live_channel.py
# full matrix:
pytest tests/test_examples_matrix.py tests/test_online_matrix.py \
       tests/test_parity_extra.py tests/test_every_mode.py -q
```

## License

MIT
