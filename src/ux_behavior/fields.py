"""Author field planes — component state, not HTTP/Channel session.

Names keep ux-app plane intent; ``State`` suffix avoids session/client collisions.

* ``SessionState``   — UI chrome / screen state (page, menu_open, promo)
* ``ClientState``    — browser preference (optional allowlist key)
* ``StoreState``     — component-local value kept across actions
* ``TransientState`` — this instance only; not treated as durable

Offline: instance ``__dict__``. Live Channel draft mirror stays Host/Channel.
"""

from __future__ import annotations

from typing import Any


class Field:
    """Descriptor with default; value lives on the instance under the field name."""

    plane: str = "session"

    def __init__(self, default: Any = None, *, key: str | None = None) -> None:
        self.default = default
        self.key = key
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.name] = value


def SessionState(default: Any = None) -> Field:
    """UI chrome / screen state (ux-app Session + State suffix)."""
    f = Field(default)
    f.plane = "session"
    return f


def ClientState(default: Any = None, *, key: str | None = None) -> Field:
    """Browser preference (ux-app Client + State suffix)."""
    f = Field(default, key=key)
    f.plane = "client"
    return f


def StoreState(default: Any = None) -> Field:
    """Component-local value kept across actions (ux-app Store + State suffix)."""
    f = Field(default)
    f.plane = "store"
    return f


def TransientState(default: Any = None) -> Field:
    """Instance-only; not durable (ux-app Transient + State suffix)."""
    f = Field(default)
    f.plane = "transient"
    return f
