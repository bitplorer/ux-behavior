"""MorphState planes + RefState + app.state storage."""

from __future__ import annotations

from ux_behavior import (
    Behavior,
    Component,
    DictBackend,
    KeepState,
    MorphState,
    PrefState,
    RefState,
    UiState,
    action,
)


class Panel(Component):
    id = "panel"
    page = UiState("home")
    theme = PrefState("system", key="ui.theme")
    step = KeepState(1)
    tick = RefState(0)

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


def test_session_store_in_memory_backends():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.page = "shop"
    assert app.state.backend("session").data["panel.page"] == "shop"
    assert inst.page == "shop"
    inst.step = 3
    assert app.state.backend("store").data["panel.step"] == 3


def test_client_uses_key_path():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.theme = "dark"
    assert app.state.backend("client").data["ui.theme"] == "dark"
    assert inst.theme == "dark"


def test_ref_not_in_plane_backends():
    app = Behavior.boot()
    inst = app.add(Panel)
    inst.tick = 9
    assert "tick" not in getattr(app.state.backend("session"), "data", {})
    assert app.state.backend("store").data.get("panel.tick") is None
    assert inst.tick == 9


def test_host_use_backend():
    app = Behavior.boot()
    custom = DictBackend()
    app.state.use("store", custom)
    inst = app.add(Panel)
    inst.step = 7
    assert custom.data["panel.step"] == 7
    # default memory store bag was not written
    mem = app.state._memory.store
    assert "panel.step" not in mem.data
    assert app.state.report["store"] == "host"
    assert "store" in app.state.locked


def test_dirty_and_ref():
    app = Behavior.boot()
    app.add(Panel)
    assert app.dispatch("panel.go", page="cart")
    assert app.dispatch("panel.next_step")
    assert app.dispatch("panel.bump") == []


def test_morph_backend_param():
    """Explicit MorphState(backend=...) matches Ui/Pref/Keep sugar."""

    class Box(Component):
        id = "box"
        a = MorphState("x")
        b = MorphState("y", backend="client", key="ui.b")
        c = MorphState(0, backend="store")

        def render(self):
            return ""

    app = Behavior.boot()
    inst = app.add(Box)
    inst.a = "A"
    inst.b = "B"
    inst.c = 2
    assert app.state.backend("session").data["box.a"] == "A"
    assert app.state.backend("client").data["ui.b"] == "B"
    assert app.state.backend("store").data["box.c"] == 2
