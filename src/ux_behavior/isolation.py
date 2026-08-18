"""Isolation and public-surface freeze.

Application modules must never import cores.
Only the progressive wire door may soft-load cores when present.
Public __all__ is a freeze list; expanding it requires a DESIGN.md reopen entry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

BANNED_IMPORT_PREFIXES = (
    "ux_channel",
    "cek_",
    "cek_host",
    "cek_surface",
    "cek_runtime",
    "cek_framework",
)

# Progressive door: may speak wire shape / soft-attach cores.
WIRE_DOOR_PARTS = ("/wire/", "\\wire\\")

FROZEN_PUBLIC = frozenset(
    {
        "Behavior",
        "Component",
        "action",
        "update",
        "notify",
        "go",
        "open",
        "close",
        "select",
        "confirm",
        "Op",
        "__version__",
    }
)

BANNED_PUBLIC_NAMES = frozenset(
    {
        "reply",
        "chrome",
        "glue",
        "bridge",
        "surface",
        "Effect",
        "shell",
        "Frame",
        "Main",
        "compose",
        "lower",
        "Result",
    }
)


def _in_wire_door(path: Path) -> bool:
    text = str(path).replace("\\", "/")
    return "/wire/" in text


def scan_imports(paths: Iterable[Path]) -> list[str]:
    """Return violation messages for banned core imports outside the wire door.

    Only matches real import statements (line starts with import/from),
    not docstring prose that happens to contain those substrings.
    """
    violations: list[str] = []
    for path in paths:
        if not path.is_file() or path.suffix != ".py":
            continue
        if _in_wire_door(path):
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            is_import = stripped.startswith("import ") or stripped.startswith("from ")
            if not is_import:
                continue
            for banned in BANNED_IMPORT_PREFIXES:
                if f"import {banned}" in stripped or f"from {banned}" in stripped:
                    violations.append(f"{path}:{i}: banned import of {banned}")
    return violations


def check_public_surface(exported: Iterable[str]) -> list[str]:
    """Return violations if exported names drift from the freeze list or hit bans."""
    names = set(exported)
    violations: list[str] = []
    extra = names - FROZEN_PUBLIC
    missing = FROZEN_PUBLIC - names
    banned = names & BANNED_PUBLIC_NAMES
    if extra:
        violations.append(
            f"public surface expanded without DESIGN reopen: {sorted(extra)}"
        )
    if missing:
        violations.append(f"public surface missing frozen names: {sorted(missing)}")
    if banned:
        violations.append(f"banned public names present: {sorted(banned)}")
    return violations


def doctor(package_root: Path | None = None) -> list[str]:
    """Run isolation + public-surface checks. Empty list means healthy."""
    import ux_behavior

    violations = check_public_surface(ux_behavior.__all__)
    root = package_root or Path(ux_behavior.__file__).resolve().parent
    violations.extend(scan_imports(root.rglob("*.py")))
    return violations
