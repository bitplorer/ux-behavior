"""Behavior.refresh — id → render → update Op."""

from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, action


class Badge(Component):
    id = "cart.badge"
    count: int = 0

    def render(self):
        return f"<button>{self.count}</button>"

    @action(caps=())
    def add(self):
        self.count += 1
        return None


def test_refresh_produces_update_op():
    app = Behavior.boot(title="Shop")
    app.add(Badge)
    ops = app.refresh("cart.badge")
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
    assert ops[0].payload["target"] == "cart.badge"
    assert "<button>0</button>" in str(ops[0].payload["patch"])


def test_refresh_unknown_id():
    app = Behavior.boot()
    with pytest.raises(KeyError, match="unknown component"):
        app.refresh("missing")


def test_action_rejects_non_op_return():
    class Bad(Component):
        id = "bad"

        def render(self):
            return ""

        @action(caps=())
        def boom(self):
            return "not-ops"

    inst = Bad()
    with pytest.raises(TypeError, match=r"list\[Op\]"):
        inst.boom()


def test_action_normalizes_single_op():
    class One(Component):
        id = "one"

        def render(self):
            return "x"

        @action(caps=())
        def once(self):
            from ux_behavior import update

            return update("one", "x")

    ops = One().once()
    assert isinstance(ops, list)
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
