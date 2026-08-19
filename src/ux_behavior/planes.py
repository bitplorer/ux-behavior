"""Plane-aware storage backends.

Default: in-process MemoryPlanes (session / client / store bags).
Hosts may replace any plane via ``Behavior.set_plane_backend``.
Live Channel attach may soft-install session/client adapters (wire door).

Transient is never stored in a plane backend — instance only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class PlaneBackend(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...


@dataclass
class DictBackend:
    """Simple key/value plane bag."""

    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value


@dataclass
class MemoryPlanes:
    """Default offline backends — one bag per plane that means storage."""

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
        return None  # transient has no backend


def field_key(component_id: str, name: str) -> str:
    ident = (component_id or "").strip() or "component"
    return f"{ident}.{name}"


def client_path(name: str, key: str | None) -> str:
    return (key or name or "").strip() or name
