"""Author field markers — component instance state.

**Council binding (claims == code):**

All four factories return the same ``Field`` descriptor. Values live in
``instance.__dict__``. The ``plane`` string is an **author intent label**
for migration and future Host/Channel wiring — it is not a storage engine.

* ``SessionState``   — label: UI chrome / screen state
* ``ClientState``    — label: browser preference (``key=`` reserved, unused offline)
* ``StoreState``     — label: component-local kept value
* ``TransientState`` — label: ephemeral; **also** omitted from dirty projection

What these are NOT (offline / current runtime):
Channel draft, world.kv, browser client ops, or HTTP session.
Live mirrors remain Host/Channel after attach — not claimed here until wired.
"""

from __future__ import annotations

from typing import Any


class Field:
    """Descriptor: default + instance ``__dict__`` storage."""

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
    """UI chrome / screen state (intent label; storage = instance dict)."""
    f = Field(default)
    f.plane = "session"
    return f


def ClientState(default: Any = None, *, key: str | None = None) -> Field:
    """Browser preference intent label. ``key`` reserved for live allowlist."""
    f = Field(default, key=key)
    f.plane = "client"
    return f


def StoreState(default: Any = None) -> Field:
    """Component-local kept-value intent label (storage = instance dict)."""
    f = Field(default)
    f.plane = "store"
    return f


def TransientState(default: Any = None) -> Field:
    """Ephemeral intent label; changes do not trigger dirty projection."""
    f = Field(default)
    f.plane = "transient"
    return f


def transient_field_names(inst: Any) -> frozenset[str]:
    """Names of TransientState fields on this instance's class."""
    names: set[str] = set()
    cls = type(inst)
    for key, val in vars(cls).items():
        if isinstance(val, Field) and val.plane == "transient":
            names.add(key)
    return frozenset(names)
