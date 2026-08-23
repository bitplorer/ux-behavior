# Production-shaped application

> **Diátaxis:** how-to · **Canonical:** `docs/guides/PRODUCTION_APP.md` · **Layer:** ux-behavior  
> Map: [INDEX.md](../INDEX.md).

This is a **complete** offline-testable product slice illustrating states together, chrome, cart, checkout continuation, Host store plug, and diagnostics. Live Channel attach is shown as a function boundary.

```python
"""shop_behavior.py — production-shaped Host behavior module."""

from __future__ import annotations

from ux_behavior import (
    Behavior,
    Component,
    MorphState,
    RefState,
    DictBackend,
    action,
    follow_up,
    notify,
    go,
    open,
    close,
    update,
)

# ── Domain note ──
# Real inventory/charges live in Host services. Cart.count here is UI projection only.

class Chrome(Component):
    id = "chrome"
    page = MorphState("home")
    cart_open = MorphState(False)

    def render(self) -> str:
        return (
            f"<header id='chrome' data-page='{self.page}' "
            f"data-cart-open='{str(self.cart_open).lower()}'></header>"
        )

    @action(caps=())
    def navigate(self, page: str = "home"):
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

    def render(self) -> str:
        return f"<aside id='cart' data-count='{self.count}'></aside>"

    @action(caps=())
    def add(self, sku: str = ""):
        if not sku:
            return [update("cart.add.sku-error", "sku required")]
        self.last_sku = sku
        self.count = int(self.count) + 1
        return None


class Prefs(Component):
    id = "prefs"
    theme = MorphState("system", backend="client", key="ui.theme")

    def render(self) -> str:
        return f"<div id='prefs' data-theme='{self.theme}'></div>"

    @action(caps=())
    def set_theme(self, theme: str = "system"):
        self.theme = theme
        return None


class Checkout(Component):
    id = "checkout"
    status = MorphState("idle", backend="session")
    draft_note = MorphState("", backend="store")

    def render(self) -> str:
        return (
            f"<section id='checkout' data-status='{self.status}'>"
            f"{self.draft_note}</section>"
        )

    @action(caps=())
    def save_note(self, text: str = ""):
        self.draft_note = text
        return None

    @action(caps=("checkout.start",))
    def start(self):
        follow_up("paid", "checkout.complete")
        self.status = "awaiting_payment"
        return [open("modal.pay"), notify("Complete payment")]

    @action(caps=("checkout.complete",))
    def complete(self):
        self.status = "paid"
        return [close("modal.pay"), go("/thanks"), notify("Paid")]


def build_behavior(*, production: bool = False) -> Behavior:
    app = Behavior.boot(
        "Shop",
        strict_caps=True,
        client_risk=True,
        strict_control=production,
        strict_attach=production,
    )
    # Host durable bag for store plane (replace with Redis adapter in prod)
    app.state.use("store", DictBackend(), lock=True, source="host")
    app.add(Chrome)
    app.add(Cart)
    app.add(Prefs)
    app.add(Checkout)
    return app


def attach_live(app: Behavior, asgi) -> object | None:
    app.region(
        lambda: (
            f"{app.get('chrome').render()}"
            f"{app.get('cart').render()}"
            f"{app.get('checkout').render()}"
        ),
        uid="app.root",
    )
    return app.attach(asgi)


def demo_offline() -> None:
    app = build_behavior(production=False)
    app.dispatch("cart.add", sku="tee")
    app.dispatch("prefs.set_theme", theme="dark")
    app.dispatch("checkout.save_note", text="gift wrap")
    with app.trust():
        app.dispatch("checkout.start")
    app.emit("paid")
    assert app.get("checkout").status == "paid"
    assert app.get("cart").count == 1
    assert app.state.report["store"] == "host"
    print("demo_offline ok", app.diagnostics.summary()["counts"])


if __name__ == "__main__":
    demo_offline()
```

### How states interact in this app

| Field | Plane | Role |
|-------|-------|------|
| `chrome.page` | session | navigation |
| `cart.count` | session | UI count projection |
| `cart.last_sku` | ref | silent last input |
| `prefs.theme` | client | preference |
| `checkout.draft_note` | store (Host-locked) | durable draft |
| `checkout.status` | session | flow status |

### Live Host wiring (sketch)

```python
app = build_behavior(production=True)
ch = attach_live(app, asgi)
assert ch is not None, app.diagnostics.last_hint()
# templates: button(**app.control(app.get("cart").add, sku=sku))
```
