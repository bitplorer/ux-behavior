"""ClientState participates in dirty (SSR-first)."""

from __future__ import annotations

from ux_behavior import Behavior, ClientState, Component, TransientState, action


class Theme(Component):
    id = "theme"
    mode = ClientState("system", key="ui.theme")
    tick = TransientState(0)

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


def test_client_state_dirties():
    app = Behavior.boot()
    app.add(Theme)
    ops = app.dispatch("theme.set_mode", mode="dark")
    assert app.get("theme").mode == "dark"
    assert len(ops) == 1
    assert ops[0].pair == ("ui.dom", "morph")
    assert "dark" in str(ops[0].payload.get("patch"))


def test_transient_still_skips_dirty():
    app = Behavior.boot()
    app.add(Theme)
    assert app.dispatch("theme.bump") == []
