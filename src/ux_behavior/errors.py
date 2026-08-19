"""Author-facing errors — clear, no Channel types."""

from __future__ import annotations


class BehaviorError(Exception):
    """Base for ux-behavior failures."""


class AuthorityError(BehaviorError):
    """Action refused: Cap / trust required."""


class ContinuationError(BehaviorError):
    """Event has no continuation, or continuation is incomplete."""
