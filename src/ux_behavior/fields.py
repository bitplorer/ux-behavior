"""Author fields — MorphState vs NoMorphState.

* ``MorphState``   — change + return None → dirty → morph
* ``NoMorphState`` — instance memory only; never auto-morph

Storage backend is a parameter on MorphState::

    MorphState("home")                       # backend="session"
    MorphState("system", backend="client", key="ui.theme")
    MorphState(1, backend="store")
    MorphState(0, seal=int)                  # opt-in strict type

Host-wide backends: ``Behavior.set_plane_backend("session", …)``.
Field-level custom ``PlaneBackend`` instance also accepted as ``backend=``.
"""

from __future__ import annotations

from typing import Any, Callable

from ux_behavior.planes import MISSING, client_path, field_key

_PLANE_NAMES = frozenset({"session", "client", "store"})


class Field:
    plane: str = "session"  # session|client|store|nomorph
    seal: Any = None
    custom_backend: Any = None

    def __init__(
        self,
        default: Any = None,
        *,
        plane: str = "session",
        key: str | None = None,
        seal: Any = None,
        backend: Any = None,
    ) -> None:
        self.default = default
        self.key = key
        self.name: str = ""
        self.plane = plane
        self.seal = seal
        self.custom_backend = None
        if backend is None:
            return
        if isinstance(backend, str):
            if backend not in _PLANE_NAMES:
                raise ValueError(
                    f"backend must be session|client|store or a PlaneBackend, got {backend!r}"
                )
            self.plane = backend
        else:
            # custom PlaneBackend for this field only
            self.custom_backend = backend
            if plane == "session":
                self.plane = "store"  # custom bags act like keep unless set

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def _check_seal(self, value: Any) -> Any:
        if self.seal is None:
            return value
        if isinstance(self.seal, type):
            if type(value) is not self.seal:
                raise TypeError(
                    f"sealed field {self.name!r} requires {self.seal.__name__}, "
                    f"got {type(value).__name__} (no coerce)"
                )
            return value
        if callable(self.seal):
            return self.seal(value)
        return value

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if obj is None:
            return self
        if self.plane == "nomorph":
            return obj.__dict__.get(self.name, self.default)
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            val = behavior.plane_get(self.plane, obj, self)
            if val is not MISSING:
                return val
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        value = self._check_seal(value)
        if self.plane == "nomorph":
            obj.__dict__[self.name] = value
            return
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            behavior.plane_set(self.plane, obj, self, value)
        obj.__dict__[self.name] = value


def MorphState(
    default: Any = None,
    *,
    backend: Any = "session",
    key: str | None = None,
    seal: Any = None,
) -> Field:
    """State that may auto-morph on change + return None.

    ``backend``: ``"session"`` | ``"client"`` | ``"store"`` | PlaneBackend
    ``seal``: type (exact) or callable validator — opt-in, no coerce for types
    """
    if isinstance(backend, str):
        return Field(default, plane=backend, key=key, seal=seal, backend=backend)
    return Field(default, plane="store", key=key, seal=seal, backend=backend)


def NoMorphState(default: Any = None, *, seal: Any = None) -> Field:
    """Instance memory only — never participates in dirty / auto-morph."""
    return Field(default, plane="nomorph", seal=seal)


# Transparent aliases (storage kind)
def SessionState(default: Any = None, *, seal: Any = None) -> Field:
    return MorphState(default, backend="session", seal=seal)


def ClientState(default: Any = None, *, key: str | None = None, seal: Any = None) -> Field:
    return MorphState(default, backend="client", key=key, seal=seal)


def StoreState(default: Any = None, *, seal: Any = None) -> Field:
    return MorphState(default, backend="store", seal=seal)


# Back-compat name
def TransientState(default: Any = None, *, seal: Any = None) -> Field:
    return NoMorphState(default, seal=seal)


def nomorph_field_names(inst: Any) -> frozenset[str]:
    names: set[str] = set()
    for key, val in vars(type(inst)).items():
        if isinstance(val, Field) and val.plane == "nomorph":
            names.add(key)
    return frozenset(names)


# alias used by root
transient_field_names = nomorph_field_names


def plane_storage_key(plane: str, inst: Any, fld: Field) -> str:
    cid = str(getattr(inst, "id", "") or "component")
    if plane == "client":
        return client_path(fld.name, fld.key)
    return field_key(cid, fld.name)
