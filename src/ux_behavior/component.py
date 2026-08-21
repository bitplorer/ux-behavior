"""Component — unit of product behavior with render + actions.

Contract (structural + concrete base)
------------------------------------
``ComponentProtocol`` is the structural typing surface. Any object that
provides ``id``, ``render``, ``__render__``, and ``__async_render__``
satisfies it (``@runtime_checkable``).

``Component`` is the concrete author base: subclass it, implement
``render``. ``id`` defaults to ``ClassName.lower()``; set ``id = "..."``
on the class to override. Composition layers (e.g. ux-compose) own
serialization (``__render__`` / ``__async_render__``).
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class ComponentProtocol(Protocol):
    """Structural contract for a behavior unit on the router/response plane.

    * ``render`` — author markup / tree (required)
    * ``__render__`` — sync HTML (or serializable) form
    * ``__async_render__`` — async stream for StreamingResponse
    """

    id: str

    def render(self) -> Any:
        """Return markup for this unit."""
        ...

    def __render__(self, pretty: bool = False, **kw: Any) -> str:
        """Serialize live render output to HTML string."""
        ...

    def __async_render__(
        self, pretty: bool = False, **kw: Any
    ) -> AsyncIterator[str]:
        """Async HTML stream for StreamingResponse / DirectoryRouter plane."""
        ...


class Component:
    """Base for product behavior components.

    Subclass and implement ``render``. Methods decorated with ``@action``
    become the behavior entry points.

    **Identity**

    * Default: ``id = ClassName.lower()`` (e.g. ``Cart`` → ``"cart"``)
    * Opt-in custom: declare ``id = "bag"`` on the class body

    ``bind_behavior`` is called by ``Behavior.add`` so plane-aware fields work.

    ``__render__`` / ``__async_render__`` are intentionally unimplemented
    here — composition layers supply serialization (and must satisfy
    ``ComponentProtocol``).
    """

    id: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Auto-id only when this class body did not declare id=...
        if "id" not in cls.__dict__:
            cls.id = cls.__name__.lower()

    def __init__(self) -> None:
        self._behavior: Any = None

    def bind_behavior(self, behavior: Any) -> None:
        self._behavior = behavior

    def render(self) -> Any:
        """Return markup for this unit. Subclasses must implement."""
        raise NotImplementedError(f"{type(self).__name__}.render() is required")

    def __render__(self, pretty: bool = False, **kw: Any) -> str:
        """Serialize live render output. Subclasses / composition must implement."""
        raise NotImplementedError(
            f"{type(self).__name__}.__render__() is required "
            "(composition layer should provide HTML serialization)"
        )

    async def __async_render__(
        self, pretty: bool = False, **kw: Any
    ) -> AsyncIterator[str]:
        """Async HTML stream. Subclasses / composition must implement."""
        raise NotImplementedError(
            f"{type(self).__name__}.__async_render__() is required "
            "(composition layer should provide streaming HTML)"
        )
        # make this an async generator for type-checkers
        if False:  # pragma: no cover
            yield ""
