"""Soft-register Channel drivers for agreed domain packs."""

from __future__ import annotations

from typing import Any


def try_register_drivers(behavior: Any, channel: Any) -> dict[str, str]:
    """Best-effort: if Host agreed effects/search, ask Channel to wire drivers.

    Fail-closed: missing APIs leave report as 'skipped'.
    """
    report: dict[str, str] = {}
    names = set(getattr(getattr(behavior, "domains", None), "names", []) or [])

    if "effects" in names:
        report["effects"] = _try_effects(channel)
    if "search" in names:
        report["search"] = _try_search(channel)

    behavior._driver_report = report
    return report


def _try_effects(channel: Any) -> str:
    try:
        # Channel may expose notice helpers; never hard-depend
        st = getattr(channel, "st", None)
        if st is not None and hasattr(st, "client"):
            return "channel"
        if hasattr(channel, "use"):
            channel.use("effects")
            return "channel"
    except Exception:
        return "skipped"
    return "skipped"


def _try_search(channel: Any) -> str:
    try:
        if hasattr(channel, "use"):
            channel.use("search")
            return "channel"
    except Exception:
        return "skipped"
    return "skipped"
