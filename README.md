# ux-behavior

**Standard Channel interface for product behavior.**  
Component + actions + Morph/Ref state → verified `list[Op]`. Optional live Caps via `ux-channel`.

```python
from ux_behavior import Behavior, Component, MorphState, action

class Cart(Component):
    id = "cart"
    count = MorphState(0)

    def render(self):
        return f"<div id='cart'>{self.count}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return None

app = Behavior.boot("Shop")
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")
```

## Documentation

| | |
|--|--|
| **Tutorial (FastAPI-style)** | **[docs/tutorial/README.md](docs/tutorial/README.md)** |
| Guide | [docs/GUIDE.md](docs/GUIDE.md) |
| API reference | [docs/REFERENCE.md](docs/REFERENCE.md) |
| States | [docs/STATE.md](docs/STATE.md) |
| Control flow / Caps | [docs/CONTROL_FLOW.md](docs/CONTROL_FLOW.md) |
| Full shop example | [docs/tutorial/09-full-shop.md](docs/tutorial/09-full-shop.md) |
| Host production | [docs/HOST.md](docs/HOST.md) |
| Internals | [docs/INTERNALS.md](docs/INTERNALS.md) |

## Install

```bash
pip install ux-behavior
pip install ux-channel   # optional live Caps
uxbehavior doctor --fail
```

## Mental model

```text
Component = who · Action = what · Behavior = runs it → Ops
Event = signal (follow_up/emit) · Wire = Channel when attached
```

## License

MIT
