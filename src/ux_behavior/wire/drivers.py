"""Soft-register Channel drivers — report every outcome."""

from __future__ import annotations

from typing import Any


def try_register_drivers(behavior: Any, channel: Any) -> dict[str, str]:
    report: dict[str, str] = {}
    diag = getattr(behavior, "diagnostics", None)
    names = set(getattr(getattr(behavior, "domains", None), "names", []) or [])

    if "effects" in names:
        report["effects"] = _try(channel, "effects", diag)
    if "search" in names:
        report["search"] = _try(channel, "search", diag)

    behavior._driver_report = report
    return report


def _try(channel: Any, name: str, diag: Any) -> str:
    try:
        if hasattr(channel, "use"):
            channel.use(name)
            return "channel"
        if diag is not None:
            diag.warn(
                "DRIVER_NO_USE",
                f"Channel has no use() for domain {name!r}",
                domain=name,
            )
        return "skipped"
    except Exception as exc:
        if diag is not None:
            diag.warn(
                "DRIVER_FAILED",
                f"domain {name!r}: {exc}",
                domain=name,
                error=type(exc).__name__,
            )
        return "skipped"
