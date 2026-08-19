"""Author field markers with plane-aware read/write."""

from __future__ import annotations

from typing import Any

from ux_behavior.planes import MISSING, client_path, field_key


class Field:
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
        if self.plane == "transient":
            return obj.__dict__.get(self.name, self.default)
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            val = behavior.plane_get(self.plane, obj, self)
            if val is not MISSING:
                return val
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        if self.plane == "transient":
            obj.__dict__[self.name] = value
            return
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            behavior.plane_set(self.plane, obj, self, value)
        obj.__dict__[self.name] = value


def SessionState(default: Any = None) -> Field:
    f = Field(default)
    f.plane = "session"
    return f


def ClientState(default: Any = None, *, key: str | None = None) -> Field:
    f = Field(default, key=key)
    f.plane = "client"
    return f


def StoreState(default: Any = None) -> Field:
    f = Field(default)
    f.plane = "store"
    return f


def TransientState(default: Any = None) -> Field:
    f = Field(default)
    f.plane = "transient"
    return f


def transient_field_names(inst: Any) -> frozenset[str]:
    names: set[str] = set()
    for key, val in vars(type(inst)).items():
        if isinstance(val, Field) and val.plane == "transient":
            names.add(key)
    return frozenset(names)


def client_field_names(inst: Any) -> frozenset[str]:
    """ClientState fields — excluded from dirty (match ux-app)."""
    names: set[str] = set()
    for key, val in vars(type(inst)).items():
        if isinstance(val, Field) and val.plane == "client":
            names.add(key)
    return frozenset(names)


def plane_storage_key(plane: str, inst: Any, fld: Field) -> str:
    cid = str(getattr(inst, "id", "") or "component")
    if plane == "client":
        return client_path(fld.name, fld.key)
    return field_key(cid, fld.name)
