"""Omitted defaults are not type-checked.

``b: Box = None`` with ``b`` left out stays accepted. Only a value the
caller actually passed is checked.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action


class Box:
    pass


class Demo(Component):
    id = "demo"
    seen = "unset"

    def render(self):
        return "<div id='demo'></div>"

    @action(caps=())
    def go(self, b: Box = None):
        self.seen = b
        return []


def test_explicit_none_for_box_default_is_rejected():
    """``2ae5c3d`` type-checks a passed ``b=None`` for ``b: Box = None``.

    The call is rejected and the action does not run. Omitting ``b`` is a
    different case and stays accepted.
    """
    app = Behavior.boot()
    app.add(Demo)
    app.dispatch("demo.go", b=None)
    assert app.get("demo").seen == "unset"

    omitted = Behavior.boot()
    omitted.add(Demo)
    omitted.dispatch("demo.go")
    assert omitted.get("demo").seen is None


def test_omitted_default_is_not_type_checked():
    app = Behavior.boot()
    app.add(Demo)
    app.dispatch("demo.go")
    assert app.get("demo").seen is None

    refused = Behavior.boot()
    refused.add(Demo)
    refused.dispatch("demo.go", b=None)
    assert refused.get("demo").seen == "unset"

    accepted = Behavior.boot()
    accepted.add(Demo)
    box = Box()
    accepted.dispatch("demo.go", b=box)
    assert accepted.get("demo").seen is box
