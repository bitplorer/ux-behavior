"""``_bound_instance`` is bookkeeping, not a payload key.

A posted key of that name is an ordinary argument when the action names
it. It must not collide with the instance the descriptor passes in.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Box(Component):
    id = "box"
    got = None

    def render(self):
        return "<div id='box'></div>"

    @action(caps=())
    def save(self, _bound_instance: str = ""):
        self.got = (self.id, _bound_instance)
        return []

    @action(caps=())
    async def save_async(self, _bound_instance: str = ""):
        self.got = (self.id, _bound_instance)
        return []

    @action(caps=())
    def ping(self, note: str = "", **extra):
        self.got = (self.id, note, extra.get("_bound_instance", "absent"))
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Box)
    return app


def test_payload_bound_instance_is_an_ordinary_key():
    app = _app()
    app.dispatch("box.save", _bound_instance="from-payload")
    assert app.get("box").got == ("box", "from-payload")


async def test_async_payload_bound_instance_is_an_ordinary_key():
    app = _app()
    await app.async_dispatch("box.save_async", _bound_instance="from-payload")
    assert app.get("box").got == ("box", "from-payload")


def test_unnamed_bound_instance_key_is_dropped():
    app = _app()
    app.dispatch("box.ping", note="ok", _bound_instance="from-payload")
    assert app.get("box").got == ("box", "ok", "absent")
