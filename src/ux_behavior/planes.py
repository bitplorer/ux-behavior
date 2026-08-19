"""Plane-aware storage backends.

Default offline: MemoryPlanes.
After Behavior.attach, wire may install Channel session/client defaults
unless the Host already called ``app.state.use(...)`` (Host wins).
Fail-closed: if Channel state is missing, memory stays.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

MISSING = object()


class PlaneBackend(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...


@dataclass
class DictBackend:
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def has(self, key: str) -> bool:
        return key in self.data


@dataclass
class MemoryPlanes:
    session: DictBackend = field(default_factory=DictBackend)
    client: DictBackend = field(default_factory=DictBackend)
    store: DictBackend = field(default_factory=DictBackend)

    def backend(self, plane: str) -> PlaneBackend | None:
        if plane == "session":
            return self.session
        if plane == "client":
            return self.client
        if plane == "store":
            return self.store
        return None


def field_key(component_id: str, name: str) -> str:
    ident = (component_id or "").strip() or "component"
    return f"{ident}.{name}"


def client_path(name: str, key: str | None) -> str:
    return (key or name or "").strip() or name
