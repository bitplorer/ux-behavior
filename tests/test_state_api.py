"""app.state Host API."""

from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, DictBackend, MorphState, action


class Box(Component):
    id = "box"
    page = MorphState("home")
    step = MorphState(1, backend="store")

    def render(self):
        return f"{self.page}:{self.step}"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        return None


def test_default_memory_report():
    app = Behavior.boot()
    assert app.state.report == {
        "session": "memory",
        "client": "memory",
        "store": "memory",
    }
    assert app.state.locked == frozenset()


def test_use_locks_and_stores():
    app = Behavior.boot()
    bag = DictBackend()
    app.state.use("store", bag)
    assert "store" in app.state.locked
    assert app.state.report["store"] == "host"
    inst = app.add(Box)
    inst.step = 7
    assert bag.data["box.step"] == 7


def test_reset():
    app = Behavior.boot()
    bag = DictBackend()
    app.state.use("session", bag)
    app.state.reset("session")
    assert "session" not in app.state.locked
    assert app.state.report["session"] == "memory"
    inst = app.add(Box)
    inst.page = "shop"
    # memory backend under state
    mem = app.state.backend("session")
    assert mem.data["box.page"] == "shop"


def test_use_bad_plane():
    app = Behavior.boot()
    with pytest.raises(ValueError):
        app.state.use("nope", DictBackend())


def test_morph_still_dirties():
    app = Behavior.boot()
    app.add(Box)
    ops = app.dispatch("box.go", page="cart")
    assert ops and ops[0].pair == ("ui.dom", "morph")
