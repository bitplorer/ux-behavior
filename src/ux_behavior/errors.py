"""Author-facing errors."""

from __future__ import annotations

from typing import Any


class BehaviorError(Exception):
    """Base for ux-behavior failures."""


class AuthorityError(BehaviorError):
    """Action refused: Cap / trust / preview."""


class ContinuationError(BehaviorError):
    """Event has no continuation."""


class ValidationError(BehaviorError):
    """Action arguments failed binding or type checks."""

    def __init__(self, message: str, *, fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.fields: dict[str, str] = dict(fields or {})
