"""Author state markers — ux-behavior way.

Not HTTP/Channel "session". These are **component field planes**:

* ``ui_state``  — UI chrome / screen state (page, menu_open, promo)
* ``pref``      — browser preference (optional allowlist key)
* ``persist``   — component-local value kept across actions
* ``flash``     — this instance only; not treated as durable

Offline: instance ``__dict__``. Live Channel draft mirror stays Host/Channel.
"""

from __future__ import annotations

from typing import Any


class Field:
    """Descriptor with default; value lives on the instance under the field name."""

    kind: str = "ui_state"

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


def ui_state(default: Any = None) -> Field:
    """UI chrome / screen state (replaces ux-app Session)."""
    f = Field(default)
    f.kind = "ui_state"
    return f


def pref(default: Any = None, *, key: str | None = None) -> Field:
    """Browser preference field (replaces ux-app Client)."""
    f = Field(default, key=key)
    f.kind = "pref"
    return f


def persist(default: Any = None) -> Field:
    """Component-local value kept across actions (replaces ux-app Store)."""
    f = Field(default)
    f.kind = "persist"
    return f


def flash(default: Any = None) -> Field:
    """Instance-only; not treated as durable (replaces ux-app Transient)."""
    f = Field(default)
    f.kind = "flash"
    return f
