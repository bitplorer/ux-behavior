# 06 — Continuations (follow_up / emit)

```python
from ux_behavior import Behavior, Component, MorphState, action, follow_up, notify

class Orders(Component):
    id = "orders"
    status = MorphState("idle")

    def render(self):
        return f"<div id='orders'>{self.status}</div>"

    @action(caps=())
    def start_checkout(self, order_id: int = 0):
        follow_up(
            "paid",
            "orders.confirm",
            args_from={"order_id": "id"},  # emit(id=...) → confirm(order_id=...)
        )
        self.status = "awaiting_payment"
        return [notify("Pay now")]

    @action(caps=())
    def confirm(self, order_id: int = 0):
        self.status = f"paid:{order_id}"
        return None

app = Behavior.boot()
app.add(Orders)

app.dispatch("orders.start_checkout", order_id=1)
assert "paid" in app.continuations

app.emit("paid", id=99)
assert app.get("orders").status == "paid:99"
```

`follow_up` **only** works inside an `@action` during dispatch (contextvar).
