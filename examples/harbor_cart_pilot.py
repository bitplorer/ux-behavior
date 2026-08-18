"""Minimal Harbor bag/cart pilot on ux-behavior.

Not a full harbor port. Shows the author-seat mapping:

  ux_app Component methods + finish/open_overlay
    →  ux_behavior @action + open / submit_outcome / dirty projection

Run in-process (no Channel required)::

    python examples/harbor_cart_pilot.py

With Channel + FastAPI::

    pip install fastapi
    pip install -e "git+https://github.com/bitplorer/ux-channel.git#subdirectory=python#egg=ux-channel"
"""

from __future__ import annotations

from ux_behavior import (
    Behavior,
    Component,
    action,
    open,
    notify,
    go,
    submit_outcome,
)
from ux_behavior.local import LocalRuntime


class Cart(Component):
    """Pilot of harbor app.screens.bag.Cart — author seat only."""

    id = "cart"

    def __init__(self) -> None:
        self.lines: list[dict] = []
        self.promo: str = ""

    def render(self) -> str:
        if not self.lines:
            return "<div id='cart'><p>Bag is empty</p></div>"
        items = "".join(
            f"<li>{row['id']} × {row['qty']}</li>" for row in self.lines
        )
        return f"<div id='cart'><ul>{items}</ul><p>promo={self.promo}</p></div>"

    @action(caps=())
    def add(self, id: str = "", qty: int = 1) -> list:
        for row in self.lines:
            if row["id"] == id:
                row["qty"] += qty
                break
        else:
            self.lines.append({"id": id, "qty": qty})
        # Harbor: finish(open_overlay("sheet", key="cart"), message=...)
        return list(open("sheet", key="cart")) + [notify(f"Added {id}")]

    @action(caps=())
    def remove(self, id: str = "") -> list:
        self.lines = [r for r in self.lines if r["id"] != id]
        return list(open("sheet", key="cart")) + [notify("Removed")]

    @action(caps=())
    def promo_apply(self, code: str = "") -> list:
        key = (code or "").strip().upper()
        if key in {"HARBOR10", "COAST20"}:
            self.promo = key
            msg = f"{key} applied"
        else:
            self.promo = ""
            msg = "Code not recognised"
        # Region morph + notice (submit_outcome pattern for the cart panel)
        return list(open("sheet", key="cart")) + list(
            submit_outcome("cart", self.render(), message=msg)
        )

    @action(caps=())
    def show(self):
        return [go("/cart")]


def main() -> None:
    app = Behavior.boot(title="Harbor pilot")
    # sheet chrome pairs are Host/overlay session keys — stamp ui/nav is enough for morph/notify/go
    app.add(Cart)
    rt = LocalRuntime.bind(app)

    ops = rt.call("cart", "add", id="linen-01", qty=1)
    print("add ops:", [(o.fq, o.payload) for o in ops])

    ops = rt.call("cart", "promo_apply", code="HARBOR10")
    print("promo ops:", len(ops), "promo=", app.get("cart").promo)

    ops = rt.call("cart", "show")
    print("show ops:", [(o.fq, o.payload) for o in ops])

    from ux_behavior.wire import probe, attach_info

    print("probe:", probe())
    print("attach_info:", attach_info(app))


if __name__ == "__main__":
    main()
