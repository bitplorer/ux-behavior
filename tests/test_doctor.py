"""Richer doctor."""

from __future__ import annotations

import ux_behavior
from ux_behavior.isolation import (
    FROZEN_PUBLIC,
    check_public_surface,
    check_stamp_hygiene,
    doctor,
)


def test_public_surface_matches_freeze():
    assert set(ux_behavior.__all__) == FROZEN_PUBLIC


def test_check_public_surface_clean():
    assert check_public_surface(ux_behavior.__all__) == []


def test_stamp_hygiene_clean():
    assert check_stamp_hygiene() == []


def test_check_public_surface_rejects_compose():
    bad = list(ux_behavior.__all__) + ["compose"]
    violations = check_public_surface(bad)
    assert violations


def test_doctor_clean_on_package():
    violations = doctor()
    assert violations == [], violations
