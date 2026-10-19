"""Payload keys must not collide with dispatch's own parameters.

``action`` binds when the action names it. ``self`` is not a product
parameter, so it is not passed into ``**extra``.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action, follow_up


class Boxy(Component):
    id = "boxy"
    got = None

    def render(self):
        return "<div id='boxy'></div>"

    @action(caps=())
    def save(self, /, action: str = "", **extra):
        self.got = (action, extra.get("self"))
        return []

    @action(caps=())
    def arm(self):
        follow_up("go", "boxy.save")
        return []


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Boxy)
    return app


def test_dispatch_payload_action_and_self_keys_reach_the_action():
    app = _app()
    app.dispatch("boxy.save", **{"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


async def test_async_dispatch_payload_action_and_self_keys_reach_the_action():
    app = _app()
    await app.async_dispatch("boxy.save", **{"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


def test_submit_payload_action_and_self_keys_reach_the_action():
    app = _app()
    app.submit("boxy.save", {"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


async def test_async_submit_payload_action_and_self_keys_reach_the_action():
    app = _app()
    await app.async_submit("boxy.save", {"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


def test_emit_slots_action_and_self_keys_reach_the_action():
    app = _app()
    app.dispatch("boxy.arm")
    app.emit("go", **{"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


async def test_async_emit_slots_action_and_self_keys_reach_the_action():
    app = _app()
    app.dispatch("boxy.arm")
    await app.async_emit("go", **{"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


def test_dispatch_verified_payload_action_and_self_keys_reach_the_action():
    app = _app()
    app.dispatch_verified("boxy.save", {"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


async def test_async_dispatch_verified_payload_action_and_self_keys():
    app = _app()
    await app.async_dispatch_verified("boxy.save", {"action": "keep", "self": "me"})
    assert app.get("boxy").got == ("keep", None)


class Plain(Component):
    id = "plain"
    got = None

    def render(self):
        return "<div id='plain'></div>"

    @action(caps=())
    def save(self, action: str = "", **extra):
        self.got = (action, extra.get("self", "absent"))
        return []


def test_normal_method_does_not_500_on_payload_self():
    """A normal ``self`` is the instance. The payload key must not TypeError."""
    app = Behavior.boot()
    app.add(Plain)
    app.dispatch("plain.save", **{"action": "keep", "self": "me"})
    assert app.get("plain").got == ("keep", "absent")
