"""wire.Result — fluent builder with XOR."""

from __future__ import annotations

import pytest

from ux_behavior.wire import Conflict, Result


class _Scene:
    def __init__(self, ops):
        self._ops = ops

    def play(self):
        return {"ok": True, "ops": list(self._ops)}


def test_result_morph_navigate_order():
    ops = (
        Result()
        .navigate("/shop")
        .morph("#view", "<p>ok</p>")
        .build()
    )
    assert [op["op"] for op in ops] == ["morph", "navigate"]
    assert ops[0]["morph"] == "idiomorph"
    assert ops[0]["target"] == "#view"


def test_result_xor():
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
        Result().morph("#view", "<section/>").motion(scene).build()


def test_result_motion_without_html_ok():
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
    ops = Result().morph("#view", "<section/>").motion(scene).build()
    assert len(ops) == 2
