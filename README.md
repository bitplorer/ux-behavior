# ux-behavior

**Standard Channel interface for product behavior.**  
`Component` + actions + Morph/Ref state → verified `list[Op]`.  
Optional live Caps via [`ux-channel`](https://github.com/bitplorer/ux-channel).

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

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

## Documentation

| Topic | Link |
|-------|------|
| Tutorial | [docs/tutorial/](docs/tutorial/README.md) |
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
