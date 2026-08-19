"""MorphState / NoMorphState — backend=, seal=."""

from __future__ import annotations

import pytest

from ux_behavior import (
    Behavior,
    Component,
    MorphState,
    NoMorphState,
    action,
)
from ux_behavior.planes import DictBackend


class Box(Component):
    id = "box"
    page = MorphState("home")  # session
    step = MorphState(1, backend="store")
    theme = MorphState("system", backend="client", key="ui.theme")
    n = MorphState(0, seal=int)
    token = NoMorphState(None)

    def render(self):
        return f"<div>{self.page}:{self.step}:{self.theme}:{self.n}</div>"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        return None

    @action(caps=())
    def bump_token(self):
        self.token = "x"
        return None

    @action(caps=())
    def set_n(self, n: int = 0):
        self.n = n
        return None


def test_morph_dirties_nomorph_does_not():
    app = Behavior.boot()
    app.add(Box)
    assert app.dispatch("box.go", page="shop")
    assert app.dispatch("box.bump_token") == []


def test_backend_bags():
    app = Behavior.boot()
    inst = app.add(Box)
    inst.page = "a"
    inst.step = 9
    inst.theme = "dark"
    assert app.planes.session.data["box.page"] == "a"
    assert app.planes.store.data["box.step"] == 9
    assert app.planes.client.data["ui.theme"] == "dark"


def test_seal_rejects_coerce():
    app = Behavior.boot()
    inst = app.add(Box)
    with pytest.raises(TypeError, match="sealed"):
        inst.n = "1"  # type: ignore[assignment]
    inst.n = 3
    assert inst.n == 3


def test_custom_backend_on_field():
    bag = DictBackend()
    class C(Component):
        id = "c"
        x = MorphState(0, backend=bag)

        def render(self):
            return str(self.x)

        @action(caps=())
        def set(self, v: int = 0):
            self.x = v
            return None

    app = Behavior.boot()
    app.add(C)
    app.dispatch("c.set", v=5)
    assert bag.data["c.x"] == 5
