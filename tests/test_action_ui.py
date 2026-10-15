"""bind() emits the live channel triad plus progressive data-ux-*."""
from __future__ import annotations

import pytest

from ux_behavior import Behavior, Component, action, bind
from ux_behavior.action import action_ui_attrs


class Slide(Component):
    id = "carousel"

    @action(caps=())
    def next(self):
        return None

    @action(caps=())
    def goto(self, key: str = ""):
        return None


def test_bind_emits_channel_action():
    Behavior.boot("BindTriad", strict_caps=False).add(Slide)
    inst = Slide()
    attrs = inst.next.ui()
    assert attrs["data-ux-action"] == "carousel.next"
    assert attrs["data-channel-action"] == "carousel.next"
    assert "data-channel-args" not in attrs


def test_bind_emits_channel_args():
    Behavior.boot("BindTriadArgs", strict_caps=False).add(Slide)
    inst = Slide()
    attrs = inst.goto.ui(key="oak")
    assert attrs["data-channel-action"] == "carousel.goto"
    assert "oak" in attrs["data-channel-args"]
    assert attrs["data-ux-arg-key"] == "oak"


class Open(Component):
    id = "open"

    @action(caps=())
    def go(self, **kwargs):
        return None


# HTML has no escape for an attribute name. These are not ASCII identifiers.
_UNSAFE_ARG_NAMES = [
    'x" onclick="alert(1)',
    "sku-id",
    "1sku",
    "",
    "sku id",
    "has\nnewline",
    "café",
]


@pytest.mark.parametrize("name", _UNSAFE_ARG_NAMES)
def test_ui_and_action_ui_attrs_reject_unsafe_arg_names(name: str):
    Behavior.boot("UnsafeArg", strict_caps=False).add(Open)
    inst = Open()
    kwargs = {name: "1"}
    with pytest.raises(ValueError, match="not a safe attribute name"):
        inst.go.ui(**kwargs)
    with pytest.raises(ValueError, match="not a safe attribute name"):
        action_ui_attrs(inst.go, **kwargs)
    with pytest.raises(ValueError, match="not a safe attribute name"):
        Open.go.ui(**kwargs)
    with pytest.raises(ValueError, match="not a safe attribute name"):
        bind(inst.go, **kwargs)
