"""Author-facing errors — message includes next step when known."""

from __future__ import annotations

from typing import Any


class BehaviorError(Exception):
    """Base. ``hint`` is the natural next step for Hosts/developers."""

    def __init__(self, message: str, *, hint: str = "") -> None:
        self.hint = hint
        if hint:
            super().__init__(f"{message} → {hint}")
        else:
            super().__init__(message)


class AuthorityError(BehaviorError):
    """Action or plane write refused (Cap / trust / preview / client risk)."""


class ContinuationError(BehaviorError):
    """Event has no continuation."""


class ValidationError(BehaviorError):
    """Action arguments failed binding or type checks."""

    def __init__(
        self,
        message: str,
        *,
        fields: dict[str, str] | None = None,
        hint: str = "",
    ) -> None:
        super().__init__(
            message,
            hint=hint
            or "Fix args or use the returned {action}.{field}-error morph targets",
        )
        self.fields: dict[str, str] = dict(fields or {})
