# ux-behavior

**Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.**

A clean author/composition layer with progressive disclosure, intentful names, low cognitive load, and strict isolation.

```python
from ux_behavior import Behavior, Component, action, update, notify, go
from ux_behavior import open, close, select, confirm

class CartBadge(Component):
    id = "cart.badge"
    count: int = 0

    def render(self):
        return f"<button id='cart.badge'>{self.count}</button>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count += 1

app = Behavior.boot(title="Shop")
app.add(CartBadge)
ops = app.refresh("cart.badge")  # re-render → update Op
```

## One mental model

```text
Product behavior  →  ux-behavior  →  verified list[Op]
Document owns markup
Channel owns wire + Caps
Motion is droppable
Host owns product chrome & layout
```

There is **one** primary path. Advanced wire control is progressive, not a second API.

## Public surface (frozen)

```python
from ux_behavior import (
    Behavior,          # composition root (+ refresh)
    Component,
    action,            # returns list[Op] | Op | None only
    update, notify, go,
    open, close, select, confirm,  # chrome verbs
    Op,
)
```

### Progressive door (Host / live Result)

```python
from ux_behavior.wire import Result, Conflict

ops = (
    Result()
    .morph("#view", html)       # idiomorph
    .motion(scene.play())       # XOR enforced — no html on #view
    .navigate("/cart")          # ordered last
    .build()
)
```

`compose` / `lower` / `Result` are **not** on top-level `__all__`. That friction is intentional.

### Doctor

```python
from ux_behavior.isolation import doctor
assert doctor() == []
```

## What is different from ux-app

| | ux-app | ux-behavior |
|--|--------|-------------|
| Name | Generic, overloaded | Specific: product *behavior* |
| Root | `App` | `Behavior` (+ `refresh`) |
| Mental model | Dual audiences | One path + progressive disclosure |
| Wire helpers | Feel bolted-on under `.adapter` | Clearly progressive `ux_behavior.wire` |
| Chrome | Macros exist, ports visible | Verbs first; ports internal |
| Public surface | Broader + historical residue | Small and frozen from day 1 |
| Stability | Strong after cleanup | Explicit freeze + doctor from v0.1 |
| Cognitive load | Medium-high | Designed to be low |

Hard laws kept identical: isolation, one-intent-one-name, no fifth kernel, XOR on one Result, cold import clean.

## Install

```bash
pip install -e ".[dev]"
pytest
```

## Docs

- [DESIGN.md](DESIGN.md) — decisions, reopen conditions, anti-patterns
- [START.md](START.md) — first behavior in five minutes
- [ARCHITECTURE.md](ARCHITECTURE.md) — ownership planes (when present)

## Status

Tier 1 complete (Result builder, XOR, doctor, START). Tier 2 started (`refresh`, action return contract).
