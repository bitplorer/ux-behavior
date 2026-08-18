"""CLI doctor + scaffold."""

from __future__ import annotations

from pathlib import Path

from ux_behavior.cli import main


def test_doctor_ok():
    assert main(["doctor"]) == 0


def test_doctor_fail_flag_clean():
    assert main(["doctor", "--fail"]) == 0


def test_new_component(tmp_path: Path):
    out = tmp_path / "cart_badge.py"
    assert main(["new", "component", "CartBadge", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "class CartBadge" in text
    assert 'id = "cartbadge"' in text or "CartBadge" in text


def test_new_action(tmp_path: Path):
    out = tmp_path / "comp.py"
    main(["new", "component", "Cart", "--id", "cart", "--out", str(out)])
    assert main(["new", "action", "Cart.add", "--file", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "def add(self)" in text
