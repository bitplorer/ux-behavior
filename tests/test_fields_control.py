"""Session fields + control/submit migration helpers."""

from __future__ import annotations

from ux_behavior import Behavior, Component, Session, action


class Chrome(Component):
    id = "chrome"
    page = Session("home")
    menu_open = Session(False)

    def render(self):
        return f"<div data-page='{self.page}'></div>"

    @action(caps=())
    def go(self, page: str = "home"):
        self.page = page
        self.menu_open = False
        return None


def test_session_field_dirty_projection():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.dispatch("chrome.go", page="shop")
    assert app.get("chrome").page == "shop"
    assert ops[0].pair == ("ui.dom", "morph")


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
    assert "data_args" in attrs
