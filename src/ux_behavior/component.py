"""Component — unit of product behavior with render + actions."""

from __future__ import annotations

from typing import Any


class Component:
    """Base for product behavior components.

    Subclass, set ``id``, implement ``render``. Methods decorated with
    ``@action`` become the behavior entry points.
    """

    id: str = ""

    def render(self) -> Any:
        raise NotImplementedError
