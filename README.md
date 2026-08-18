# ux-behavior

**Product behavior becomes a verified list of Ops. Cores stay pure. Host owns chrome.**

A clean author/composition layer with progressive disclosure, intentful names, low cognitive load, and strict isolation.

Parallel redesign of the seat currently occupied by `ux-app`.

```python
from ux_behavior import Behavior, Component, action, update, notify, go

class CartBadge(Component):
    id = "cart.badge"
    count: int = 0

    def render(self):
        return Badge(self.count, on_click=self.add)

    @action(caps=())
    def add(self, sku: str = ""):
        self.count += 1

app = Behavior.boot(title="Shop")
app.add(CartBadge)
```

## One mental model

```text
Product meaning  →  ux-behavior  →  list[Op]
Document owns markup
Channel owns the wire + Caps
Motion is droppable
Host owns product chrome and layout
```

There is **one** primary path. Advanced wire control is progressive, not a second competing API.

## Public surface (frozen)

```python
from ux_behavior import (
    Behavior,          # composition root
    Component,
    action,
    update, notify, go,
    open, close, select, confirm,  # chrome verbs
    Op,                # advanced only
)
```

### Progressive door (Host / live Result)

```python
from ux_behavior.wire import compose, lower, Conflict

ops = compose(
    lower("#view", html),
    scene.play(),          # motion without html on #view — XOR enforced
)
```

`compose` / `lower` are **not** on the top-level `__all__`. That friction is intentional.

## What is different from ux-app

| | ux-app | ux-behavior |
|--|--------|-------------|
| Name | Generic, overloaded | Specific: product *behavior* |
| Root | `App` | `Behavior` |
| Mental model | Dual audiences | One path + progressive disclosure |
| Wire helpers | Feel bolted-on under `.adapter` | Clearly progressive `ux_behavior.wire` |
| Chrome | Macros exist, ports visible | Verbs first (`open`/`close`/`select`), ports internal |
| Public surface | Broader + historical residue | Small and frozen from day 1 |
| Stability | Strong after cleanup | Explicit freeze + doctor from v0.1 |
| Cognitive load | Medium-high | Designed to be low |

Hard laws kept identical: isolation, one-intent-one-name, no fifth kernel, XOR on one Result, cold import clean.

## Install

```bash
pip install -e ".[dev]"
```

## Docs

- [DESIGN.md](DESIGN.md) — decisions, reopen conditions, comparison
- [START.md](START.md) — first morph in five minutes

## Status

Foundation. Core isolation, composition, and progressive wire door are in place. Not a full feature-for-feature port of every ux-app capability yet — the goal of this repo is a clean, high-signal seat with better ergonomics.
