"""DEBUG dev switch is public on the wire door so other stack layers reuse it."""

from __future__ import annotations

import pytest

import ux_behavior.wire as wire
from ux_behavior.wire import DEBUG_TRUTHY, debug_requests_dev
from ux_behavior.wire import attach as attach_module

TRUTHY = ["1", "true", "yes", "on", " TRUE ", "Yes", "ON", "\ton\n"]
FALSY = ["", "0", "false", "no", "off", "2", "maybe", " ", "y", "enabled"]


def test_names_are_on_the_wire_door():
    assert "DEBUG_TRUTHY" in wire.__all__
    assert "debug_requests_dev" in wire.__all__


def test_truthy_set_is_exact():
    assert DEBUG_TRUTHY == frozenset({"1", "true", "yes", "on"})
    assert isinstance(DEBUG_TRUTHY, frozenset)


def test_private_copies_are_gone():
    assert not hasattr(attach_module, "_DEBUG_TRUTHY")
    assert not hasattr(attach_module, "_debug_requests_dev")


@pytest.mark.parametrize("raw", TRUTHY)
def test_env_mapping_truthy(raw: str):
    assert debug_requests_dev({"DEBUG": raw}) is True


@pytest.mark.parametrize("raw", FALSY)
def test_env_mapping_falsy(raw: str):
    assert debug_requests_dev({"DEBUG": raw}) is False


def test_env_mapping_without_debug_is_falsy():
    assert debug_requests_dev({}) is False
    assert debug_requests_dev({"OTHER": "1"}) is False


def test_env_mapping_ignores_process_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEBUG", "1")
    assert debug_requests_dev({"DEBUG": "0"}) is False
    monkeypatch.setenv("DEBUG", "0")
    assert debug_requests_dev({"DEBUG": "1"}) is True


@pytest.mark.parametrize(("raw", "expected"), [("on", True), ("off", False)])
def test_default_reads_process_env(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool
):
    monkeypatch.setenv("DEBUG", raw)
    assert debug_requests_dev() is expected


def test_default_without_debug_is_falsy(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DEBUG", raising=False)
    assert debug_requests_dev() is False
