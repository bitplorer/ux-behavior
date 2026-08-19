"""Component field state — MorphState | RefState.

Industry map:

* ``MorphState`` ≈ ``useState`` — change + return None may auto-morph (SSR paint)
* ``RefState``   ≈ ``useRef``   — remember across actions; never auto-morph

Storage is a parameter on MorphState only::

    MorphState("home")                              # backend="session"
    MorphState("system", backend="client", key="ui.theme")
    MorphState(1, backend="store")
    MorphState(0, seal=int)                         # opt-in exact type
    RefState(None)

Host-wide backends: ``Behavior.set_plane_backend(...)``.
Attach may install Channel session/client defaults for unlocked planes.

RefState is policy (silent memory), not a DOM element ref.
"""

from __future__ import annotations

from typing import Any

from ux_behavior.planes import MISSING, client_path, field_key

_PLANE_NAMES = frozenset({"session", "client", "store"})


class Field:
    """Descriptor: Morph (plane-backed) or Ref (instance-only)."""

    plane: str = "session"  # session | client | store | ref
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
        self.name = ""
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
            self.custom_backend = backend
            if self.plane not in _PLANE_NAMES:
                self.plane = "store"

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
        if self.plane == "ref":
            return obj.__dict__.get(self.name, self.default)
        behavior = getattr(obj, "_behavior", None)
        if behavior is not None:
            val = behavior.plane_get(self.plane, obj, self)
            if val is not MISSING:
                return val
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj: Any, value: Any) -> None:
        value = self._check_seal(value)
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
    seal: Any = None,
) -> Field:
    """Reactive field ≈ useState. May auto-morph when changed and action returns None.

    backend: "session" | "client" | "store" | PlaneBackend
    seal: exact type or callable (opt-in)
    """
    if isinstance(backend, str):
        return Field(default, plane=backend, key=key, seal=seal, backend=backend)
    return Field(default, plane="store", key=key, seal=seal, backend=backend)


def RefState(default: Any = None, *, seal: Any = None) -> Field:
    """Silent field ≈ useRef. Never auto-morphs. Not a DOM ref."""
    return Field(default, plane="ref", seal=seal)


# Intent sugar (same as MorphState with fixed backend)
def UiState(default: Any = None, *, seal: Any = None) -> Field:
    """UI chrome — MorphState(backend='session')."""
    return MorphState(default, backend="session", seal=seal)


def PrefState(default: Any = None, *, key: str | None = None, seal: Any = None) -> Field:
    """Preference — MorphState(backend='client')."""
    return MorphState(default, backend="client", key=key, seal=seal)


def KeepState(default: Any = None, *, seal: Any = None) -> Field:
    """Component-local keep — MorphState(backend='store')."""
    return MorphState(default, backend="store", seal=seal)


# Migration aliases (same factories)
SessionState = UiState
ClientState = PrefState
StoreState = KeepState
TransientState = RefState


def ref_field_names(inst: Any) -> frozenset[str]:
    names: set[str] = set()
    for key, val in vars(type(inst)).items():
        if isinstance(val, Field) and val.plane == "ref":
            names.add(key)
    return frozenset(names)


# used by root dirty snapshot
nomorph_field_names = ref_field_names
transient_field_names = ref_field_names


def plane_storage_key(plane: str, inst: Any, fld: Field) -> str:
    cid = str(getattr(inst, "id", "") or "component")
    if plane == "client":
        return client_path(fld.name, fld.key)
    return field_key(cid, fld.name)
