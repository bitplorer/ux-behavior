# 08 — Live Channel attach

Requires `pip install ux-channel` (or `ux-behavior[channel]` when published).

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

def create_app(asgi):
    app = Behavior.boot(
        "Shop",
        strict_caps=True,
        strict_control=True,
        strict_attach=True,
    )
    cart = app.add(Cart)

    def paint():
        return f"<main>{cart.render()}</main>"

    app.region(paint, uid="app.root")
    ch = app.attach(asgi)
    if ch is None:
        # diagnostics: CHANNEL_MISSING or ATTACH_*
        print(app.diagnostics.summary())
    return app

# Buttons (Host template):
# app.control(cart.add, sku="tee")
# → live Cap attrs when attached; offline data_action otherwise
```

Environment:

```bash
export UX_CHANNEL_SECRET="at-least-32-chars-of-secret!!!!"
# optional
export REDIS_URL="redis://localhost:6379/0"
```

Check readiness:

```python
print(app.cores_available)
print(app.state.report)
print(app.diagnostics.last_hint())
```
