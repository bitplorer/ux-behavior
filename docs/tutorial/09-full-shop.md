# 09 — Full shop sketch (multi-component)

Complete offline-capable slice: chrome + cart + checkout continuation.

```python
from ux_behavior import (
    Behavior, Component, MorphState, RefState,
    action, notify, go, follow_up, open, close,
)

class Chrome(Component):
    id = "chrome"
    page = MorphState("home")
    cart_open = MorphState(False)

    def render(self):
        return (
            f"<header id='chrome' data-page='{self.page}' "
            f"data-cart='{int(self.cart_open)}'></header>"
        )

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        self.cart_open = False
        return None

    @action(caps=())
    def toggle_cart(self):
        self.cart_open = not bool(self.cart_open)
        return None

class Cart(Component):
    id = "cart"
    count = MorphState(0)
    last_sku = RefState("")

    def render(self):
        return f"<aside id='cart'>items={self.count}</aside>"

    @action(caps=())
    def add(self, sku: str = ""):
        self.last_sku = sku
        self.count = int(self.count) + 1
        return None

class Checkout(Component):
    id = "checkout"
    status = MorphState("idle")

    def render(self):
        return f"<section id='checkout'>{self.status}</section>"

    @action(caps=())
    def start(self):
        follow_up("paid", "checkout.finish")
        self.status = "awaiting"
        return [notify("Complete payment"), open("modal.pay")]

    @action(caps=())
    def finish(self):
        self.status = "done"
        return [close("modal.pay"), go("/thanks"), notify("Paid")]

def build():
    app = Behavior.boot("Shop")
    app.add(Chrome)
    app.add(Cart)
    app.add(Checkout)
    return app

if __name__ == "__main__":
    app = build()
    app.dispatch("cart.add", sku="tee")
    app.dispatch("chrome.toggle_cart")
    app.dispatch("checkout.start")
    app.emit("paid")
    assert app.get("checkout").status == "done"
    assert app.get("cart").count == 1
    print("ok", app.get("chrome").page, app.diagnostics.summary()["counts"])
```

Run: `python path/to/this_snippet.py` after `pip install ux-behavior`.
