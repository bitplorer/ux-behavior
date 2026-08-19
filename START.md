# Start — first behavior in five minutes

## Install

```bash
pip install -e ".[dev]"
```

## Day-1: Component + Action

```python
from ux_behavior import Behavior, Component, MorphState, action, notify
from ux_behavior import open, close, select, confirm

class CartBadge(Component):
    id = "cart.badge"
    count = MorphState(0)

    def render(self):
        return f"<button id='cart.badge'>{self.count}</button>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return [notify("Added")]

app = Behavior.boot(title="Cart")
app.add(CartBadge)
print(app.dispatch("cart.badge.add", sku="tee"))
print(list(app.components().keys()))  # ['cart.badge']
```

Chrome verbs:

```python
ops = open("dialog", title="Edit address")
ops = select("orders.tabs", "shipped")
ops = confirm("Delete?", body="Cannot undo.")
ops = close()
```

## Progressive door: live Result + motion

```python
from ux_behavior.wire import Result, Conflict

ops = (
    Result()
    .morph("#view", html)          # authority morph (idiomorph)
    .motion(scene.play())          # no html on #view — XOR enforced
    .navigate("/cart")             # ordered last
    .build()
)
```

Illegal (raises `Conflict`):

```python
Result().morph("#view", html).motion(scene_with_html_on_view).build()
```

## Doctor

```python
from ux_behavior.isolation import doctor
assert doctor() == []
```

## One mental model

```text
Product behavior  →  ux-behavior  →  verified list[Op]
Document owns markup
Channel owns wire + Caps
Motion is droppable
Host owns product chrome & layout
```
