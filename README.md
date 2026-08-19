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
        return None  # auto morph

app = Behavior.boot("Shop")
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")
```

## Docs (start here)

**[docs/README.md](docs/README.md)** — full index  
**[docs/GUIDE.md](docs/GUIDE.md)** — mental model + first app  
**[docs/REFERENCE.md](docs/REFERENCE.md)** — API  
**[docs/CONTROL_FLOW.md](docs/CONTROL_FLOW.md)** — Caps, errors, diagnostics  
**[docs/STATE.md](docs/STATE.md)** — MorphState / RefState / app.state  
**[docs/HOST.md](docs/HOST.md)** — production Host  
**[docs/EXAMPLES.md](docs/EXAMPLES.md)** — patterns  
**[docs/INTERNALS.md](docs/INTERNALS.md)** — package internals  

## One model

```text
Component  = who (state + verbs + render)
Action     = what (@action)
Behavior   = runs it → Ops
Event      = signal (follow_up / emit)
Wire       = Channel when attached
```

## Install

```bash
pip install ux-behavior
pip install ux-channel   # optional live Caps
uxbehavior doctor --fail
```

## Public surface

`Behavior`, `Component`, `action`, Ops macros, chrome verbs, `MorphState` / `RefState` (+ sugar), `StateAPI` / `DictBackend`, `follow_up` / `Continuation`, errors, `Op`.

## Boundaries

| This package | Not this package |
|--------------|------------------|
| Actions, state fields, Ops, stamp, attach door | Cap crypto (Channel) |
| Cap **policy** | Peer apply (Channel) |
| Diagnostics + fail-closed | Markup (ux-dom) |
| | Domain SQL (Host) |

## License

MIT
