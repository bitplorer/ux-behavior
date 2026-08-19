"""Author field markers (Session / Client / Store / Transient).

Offline: instance ``__dict__`` bag (same as plain attributes).
Live Channel draft mirror is Host/Channel concern after attach — not required
for kill-ux-app author migration.

``Sealed`` from ux-app is omitted; use ordinary typed attrs.
"""

from __future__ import annotations

from typing import Any


class Field:
    """Descriptor with a default; stores on the instance under the field name."""

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


def Session(default: Any = None) -> Field:
    """UI chrome / author session field."""
    f = Field(default)
    f.plane = "session"
    return f


def Client(default: Any = None, *, key: str | None = None) -> Field:
    """Browser preference field (allowlist key optional)."""
    f = Field(default, key=key)
    f.plane = "client"
    return f


def Store(default: Any = None) -> Field:
    """Component-local durable-ish value."""
    f = Field(default)
    f.plane = "store"
    return f


def Transient(default: Any = None) -> Field:
    """This instance only; never treated as durable."""
    f = Field(default)
    f.plane = "transient"
    return f
