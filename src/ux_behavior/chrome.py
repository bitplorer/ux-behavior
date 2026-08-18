"""Chrome verbs — open / close / select / confirm.

Intent-level macros. Ports and session keys stay internal.
"""

from __future__ import annotations

from typing import Any

from ux_behavior.ops import Op


def open(kind: str, **payload: Any) -> list[Op]:
    """Open overlay of the given kind."""
    return [
        Op("kv", "set", {"key": "ui.overlay.open", "value": True}),
        Op("kv", "set", {"key": "ui.overlay.kind", "value": kind}),
        Op("kv", "set", {"key": "ui.overlay.payload", "value": dict(payload)}),
        Op("ui.dom", "morph", {"target": "overlay", "patch": None}),
    ]


def close() -> list[Op]:
    """Close overlay and clear kind/payload."""
    return [
        Op("kv", "set", {"key": "ui.overlay.open", "value": False}),
        Op("kv", "delete", {"key": "ui.overlay.kind"}),
        Op("kv", "delete", {"key": "ui.overlay.payload"}),
        Op("ui.dom", "morph", {"target": "overlay", "patch": None}),
    ]


def select(region: str, value: str) -> list[Op]:
    """Select active tab/page/accordion key."""
    return [
        Op("kv", "set", {"key": f"ui.select.{region}", "value": value}),
        Op("ui.dom", "morph", {"target": region, "patch": None}),
    ]


def confirm(title: str, body: str = "", **payload: Any) -> list[Op]:
    """Confirm dialog via the single overlay cell."""
    return open("confirm", title=title, body=body, **payload)
