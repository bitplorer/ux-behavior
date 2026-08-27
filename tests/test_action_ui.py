"""bind() emits the live channel triad plus progressive data-ux-*."""
from __future__ import annotations

from ux_behavior import Behavior, Component, action


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
