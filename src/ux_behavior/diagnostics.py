"""Explicit diagnostics — nothing silent.

Every degraded or refused path records a structured event and logs it.
Hosts can read ``app.diagnostics.events`` or ``app.diagnostics.summary()``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

log = logging.getLogger("ux_behavior")

Level = Literal["info", "warn", "error"]


@dataclass
class DiagEvent:
    level: Level
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Diagnostics:
    def __init__(self) -> None:
        self.events: list[DiagEvent] = []

    def _emit(
        self,
        level: Level,
        code: str,
        message: str,
        **context: Any,
    ) -> DiagEvent:
        ev = DiagEvent(level=level, code=code, message=message, context=dict(context))
        self.events.append(ev)
        line = f"[{code}] {message}"
        if context:
            line = f"{line} | {context}"
        if level == "error":
            log.error(line)
        elif level == "warn":
            log.warning(line)
        else:
            log.info(line)
        return ev

    def info(self, code: str, message: str, **context: Any) -> DiagEvent:
        return self._emit("info", code, message, **context)

    def warn(self, code: str, message: str, **context: Any) -> DiagEvent:
        return self._emit("warn", code, message, **context)

    def error(self, code: str, message: str, **context: Any) -> DiagEvent:
        return self._emit("error", code, message, **context)

    def summary(self) -> dict[str, Any]:
        counts = {"info": 0, "warn": 0, "error": 0}
        for e in self.events:
            counts[e.level] = counts.get(e.level, 0) + 1
        return {
            "counts": counts,
            "codes": [e.code for e in self.events],
            "events": [
                {
                    "level": e.level,
                    "code": e.code,
                    "message": e.message,
                    "context": e.context,
                    "at": e.at,
                }
                for e in self.events
            ],
        }

    def clear(self) -> None:
        self.events.clear()

    def has_errors(self) -> bool:
        return any(e.level == "error" for e in self.events)

    def has_warnings(self) -> bool:
        return any(e.level == "warn" for e in self.events)
