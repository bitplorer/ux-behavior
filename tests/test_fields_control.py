"""SessionState / ClientState / StoreState / TransientState — claims == code."""

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


class Chrome(Component):
    id = "chrome"
    page = SessionState("home")
    menu_open = SessionState(False)
    theme = ClientState("system", key="ui.theme")
    draft = StoreState("")
    tick = TransientState(0)

    def render(self):
        return f"<div data-page='{self.page}'></div>"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        self.menu_open = False
        return None

    @action(caps=())
    def set_theme(self, theme: str = "system"):
        self.theme = theme
        return None

    @action(caps=())
    def bump_tick(self):
        self.tick = int(self.tick or 0) + 1
        return None

    @action(caps=())
    def bump_tick_and_page(self):
        self.tick = int(self.tick or 0) + 1
        self.page = "shop"
        return None


def test_session_state_dirty_projection():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.dispatch("chrome.go", page="shop")
    assert app.get("chrome").page == "shop"
    assert ops[0].pair == ("ui.dom", "morph")


def test_transient_does_not_dirty_alone():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.dispatch("chrome.bump_tick")
    assert app.get("chrome").tick == 1
    assert ops == []  # transient excluded from dirty snapshot


def test_transient_plus_session_still_dirties():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.dispatch("chrome.bump_tick_and_page")
    assert app.get("chrome").page == "shop"
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")


def test_client_store_values():
    app = Behavior.boot()
    inst = app.add(Chrome)
    assert inst.theme == "system"
    app.dispatch("chrome.set_theme", theme="dark")
    assert inst.theme == "dark"
    inst.draft = "x"
    assert inst.draft == "x"


def test_submit_alias():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.submit("chrome.go", {"page": "cart"})
    assert app.get("chrome").page == "cart"
    assert ops


def test_control_offline():
    app = Behavior.boot()
    inst = app.add(Chrome)
    attrs = app.control(inst.go, page="home")
    assert attrs["data_action"] == "chrome.go"
