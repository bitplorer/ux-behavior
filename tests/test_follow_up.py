"""follow_up + emit + Cap posture."""

from __future__ import annotations

import pytest

from ux_behavior import (
    AuthorityError,
    Behavior,
    Component,
    ContinuationError,
    MorphState,
    action,
    follow_up,
    notify,
)


class Orders(Component):
    id = "orders"
    last = MorphState("")

    def render(self):
        return f"<div>{self.last}</div>"

    @action(caps=())
    def start(self):
        follow_up("paid", "orders.confirm", order_id=1)
        return [notify("awaiting payment")]

    @action(caps=())
    def confirm(self, order_id: int = 0):
        self.last = f"ok:{order_id}"
        return None

    @action(caps=("orders.write",))
    def secure(self):
        return [notify("secure")]


def test_follow_up_emit():
    app = Behavior.boot()
    app.add(Orders)
    ops = app.dispatch("orders.start")
    assert ops and ops[0].pair == ("log", "append")
    assert "paid" in app.continuations
    ops2 = app.emit("paid")
    assert app.get("orders").last == "ok:1"
    assert ops2  # dirty morph


def test_emit_unknown():
    app = Behavior.boot()
    app.add(Orders)
    with pytest.raises(ContinuationError):
        app.emit("missing")


def test_follow_up_outside_action():
    with pytest.raises(RuntimeError):
        follow_up("x", "orders.confirm")


def test_strict_caps_offline():
    app = Behavior.boot()
    app.add(Orders)
    with pytest.raises(AuthorityError):
        app.dispatch("orders.secure")
    ops = app.dispatch("orders.secure", _trusted=True)
    assert ops


def test_strict_caps_off():
    app = Behavior.boot(strict_caps=False)
    app.add(Orders)
    assert app.dispatch("orders.secure")
