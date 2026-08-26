"""bind_action_args binds the @action function, not BoundAction.__call__(*args)."""

from __future__ import annotations

from ux_behavior import Behavior, Component, action
from ux_behavior.validate import bind_action_args


class Cart(Component):
    id = "cart"
    n: int = 0

    def render(self):
        return str(self.n)

    @action(caps=())
    def tick(self):
        self.n += 1
        return None

    @action(caps=())
    def add(self, sku: str = "", n: int = 1):
        self.n += n
        return None

    @action(caps=())
    def pack(self, args: dict | None = None):
        self.n += 1
        return None


def test_bind_empty_does_not_inject_args():
    app = Behavior.boot(strict_caps=False)
    inst = app.add(Cart)
    assert bind_action_args(inst.tick, {}) == {}
    assert "args" not in bind_action_args(inst.tick, {"args": {}})


def test_bind_unpacks_intent_args_dict():
    app = Behavior.boot(strict_caps=False)
    inst = app.add(Cart)
    assert bind_action_args(inst.add, {"args": {"sku": "tee", "n": 2}}) == {
        "sku": "tee",
        "n": 2,
    }
    assert bind_action_args(inst.add, {"sku": "oak"})["sku"] == "oak"


def test_bind_keeps_declared_args_parameter():
    app = Behavior.boot(strict_caps=False)
    inst = app.add(Cart)
    payload = {"x": 1}
    assert bind_action_args(inst.pack, {"args": payload}) == {"args": payload}


def test_dispatch_tick_without_kwargs():
    app = Behavior.boot(strict_caps=False)
    app.add(Cart)
    ops = app.dispatch("cart.tick")
    assert isinstance(ops, list)
    assert app.get("cart").n == 1


def test_dispatch_intent_args_dict():
    app = Behavior.boot(strict_caps=False)
    app.add(Cart)
    ops = app.dispatch("cart.add", args={"sku": "tee", "n": 3})
    assert isinstance(ops, list)
    assert app.get("cart").n == 3
