"""ui_state / pref / persist / flash + control/submit."""

from __future__ import annotations

from ux_behavior import Behavior, Component, action, flash, persist, pref, ui_state


class Chrome(Component):
    id = "chrome"
    page = ui_state("home")
    menu_open = ui_state(False)
    theme = pref("system", key="ui.theme")
    draft = persist("")
    tick = flash(0)

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


def test_ui_state_dirty_projection():
    app = Behavior.boot()
    app.add(Chrome)
    ops = app.dispatch("chrome.go", page="shop")
    assert app.get("chrome").page == "shop"
    assert ops[0].pair == ("ui.dom", "morph")


def test_pref_and_persist():
    app = Behavior.boot()
    inst = app.add(Chrome)
    assert inst.theme == "system"
    app.dispatch("chrome.set_theme", theme="dark")
    assert inst.theme == "dark"
    inst.draft = "x"
    assert inst.draft == "x"
    inst.tick = 1
    assert inst.tick == 1


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
