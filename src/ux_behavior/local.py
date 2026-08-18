"""In-process helpers for tests — not a third kernel.

LocalRuntime lets Hosts and unit tests exercise Actions and refresh
without installing live ux-channel / Document. Authority stays in
Python; there is no Peer apply here.
"""

from __future__ import annotations

from typing import Any, Callable

from ux_behavior.ops import Op
from ux_behavior.root import Behavior


class LocalRuntime:
    """Bind a Behavior and invoke Actions, collecting list[Op].

    This is **not** a Host or Peer kernel. It only:

    - holds a Behavior registry
    - calls ``@action`` methods
    - returns the Ops those methods produce (or refresh Ops)
    """

    def __init__(self, behavior: Behavior | None = None) -> None:
        self.behavior = behavior or Behavior.boot()

    @classmethod
    def bind(cls, behavior: Behavior | None = None) -> "LocalRuntime":
        return cls(behavior=behavior)

    def call(self, component_id: str, method: str, **kwargs: Any) -> list[Op]:
        """Invoke an @action method and return its Ops (empty list if None)."""
        inst = self.behavior.get(component_id)
        fn = getattr(inst, method, None)
        if fn is None or not callable(fn):
            raise AttributeError(
                f"{component_id}.{method} is not a callable action"
            )
        if not getattr(fn, "_ux_behavior_action", False):
            raise TypeError(
                f"{component_id}.{method} is not marked with @action"
            )
        result = fn(**kwargs)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        raise TypeError(
            f"{component_id}.{method} returned {type(result).__name__}; "
            "expected list[Op] | None"
        )

    def refresh(self, component_id: str) -> list[Op]:
        return self.behavior.refresh(component_id)

    def actions(self, component_id: str) -> list[str]:
        """Names of @action methods on a registered component."""
        inst = self.behavior.get(component_id)
        names: list[str] = []
        for name in dir(inst):
            if name.startswith("_"):
                continue
            attr = getattr(inst, name, None)
            if callable(attr) and getattr(attr, "_ux_behavior_action", False):
                names.append(name)
        return sorted(names)
