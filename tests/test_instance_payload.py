"""A posted field named ``instance`` is the action's parameter.

``ActionMethod.__call__`` takes the component positionally. Dropping that
``/`` makes ``instance=`` collide with the bookkeeping argument and the
call raises (a 500 or bad_request at the bridge).
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Box(Component):
    id = "box"
    got = None

    def render(self):
        return "<div id='box'></div>"

    @action(caps=())
    def save(self, instance: str = ""):
        self.got = (self.id, instance)
        return []

    @action(caps=())
    async def save_async(self, instance: str = ""):
        self.got = (self.id, instance)
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Box)
    return app


def test_posted_instance_field_reaches_the_action():
    app = _app()
    app.dispatch("box.save", instance="from-payload")
    assert app.get("box").got == ("box", "from-payload")


async def test_async_posted_instance_field_reaches_the_action():
    app = _app()
    await app.async_dispatch("box.save_async", instance="from-payload")
    assert app.get("box").got == ("box", "from-payload")
