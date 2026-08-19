"""Pref MorphState dirties; RefState does not."""

from __future__ import annotations

from ux_behavior import Behavior, Component, MorphState, RefState, action


class Theme(Component):
    id = "theme"
    mode = MorphState("system", backend="client", key="ui.theme")
    tick = RefState(0)

    def render(self):
        return f"<div data-theme='{self.mode}'></div>"

    @action(caps=())
    def set_mode(self, mode: str = "system"):
        self.mode = mode
        return None

    @action(caps=())
    def bump(self):
        self.tick = int(self.tick or 0) + 1
        return None


def test_client_morph_dirties():
    app = Behavior.boot()
    app.add(Theme)
    ops = app.dispatch("theme.set_mode", mode="dark")
    assert app.get("theme").mode == "dark"
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")


def test_ref_skips_dirty():
    app = Behavior.boot()
    app.add(Theme)
    assert app.dispatch("theme.bump") == []
