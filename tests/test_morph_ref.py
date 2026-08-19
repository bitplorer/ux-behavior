"""MorphState + RefState — canonical field API."""

from __future__ import annotations

import pytest

from ux_behavior import (
    Behavior,
    Component,
    KeepState,
    MorphState,
    PrefState,
    RefState,
    UiState,
    action,
)
from ux_behavior.planes import DictBackend


class Box(Component):
    id = "box"
    page = MorphState("home")
    step = MorphState(1, backend="store")
    theme = MorphState("system", backend="client", key="ui.theme")
    n = MorphState(0, seal=int)
    token = RefState(None)

    def render(self):
        return f"<div>{self.page}:{self.step}:{self.theme}:{self.n}</div>"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        return None

    @action(caps=())
    def bump_ref(self):
        self.token = "x"
        return None

    @action(caps=())
    def set_n(self, n: int = 0):
        self.n = n
        return None


def test_morph_dirties_ref_does_not():
    app = Behavior.boot()
    app.add(Box)
    ops = app.dispatch("box.go", page="shop")
    assert ops and ops[0].pair == ("ui.dom", "morph")
    assert app.dispatch("box.bump_ref") == []


def test_backends():
    app = Behavior.boot()
    inst = app.add(Box)
    inst.page = "a"
    inst.step = 9
    inst.theme = "dark"
    assert app.planes.session.data["box.page"] == "a"
    assert app.planes.store.data["box.step"] == 9
    assert app.planes.client.data["ui.theme"] == "dark"


def test_seal():
    app = Behavior.boot()
    inst = app.add(Box)
    with pytest.raises(TypeError, match="sealed"):
        inst.n = "1"  # type: ignore[assignment]
    inst.n = 2
    assert inst.n == 2


def test_sugar_aliases():
    class C(Component):
        id = "c"
        a = UiState("x")
        b = PrefState("y", key="ui.y")
        c = KeepState(1)
        d = RefState(0)

        def render(self):
            return ""

    app = Behavior.boot()
    inst = app.add(C)
    inst.a = "z"
    assert app.planes.session.data["c.a"] == "z"


def test_field_custom_backend():
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
