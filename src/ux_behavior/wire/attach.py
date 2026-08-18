"""Soft live-core attach probe (progressive door).

Does not load cores at import time. Call ``probe()`` or ``attach_info()``
when a Host is ready. Full ASGI mount remains Host + Channel responsibility;
this module only reports availability and documents the attach seat.
"""

from __future__ import annotations

import importlib.util
from typing import Any


def probe() -> dict[str, bool]:
    """Return which peer cores are importable without importing them."""
    return {
        "ux_dom": importlib.util.find_spec("ux_dom") is not None,
        "ux_channel": importlib.util.find_spec("ux_channel") is not None,
    }


def attach_info(behavior: Any | None = None) -> dict[str, Any]:
    """Snapshot for Hosts deciding whether to mount live Channel."""
    available = probe()
    stamp: list[str] = []
    title = ""
    if behavior is not None:
        title = getattr(behavior, "title", "") or ""
        domains = getattr(behavior, "domains", None)
        if domains is not None:
            stamp = sorted(f"{ns}.{name}" for ns, name in domains.stamp)
    return {
        "title": title,
        "cores": available,
        "stamp": stamp,
        "ready_for_live": bool(available.get("ux_channel")),
    }
