"""Host State API — where MorphState planes store values.

Author fields pick a plane name (session|client|store).
Hosts wire implementations here::

    app.state.use("session", backend)
    app.state.use("store", kv)
    app.state.report
    app.state.reset("client")

No shims. Channel attach calls ``use(..., lock=False)`` for unlocked planes.
"""

from __future__ import annotations

from typing import Any, Mapping

from ux_behavior.planes import DictBackend, MemoryPlanes, PlaneBackend

_PLANES = frozenset({"session", "client", "store"})


class StateAPI:
    """Storage policy for MorphState planes on one Behavior."""

    def __init__(self, behavior: Any) -> None:
        self._behavior = behavior
        self._memory = MemoryPlanes()
        self._overrides: dict[str, PlaneBackend] = {}
        self._locked: set[str] = set()
        self._report: dict[str, str] = {
            "session": "memory",
            "client": "memory",
            "store": "memory",
        }

    # --- Host API ---------------------------------------------------------

    def use(
        self,
        plane: str,
        backend: PlaneBackend,
        *,
        lock: bool = True,
        source: str = "host",
    ) -> Any:
        """Install a backend for a plane.

        ``lock=True`` (default): Host owns this plane; attach will not overwrite.
        ``lock=False``: used by wire Channel defaults for still-unlocked planes.
        """
        self._check_plane(plane)
        if not hasattr(backend, "get") or not hasattr(backend, "set"):
            raise TypeError(
                f"backend for {plane!r} must provide get(key, default) and set(key, value)"
            )
        self._overrides[plane] = backend
        if lock:
            self._locked.add(plane)
        self._report[plane] = source
        return self._behavior

    def reset(self, plane: str | None = None) -> Any:
        """Restore memory backend(s). Clears lock for reset planes."""
        if plane is None:
            self._overrides.clear()
            self._locked.clear()
            self._report = {p: "memory" for p in _PLANES}
            return self._behavior
        self._check_plane(plane)
        self._overrides.pop(plane, None)
        self._locked.discard(plane)
        self._report[plane] = "memory"
        return self._behavior

    @property
    def report(self) -> dict[str, str]:
        """Active source per plane: memory | host | channel | …"""
        return dict(self._report)

    @property
    def locked(self) -> frozenset[str]:
        return frozenset(self._locked)

    @property
    def backends(self) -> dict[str, PlaneBackend]:
        """Resolved backend per plane (override or memory)."""
        return {p: self.backend(p) for p in sorted(_PLANES)}

    def backend(self, plane: str) -> PlaneBackend:
        self._check_plane(plane)
        if plane in self._overrides:
            return self._overrides[plane]
        bag = self._memory.backend(plane)
        assert bag is not None
        return bag

    def is_locked(self, plane: str) -> bool:
        return plane in self._locked

    # --- used by Behavior.plane_get / plane_set ----------------------------

    def get(self, plane: str, key: str, default: Any = None) -> Any:
        return self.backend(plane).get(key, default)

    def set(self, plane: str, key: str, value: Any) -> None:
        self.backend(plane).set(key, value)

    def has(self, plane: str, key: str) -> bool:
        b = self.backend(plane)
        data = getattr(b, "data", None)
        if isinstance(data, dict):
            return key in data
        # Channel backends may always "have" via get(default)
        return False

    def _check_plane(self, plane: str) -> None:
        if plane not in _PLANES:
            raise ValueError(f"unknown plane {plane!r}; use session|client|store")
