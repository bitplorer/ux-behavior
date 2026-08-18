"""CLI doctor."""

from __future__ import annotations

from ux_behavior.cli import main


def test_doctor_ok():
    assert main(["doctor"]) == 0


def test_doctor_fail_flag_still_zero_when_clean():
    assert main(["doctor", "--fail"]) == 0
