"""Component field state — MorphState | RefState.

* ``MorphState`` ≈ useState — may auto-morph on change + return None
* ``RefState``   ≈ useRef   — never auto-morph

Storage plane on MorphState: backend="session"|"client"|"store"|PlaneBackend
Host wires plane implementations via ``app.state.use(...)``.

Sugar: UiState, PrefState, KeepState (fixed backend names).
"""

from __future__ import annotations

import builtins
from typing import Any, Callable

from ux_behavior.planes import MISSING, client_path, field_key

_PLANE_NAMES = frozenset({"session", "client", "store"})


class Field:
    plane: str = "session"
    type_guard: Any = None
    validate: Callable[[Any], Any] | None = None
    custom_backend: Any = None

    def __init__(
        self,
        default: Any = None,
        *,
        plane: str = "session",
        key: str | None = None,
        type: Any = None,
        validate: Callable[[Any], Any] | None = None,
        backend: Any = None,
    ) -> None:
        self.default = default
        self.key = key
        self.name = ""
        self.plane = plane
        self.type_guard = type
        self.validate = validate
        self.custom_backend = None
        if type is not None and not isinstance(type, builtins.type):
            raise TypeError(
                "type= must be a class (e.g. int); use validate= for callables"
            )
        if isinstance(backend, str):
            if backend not in _PLANE_NAMES:
                raise ValueError(
                    f"backend must be session|client|store or a PlaneBackend, got {backend!r}"
                )
            self.plane = backend
        elif backend is not None:
            self.custom_backend = backend
            if self.plane not in _PLANE_NAMES:
                self.plane = "store"

    def __set_name__(self, owner: builtins.type, name: str) -> None:
        self.name = name

    def _guard_write(self, value: Any) -> Any:
        if self.type_guard is not None:
            if builtins.type(value) is not self.type_guard:
                raise TypeError(
                    f"field {self.name!r} requires {self.type_guard.__name__}, "
                    f"got {builtins.type(value).__name__} (no coerce)"
                )
        if self.validate is not None:
            value = self.validate(value)
        return value

    def __get__(self, obj: Any, owner: builtins.type | None = None) -> Any:
        if obj is None:
            return self
        if self.plane == "ref":
            return obj.__dict__.get(self.name, self.default)
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            val = behavior.plane_get(self.plane, obj, self)
            if val is not MISSING:
                return val
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        value = self._guard_write(value)
        if self.plane == "ref":
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
    type: Any = None,
    validate: Callable[[Any], Any] | None = None,
) -> Field:
    if isinstance(backend, str):
        return Field(
            default, plane=backend, key=key, type=type, validate=validate, backend=backend
        )
    return Field(
        default, plane="store", key=key, type=type, validate=validate, backend=backend
    )


def RefState(
    default: Any = None,
    *,
    type: Any = None,
    validate: Callable[[Any], Any] | None = None,
) -> Field:
    return Field(default, plane="ref", type=type, validate=validate)


def UiState(
    default: Any = None,
    *,
    type: Any = None,
    validate: Callable[[Any], Any] | None = None,
) -> Field:
    return MorphState(default, backend="session", type=type, validate=validate)


def PrefState(
    default: Any = None,
    *,
    key: str | None = None,
    type: Any = None,
    validate: Callable[[Any], Any] | None = None,
) -> Field:
    return MorphState(default, backend="client", key=key, type=type, validate=validate)


def KeepState(
    default: Any = None,
    *,
    type: Any = None,
    validate: Callable[[Any], Any] | None = None,
) -> Field:
    return MorphState(default, backend="store", type=type, validate=validate)


def ref_field_names(inst: Any) -> frozenset[str]:
    names: set[str] = set()
    for key, val in vars(builtins.type(inst)).items():
        if isinstance(val, Field) and val.plane == "ref":
            names.add(key)
    return frozenset(names)


def plane_storage_key(plane: str, inst: Any, fld: Field) -> str:
    cid = str(getattr(inst, "id", "") or "component")
    if plane == "client":
        return client_path(fld.name, fld.key)
    return field_key(cid, fld.name)
