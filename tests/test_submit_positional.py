"""``submit(name, action=...)`` keeps ``action`` as payload data.

The method parameters are positional-only. Removing the ``/`` makes
``action=`` collide with the action-name parameter and this test raises.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Box(Component):
    id = "box"
    got = None

    def render(self):
        return "<div id='box'></div>"

    @action(caps=())
    def save(self, action: str = ""):
        self.got = action
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Box)
    return app


def test_submit_keyword_action_is_payload():
    app = _app()
    app.submit("box.save", action="keep")
    assert app.get("box").got == "keep"


async def test_async_submit_keyword_action_is_payload():
    app = _app()
    await app.async_submit("box.save", action="keep")
    assert app.get("box").got == "keep"
