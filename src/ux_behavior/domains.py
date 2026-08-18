"""Domain packs and session stamp.

Author-layer stamp only. Peer drivers stay with Channel/Host wiring.
Always-understood S pairs seed baseline + ui.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

# Always understood (S). name is one token.
S_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("kv", "set"),
        ("kv", "delete"),
        ("log", "append"),
        ("ui.dom", "morph"),
        ("ui.dom", "restore"),
        ("nav", "push"),
    }
)


def validate_pair(ns: str, name: str) -> None:
    if not ns or not name:
        raise ValueError("pair ns and name must be non-empty")
    if "." in name:
        raise ValueError(f"pair name must be one token, got {name!r}")


@dataclass(frozen=True)
class DomainPack:
    name: str
    version: str
    seed_pairs: tuple[tuple[str, str], ...]
    core: bool = False

    @property
    def pairs(self) -> frozenset[tuple[str, str]]:
        return frozenset(self.seed_pairs)


BASELINE = DomainPack(
    name="baseline",
    version="1",
    seed_pairs=(("kv", "set"), ("kv", "delete"), ("log", "append")),
    core=True,
)

UI = DomainPack(
    name="ui",
    version="1",
    seed_pairs=(("ui.dom", "morph"), ("ui.dom", "restore")),
    core=True,
)

NAV = DomainPack(
    name="nav",
    version="1",
    seed_pairs=(("nav", "push"),),
    core=True,
)


@dataclass
class DomainTable:
    """Agreed packs + stamp. Drivers are Host/Channel concern."""

    _packs: dict[str, DomainPack] = field(
        default_factory=lambda: {
            "baseline": BASELINE,
            "ui": UI,
            "nav": NAV,
        }
    )
    _agreed: list[str] = field(default_factory=lambda: ["baseline", "ui", "nav"])
    _stamp: set[tuple[str, str]] = field(default_factory=lambda: set(S_PAIRS))

    @property
    def stamp(self) -> frozenset[tuple[str, str]]:
        return frozenset(self._stamp)

    @property
    def names(self) -> list[str]:
        return list(self._agreed)

    @property
    def packs(self) -> dict[str, DomainPack]:
        return dict(self._packs)

    def register(self, pack: DomainPack) -> None:
        if not pack.seed_pairs:
            raise ValueError(f"domain {pack.name!r} has no seed pairs")
        for ns, name in pack.seed_pairs:
            validate_pair(ns, name)
        existing = self._packs.get(pack.name)
        if existing and existing.core and not pack.core:
            raise ValueError(f"cannot overwrite core domain {pack.name!r}")
        self._packs[pack.name] = pack

    def use(self, *names: str) -> None:
        for name in names:
            pack = self._packs.get(name)
            if pack is None:
                raise KeyError(f"unknown domain: {name!r}")
            if name not in self._agreed:
                self._agreed.append(name)
            self._stamp |= set(pack.seed_pairs)

    def domain(
        self,
        name: str,
        version: str,
        pairs: Iterable[tuple[str, str]],
    ) -> DomainPack:
        seed = tuple(pairs)
        pack = DomainPack(name=name, version=version, seed_pairs=seed, core=False)
        self.register(pack)
        self.use(name)
        return pack

    def allows(self, ns: str, name: str) -> bool:
        return (ns, name) in self._stamp


def default_table() -> DomainTable:
    table = DomainTable()
    # baseline/ui/nav already agreed in defaults
    return table
