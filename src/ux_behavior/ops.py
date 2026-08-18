"""Author-facing Ops and macros.

These expand to legal pairs. They do not import Channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Op:
    ns: str
    name: str
    payload: dict[str, Any]

    @property
    def pair(self) -> tuple[str, str]:
        return (self.ns, self.name)

    @property
    def fq(self) -> str:
        return f"{self.ns}.{self.name}"


def update(target: str, html: Any = "") -> Op:
    """Author morph. Projected to Channel idiomorph by the wire door."""
    return Op("ui.dom", "morph", {"target": target, "patch": html})


def notify(message: str, *, level: str = "info") -> Op:
    """S-only notice."""
    return Op("log", "append", {"message": message, "level": level})


def go(href: str) -> Op:
    """Navigate last."""
    return Op("nav", "push", {"href": href})


def submit_outcome(
    target: str,
    html: Any = "",
    *,
    message: str | None = None,
    level: str = "info",
) -> list[Op]:
    """Outcome of a submit: morph the region + optional notice."""
    ops: list[Op] = [update(target, html)]
    if message is not None:
        ops.append(notify(message, level=level))
    return ops
