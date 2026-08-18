"""wire.compose — fold + XOR law."""

from __future__ import annotations

import pytest

from ux_behavior.wire import Conflict, compose, lower
from ux_behavior.ops import update


class _Scene:
    def __init__(self, ops):
        self._ops = ops

    def play(self):
        return {"ok": True, "ops": list(self._ops)}


def test_lower_idiomorph():
    wire = lower("view", "<p>x</p>")
    assert wire["op"] == "morph"
    assert wire["target"] == "#view"
    assert wire["morph"] == "idiomorph"


def test_navigate_last():
    ops = compose(
        {"op": "navigate", "href": "/shop"},
        {"op": "morph", "target": "#view", "html": "<p/>", "morph": "idiomorph"},
    )
    assert [op["op"] for op in ops] == ["morph", "navigate"]


def test_xor():
    scene = _Scene(
        [
            {
                "op": "transition.play",
                "plan": {
                    "kind": "plan",
                    "root": {
                        "kind": "track",
                        "target": "#view",
                        "html": "<section id='view'>x</section>",
                    },
                },
            }
        ]
    )
    with pytest.raises(Conflict, match="XOR"):
        compose(
            {"op": "morph", "target": "view", "html": "<section/>", "morph": "idiomorph"},
            scene,
        )


def test_motion_without_html_ok():
    scene = _Scene(
        [
            {
                "op": "transition.play",
                "plan": {
                    "kind": "plan",
                    "root": {"kind": "track", "target": "#view", "role": "enter"},
                },
            }
        ]
    )
    ops = compose(
        {"op": "morph", "target": "#view", "html": "<section/>", "morph": "idiomorph"},
        scene,
    )
    assert len(ops) == 2
