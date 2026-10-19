"""B1: list[int] pass-through stays; one bad annotation must not blank the rest.

Live script item3_behavior_b1_type_match.py. ``list[int]`` accepting non-ints
is the documented pass-through. The sibling case (``n: int`` next to an
unresolvable annotation) is the hole: today the action runs.
"""

from __future__ import annotations

from ux_behavior import Behavior, Component, action
from ux_behavior.validate import _matches


class Box(Component):
    id = "box"
    got = None

    def render(self):
        return "<div id='box'></div>"

    @action(caps=())
    def take(self, xs: list[int]):
        self.got = ("take", xs)

    @action(caps=())
    def count(self, n: int):
        self.got = ("count", n)

    @action(caps=())
    def mixed(self, n: int, ref: "NotDefinedAnywhere" = None):  # noqa: F821
        self.got = ("mixed", n)


def _app() -> Behavior:
    app = Behavior.boot()
    app.add(Box)
    return app


def _ran(app: Behavior, name: str, **kwargs: object) -> bool:
    box = app.get("box")
    box.got = None
    app.dispatch(name, **kwargs)
    return box.got is not None


def test_list_int_pass_through_is_kept():
    """Complex generics are not element-checked. Pin the live script's claim."""
    app = _app()
    assert _ran(app, "box.take", xs=["a"])
    assert app.get("box").got == ("take", ["a"])
    assert _ran(app, "box.take", xs=5)
    assert app.get("box").got == ("take", 5)
    assert _matches(list[int], ["a"]) is True
    assert _matches(list[int], 5) is True


def test_plain_int_annotation_still_refuses():
    app = _app()
    assert _ran(app, "box.count", n="not-an-int") is False
    assert app.get("box").got is None
    assert _ran(app, "box.count", n=3)
    assert app.get("box").got == ("count", 3)


def test_unresolved_string_annotation_is_skipped():
    """An annotation that stays a string is not a type check (today and after)."""
    assert _matches("int", 1) is True
    assert _matches("int", "x") is True


def test_valid_int_still_runs_beside_unresolvable_annotation():
    app = _app()
    assert _ran(app, "box.mixed", n=4)
    assert app.get("box").got == ("mixed", 4)


def test_unresolved_annotation_does_not_disable_sibling_int_check():
    """One unresolvable hint must not turn off ``n: int`` on the same action."""
    app = _app()
    assert _ran(app, "box.mixed", n="not-an-int") is False
    assert app.get("box").got is None
    ops = app.dispatch("box.mixed", n="not-an-int")
    targets = [
        str(op.payload.get("target", ""))
        for op in ops
        if getattr(op, "pair", None) == ("ui.dom", "morph")
    ]
    assert any("error" in target for target in targets)
