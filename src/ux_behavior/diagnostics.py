"""In-process diagnostics.

**Production:** keep ``developer_hints=False`` (Behavior default). Do **not**
serialize ``summary()`` or ``hint`` fields to end-user HTTP responses.
Server logs may still record codes + safe messages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Level = Literal["info", "warn", "error"]

log = logging.getLogger("ux_behavior")

# Developer-only next steps — never attach when developer_hints is False.
HINTS: dict[str, str] = {
    "CORE_CHANNEL_ABSENT": (
        "pip install ux-channel (or ux-behavior[channel]) then app.attach(asgi)."
    ),
    "CHANNEL_MISSING": "Install ux-channel before attach if live Caps are required.",
    "ATTACH_FAILED": "Inspect Channel ASGI factory; check version compatibility.",
    "ATTACH_NO_ASGI": "Pass a real ASGI app: app.attach(asgi).",
    "ATTACH_DEV_SECRET": (
        "Set env UX_CHANNEL_SECRET (or UX_BEHAVIOR_SECRET) before production attach."
    ),
    "ATTACH_BOOT_FAILED": (
        "Check Channel config, secret length, and Redis URL; retry attach."
    ),
    "ATTACH_ASYNC_HANDLER": "Inbound dispatch uses async_dispatch.",
    "ATTACH_ASYNC_HANDLER_FAILED": (
        "Sync dispatch is active; prefer a Channel build that accepts async handlers."
    ),
    "ATTACH_IDEMPOTENT": "Reuse the existing Channel; no second boot.",
    "ATTACH_OK": "Live Caps and control() mint are available.",
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
    "CONTROL_MINTED": "Button attrs include a Cap token.",
    "CAP_REQUIRED": (
        "Attach Channel for live Caps. "
        "app.trust() / _trusted=True are for tests and wire-after-verify only."
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
    "PLANES_INSTALLED": "Session/client backends now use Channel.",
    "PLANES_NO_CHANNEL_STATE": "Channel has no state(); memory planes stay.",
    "PLANES_STATE_FAILED": "Inspect Channel state adapters; memory planes stay.",
    "DRIVERS_FAILED": "Drivers skipped; stamp still applies — register drivers on Host/Channel.",
    "DRIVER_NO_USE": "Channel has no use(); register drivers on the Host.",
    "DRIVER_FAILED": "Fix Channel domain registration or omit app.use for that domain.",
    "DRIVERS_REPORT": "Domain drivers registered on Channel.",
    "REGION_EMPTY": "app.region(render) or pass region= to attach().",
    "COMPONENT_REPLACE": "Use unique component id= to avoid overwriting.",
    "TRUST_ON": "Leave trust() ASAP; never enable in production request paths.",
    "TRUST_OFF": "strict_caps restored.",
    "PREVIEW_ON": "Writes to session/store raise until the with-block exits.",
    "PREVIEW_OFF": "session/store writes are allowed again.",
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
    def __init__(self, *, developer_hints: bool = False) -> None:
        self.developer_hints = developer_hints
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
        if self.developer_hints:
            next_step = HINTS.get(code, "") if hint is None else hint
        else:
            next_step = ""
        ev = DiagEvent(
            level=level,
            code=code,
            message=message,
            hint=next_step,
            context=dict(context),
        )
        self.events.append(ev)
        line = f"[{code}] {message}"
        if next_step:
            line = f"{line} → {next_step}"
        if context and self.developer_hints:
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
                    "context": e.context if self.developer_hints else {},
                    "at": e.at,
                }
                for e in self.events
            ],
            "developer_hints": self.developer_hints,
        }

    def clear(self) -> None:
        self.events.clear()

    def has_errors(self) -> bool:
        return any(e.level == "error" for e in self.events)

    def has_warnings(self) -> bool:
        return any(e.level == "warn" for e in self.events)

    def last_hint(self) -> str:
        """Next step from the most recent warn/error, or empty when hints off."""
        if not self.developer_hints:
            return ""
        for e in reversed(self.events):
            if e.level in ("warn", "error") and e.hint:
                return e.hint
        return ""
