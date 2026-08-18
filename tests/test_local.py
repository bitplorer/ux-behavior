"""LocalRuntime — in-process Action calls, not a kernel."""

from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, action, update
from ux_behavior.local import LocalRuntime


class Cart(Component):
    id = "cart"

    def __init__(self) -> None:
        self.count = 0

    def render(self):
        return f"<span>{self.count}</span>"

    @action(caps=())
    def add(self, n: int = 1):
        self.count += n
        return None

    @action(caps=())
    def set_explicit(self, n: int):
        self.count = n
        return [update("cart", self.render())]

    def not_action(self):
        return None


def test_local_call_dirty_projection():
    rt = LocalRuntime.bind(Behavior.boot())
    rt.behavior.add(Cart)
    ops = rt.call("cart", "add", n=2)
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
    assert rt.behavior.get("cart").count == 2


def test_local_rejects_non_action():
    rt = LocalRuntime.bind(Behavior.boot())
    rt.behavior.add(Cart)
    with pytest.raises(TypeError, match="@action"):
        rt.call("cart", "not_action")


def test_local_actions_list():
    rt = LocalRuntime.bind(Behavior.boot())
    rt.behavior.add(Cart)
    assert "cart.add" in rt.actions("cart")


def test_local_refresh():
    rt = LocalRuntime.bind(Behavior.boot())
    rt.behavior.add(Cart)
    ops = rt.refresh("cart")
    assert ops[0].payload["target"] == "cart"
