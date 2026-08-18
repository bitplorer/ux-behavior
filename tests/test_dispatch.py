"""Behavior.dispatch + dirty-field projection."""

from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, action, update


class CartBadge(Component):
    id = "cart.badge"
    count: int = 0

    def __init__(self) -> None:
        self.count = 0

    def render(self):
        return f"<button>{self.count}</button>"

    @action(caps=())
    def add(self, n: int = 1):
        self.count += n
        return None  # dirty projection should refresh

    @action(caps=())
    def set_explicit(self, n: int):
        self.count = n
        return [update("cart.badge", self.render())]

    @action(caps=())
    def noop(self):
        return None


def test_dispatch_dirty_projects_refresh():
    app = Behavior.boot(title="Shop")
    app.add(CartBadge)
    ops = app.dispatch("cart.badge.add", n=3)
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
    assert "3" in str(ops[0].payload["patch"])
    assert app.get("cart.badge").count == 3


def test_dispatch_explicit_ops():
    app = Behavior.boot()
    app.add(CartBadge)
    ops = app.dispatch("cart.badge.set_explicit", n=9)
    assert len(ops) == 1
    assert app.get("cart.badge").count == 9


def test_dispatch_noop_empty():
    app = Behavior.boot()
    app.add(CartBadge)
    assert app.dispatch("cart.badge.noop") == []


def test_dispatch_requires_qualified_name():
    app = Behavior.boot()
    app.add(CartBadge)
    with pytest.raises(ValueError, match="component.method"):
        app.dispatch("add")


def test_actions_list():
    app = Behavior.boot()
    app.add(CartBadge)
    names = app.actions()
    assert "cart.badge.add" in names
    assert "cart.badge.noop" in names


def test_cores_available_keys():
    app = Behavior.boot()
    assert set(app.cores_available) == {"ux_dom", "ux_channel"}
