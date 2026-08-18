"""In-process helpers for tests — not a third kernel.

LocalRuntime lets Hosts and unit tests exercise Actions and refresh
without installing live ux-channel / Document. Authority stays in
Python; there is no Peer apply here.
"""

from __future__ import annotations

from typing import Any

from ux_behavior.ops import Op
from ux_behavior.root import Behavior


class LocalRuntime:
    """Bind a Behavior and invoke Actions, collecting list[Op].

    This is **not** a Host or Peer kernel. It only:

    - holds a Behavior registry
    - dispatches ``@action`` methods (with dirty-field projection)
    - returns the Ops those methods produce (or refresh Ops)
    """

    def __init__(self, behavior: Behavior | None = None) -> None:
        self.behavior = behavior or Behavior.boot()

    @classmethod
    def bind(cls, behavior: Behavior | None = None) -> "LocalRuntime":
        return cls(behavior=behavior)

    def call(self, component_id: str, method: str, **kwargs: Any) -> list[Op]:
        """Invoke an @action via Behavior.dispatch (dirty projection included)."""
        return self.behavior.dispatch(f"{component_id}.{method}", **kwargs)

    def refresh(self, component_id: str) -> list[Op]:
        return self.behavior.refresh(component_id)

    def actions(self, component_id: str | None = None) -> list[str]:
        return self.behavior.actions(component_id)
