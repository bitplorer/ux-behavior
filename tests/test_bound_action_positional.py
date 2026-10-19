"""``BoundAction.__call__`` takes ``self`` positionally.

A keyword ``self`` is payload data. Dropping the ``/`` raises
``TypeError: multiple values for argument 'self'``.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Box(Component):
    id = "box"
    got = None

    def render(self):
        return "<div id='box'></div>"

    @action(caps=())
    def save(self, /, **extra):
        self.got = (self.id, extra.get("self"))
        return []

    @action(caps=())
    async def save_async(self, /, **extra):
        self.got = (self.id, extra.get("self"))
        return []


def _box():
    app = Behavior.boot()
    app.add(Box)
    return app.get("box")


def test_bound_action_keyword_self_is_payload():
    box = _box()
    box.save(self="me")
    assert box.got == ("box", "me")


async def test_async_bound_action_keyword_self_is_payload():
    box = _box()
    await box.save_async(self="me")
    assert box.got == ("box", "me")
