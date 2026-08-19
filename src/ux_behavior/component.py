"""Component — unit of product behavior with render + actions."""

from __future__ import annotations

from typing import Any


class Component:
    """Base for product behavior components.

    Subclass, set ``id``, implement ``render``. Methods decorated with
    ``@action`` become the behavior entry points.

    ``bind_behavior`` is called by ``Behavior.add`` so plane-aware fields work.
    """

    id: str = ""

    def __init__(self) -> None:
        self._behavior: Any = None

    def bind_behavior(self, behavior: Any) -> None:
        self._behavior = behavior

    def render(self) -> Any:
        raise NotImplementedError
