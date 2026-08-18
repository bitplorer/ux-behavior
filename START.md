# Start — first behavior in five minutes

```bash
pip install -e ".[dev]"
```

```python
from ux_behavior import Behavior, Component, action

class CartBadge(Component):
    id = "cart.badge"
    count: int = 0

    def render(self):
        return f"<button>{self.count}</button>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.count += 1

app = Behavior.boot(title="Cart")
app.add(CartBadge)
print(app.components().keys())
```

When you need a live Result with motion:

```python
from ux_behavior.wire import compose, lower

ops = compose(
    lower("#view", html),
    scene.play(),  # no html on #view
)
```
