"""Explicit diagnostics — nothing silent; every event carries a next step.

Hosts read ``app.diagnostics.summary()`` or individual events' ``hint``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

log = logging.getLogger("ux_behavior")

Level = Literal["info", "warn", "error"]

# Default next steps by code (overridable per emit)
HINTS: dict[str, str] = {
    "CORE_CHANNEL_ABSENT": (
        "Install ux-channel (pip install ux-behavior[channel] or ux-channel) "
        "then app.attach(asgi) for live Caps."
    ),
    "CHANNEL_MISSING": (
        "Install ux-channel and retry attach; offline Caps stay refused."
    ),
    "ATTACH_NO_ASGI": "Pass a real ASGI app: app.attach(asgi).",
    "ATTACH_DEV_SECRET": (
        "Set env UX_CHANNEL_SECRET (or UX_BEHAVIOR_SECRET) before production attach."
    ),
    "ATTACH_BOOT_FAILED": (
        "Check Channel config, secret length, and Redis URL; retry attach."
    ),
    "ATTACH_ASYNC_HANDLER_FAILED": (
        "Sync dispatch is active; prefer Channel build that accepts async handlers."
    ),
    "CONTROL_OFFLINE": (
        "Call app.attach(asgi) so control() can mint Cap tokens, "
        "or keep offline attrs for pure SSR tests."
    ),
    "CONTROL_MINT_FAILED": (
        "Inspect Channel control/Cap service; fix secret/trust keys; "
        "or set strict_control=False only while debugging."
    ),
    "CONTROL_FALLBACK_OFFLINE": (
        "Buttons lack Cap until mint works; do not ship this path to production."
    ),
    "CONTROL_NO_DISPATCH": "Re-run attach() so the dispatch handler is registered.",
    "CAP_REQUIRED": (
        "Attach Channel for live Caps, or use with app.trust(): / "
        "dispatch(..., _trusted=True) only in tests."
    ),
    "VALIDATION_FAILED": (
        "Fix the posted args or show the returned {action}.{field}-error morphs."
    ),
    "STAMP_REJECT": (
        "app.use('effects'|'search'|...) or app.domain(...) to agree the pair, "
        "then retry."
    ),
    "CONTINUATION_MISSING": (
        "Call follow_up(event, action) inside a prior @action before emit(event)."
    ),
    "CONTINUATION_ARMED": "Later call app.emit(event, **slots) or async_emit.",
    "DISPATCH_EMPTY_ACTION": "Ensure the client posts ux_action / data_action.",
    "DISPATCH_FAILED": "Read the exception; fix action args, caps, or stamp.",
    "PLANE_NO_BACKEND": "app.state.use(plane, backend) or rely on default memory bags.",
    "PLANE_SESSION_FALLBACK": "Session stayed memory; check Channel state() API.",
    "PLANE_CLIENT_FALLBACK": "Client stayed memory; check Channel client allowlist.",
    "CLIENT_PLANE_PUSH_FAILED": (
        "Client mirror kept locally; fix Channel client.set or path allowlist."
    ),
    "PLANES_INSTALL_FAILED": "Planes remain memory; inspect Channel state adapters.",
    "DRIVERS_FAILED": "Drivers skipped; stamp still applies — register drivers on Host/Channel.",
    "DRIVER_NO_USE": "Channel has no use(); register drivers on the Host.",
    "DRIVER_FAILED": "Fix Channel domain registration or omit app.use for that domain.",
    "REGION_EMPTY": "app.region(render) or pass region= to attach().",
    "COMPONENT_REPLACE": "Use unique component id= to avoid overwriting.",
    "TRUST_ON": "Leave trust() ASAP; never enable in production request paths.",
    "PREVIEW_ON": "Writes to session/store raise until the with-block exits.",
}


@dataclass
class DiagEvent:
    level: Level
    code: str
    message: str
    hint: str = ""
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
        *,
        hint: str | None = None,
        **context: Any,
    ) -> DiagEvent:
        next_step = hint if hint is not None else HINTS.get(code, "See docs/BEHAVIOR.md")
        ev = DiagEvent(
            level=level,
            code=code,
            message=message,
            hint=next_step,
            context=dict(context),
        )
        self.events.append(ev)
        line = f"[{code}] {message} → {next_step}"
        if context:
            line = f"{line} | {context}"
        if level == "error":
            log.error(line)
        elif level == "warn":
            log.warning(line)
        else:
            log.info(line)
        return ev

    def info(self, code: str, message: str, *, hint: str | None = None, **context: Any) -> DiagEvent:
        return self._emit("info", code, message, hint=hint, **context)

    def warn(self, code: str, message: str, *, hint: str | None = None, **context: Any) -> DiagEvent:
        return self._emit("warn", code, message, hint=hint, **context)

    def error(self, code: str, message: str, *, hint: str | None = None, **context: Any) -> DiagEvent:
        return self._emit("error", code, message, hint=hint, **context)

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
                    "hint": e.hint,
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

    def last_hint(self) -> str:
        """Next step from the most recent warn/error, or empty."""
        for e in reversed(self.events):
            if e.level in ("warn", "error") and e.hint:
                return e.hint
        return ""
