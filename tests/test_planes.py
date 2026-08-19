"""Plane-aware SessionState / ClientState / StoreState / TransientState."""

from __future__ import annotations

from ux_behavior import (
    Behavior,
    ClientState,
    Component,
    SessionState,
    StoreState,
    TransientState,
    action,
)
from ux_behavior.planes import DictBackend


class Panel(Component):
    id = "panel"
    page = SessionState("home")
    theme = ClientState("system", key="ui.theme")
    step = StoreState(1)
    tick = TransientState(0)

    def render(self):
        return f"<div>{self.page}:{self.step}</div>"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        return None

    @action(caps=())
    def next_step(self):
        self.step = int(self.step) + 1
        return None

    @action(caps=())
    def bump(self):
        self.tick = int(self.tick) + 1
        return None


def test_session_store_in_memory_planes():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.page = "shop"
    assert app.planes.session.data["panel.page"] == "shop"
    assert inst.page == "shop"
    inst.step = 3
    assert app.planes.store.data["panel.step"] == 3


def test_client_uses_key_path():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.theme = "dark"
    assert app.planes.client.data["ui.theme"] == "dark"
    assert inst.theme == "dark"


def test_transient_not_in_planes():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.tick = 9
    assert "tick" not in app.planes.session.data
    assert app.planes.store.data.get("panel.tick") is None
    assert inst.tick == 9


def test_host_override_backend():
    app = Behavior.boot()
    custom = DictBackend()
    app.set_plane_backend("store", custom)
    inst = app.add(Panel)
    inst.step = 7
    assert custom.data["panel.step"] == 7
    assert "panel.step" not in app.planes.store.data


def test_dirty_and_transient():
    app = Behavior.boot()
    app.add(Panel)
    assert app.dispatch("panel.go", page="cart")
    assert app.dispatch("panel.next_step")
    assert app.dispatch("panel.bump") == []
