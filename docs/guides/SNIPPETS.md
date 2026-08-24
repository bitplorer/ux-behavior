# ux-behavior — snippets

> **Diátaxis:** how-to · copy-paste patterns from the public API (`__all__` / CLI).
> Map: see this package `docs/INDEX.md`.

Product behavior. Component + @action + Morph/Ref → verified list[Op].

Every block is meant to run (or to be the exact fragment you drop into a running app). Names are public exports. If code and this page disagree, **code wins**.

## Contents

- [Install](#beh-install)
- [Component, MorphState, @action, dispatch](#beh-core)
- [Ops macros: update, notify, go, chrome](#beh-ops)
- [control() attrs + bind / .ui](#beh-control)
- [async_dispatch and tests-only trust()](#beh-async-trust)
- [follow_up + emit continuations](#beh-follow-up)

## Install

### Install

<a id="beh-install"></a>

Python ≥ 3.10. Isolation Law: cold import does not load Channel.

```bash
pip install ux-behavior
pip install "ux-behavior[channel]"   # optional live Caps
uxbehavior doctor --fail
```

## Core usage

### Component, MorphState, @action, dispatch

<a id="beh-core"></a>

MorphState = must repaint. RefState = silent. Empty caps = public. Non-empty caps need a live Cap or tests-only trust().

```python
from ux_behavior import Behavior, Component, MorphState, RefState, action, notify

class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")   # silent — does not by itself demand a morph

    def render(self):
        return f"<div id='cart'>{self.count} {self.last_sku}</div>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        self.last_sku = sku
        return [notify(f"Added {sku}")]

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Checkout")]

app = Behavior.boot("Shop", strict_caps=True)
app.add(Cart)
ops = app.dispatch("cart.add", sku="tee")   # public
print(ops)
# app.dispatch("cart.checkout")             # AuthorityError offline
```

### Ops macros: update, notify, go, chrome

<a id="beh-ops"></a>

@action must return list[Op] | Op | None. Chrome verbs (open/close/select/confirm) expand to legal op pairs.

```python
from ux_behavior import action, notify, update, go, open, close, confirm, select, submit_outcome

@action(caps=())
def save(self):
    return submit_outcome("#cart", self.render(), message="Saved")

@action(caps=())
def sheet(self):
    return list(open("sheet", key="cart")) + [notify("Opened")]

@action(caps=())
def jump(self):
    return [go("/orders")]
```

### control() attrs + bind / .ui

<a id="beh-control"></a>

control() emits button/form attrs. When Channel is attached, Caps are minted into those attrs.

```python
from ux_behavior import Behavior, Component, action

class Cart(Component):
    id = "cart"

    @action(caps=())
    def add(self, sku: str = ""):
        return []

app = Behavior.boot("Shop", strict_caps=False)
cart = app.add(Cart)
print(app.control("cart.add", sku="tee"))
# preferred author path when you have the method:
print(cart.add.ui(sku="tee"))
```

## Fail closed

### async_dispatch and tests-only trust()

<a id="beh-async-trust"></a>

dispatch() refuses async handlers (no nested event loop). trust() is a test door, not a production bypass.

```python
import asyncio
from ux_behavior import AuthorityError

app = Behavior.boot("Shop", strict_caps=True)
app.add(Cart)

try:
    app.dispatch("cart.checkout")
except AuthorityError as exc:
    print("offline cap", exc)

async def main():
    async with app.trust():          # tests only — never in product
        await app.async_dispatch("cart.checkout")

asyncio.run(main())
```

## Core usage

### follow_up + emit continuations

<a id="beh-follow-up"></a>

Continuations are explicit. Do not mutate from a notify callback — that is NestedTransactionError on the data plane, and ContinuationError here if misused.

```python
from ux_behavior import action, follow_up, notify

@action(caps=())
def add(self, sku: str = ""):
    self.count = int(self.count) + 1
    return [notify("Added"), follow_up("cart.refresh")]

# Later / elsewhere:
# app.emit("cart.refresh")
```
