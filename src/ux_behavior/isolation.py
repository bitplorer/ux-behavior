"""Isolation and public-surface freeze + doctor."""

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

FROZEN_PUBLIC = frozenset(
    {
        "Behavior",
        "Component",
        "action",
        "update",
        "notify",
        "go",
        "submit_outcome",
        "open",
        "close",
        "select",
        "confirm",
        "MorphState",
        "RefState",
        "UiState",
        "PrefState",
        "KeepState",
        "DictBackend",
        "StateAPI",
        "follow_up",
        "Continuation",
        "BehaviorError",
        "AuthorityError",
        "ContinuationError",
        "ValidationError",
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
        "form_result",
        "Badge",
        "App",
        "Session",
        "Client",
        "Store",
        "Transient",
        "Sealed",
        "SessionState",
        "ClientState",
        "StoreState",
        "TransientState",
        "set_plane_backend",
    }
)

BANNED_SOURCE_TOKENS = frozenset(
    {
        "form_result",
        "open_overlay",
        "close_overlay",
        "glue.js",
        "lower_morph",
    }
)


def _in_wire_door(path: Path) -> bool:
    return "/wire/" in str(path).replace("\\", "/")


def scan_imports(paths: Iterable[Path]) -> list[str]:
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


def scan_banned_tokens(paths: Iterable[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.is_file() or path.suffix != ".py":
            continue
        if path.name == "isolation.py":
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for token in BANNED_SOURCE_TOKENS:
                if token in stripped:
                    violations.append(f"{path}:{i}: banned token {token!r}")
    return violations


def check_public_surface(exported: Iterable[str]) -> list[str]:
    names = set(exported)
    violations: list[str] = []
    extra = names - FROZEN_PUBLIC
    missing = FROZEN_PUBLIC - names
    banned = names & BANNED_PUBLIC_NAMES
    if extra:
        violations.append(f"public surface expanded without DESIGN reopen: {sorted(extra)}")
    if missing:
        violations.append(f"public surface missing frozen names: {sorted(missing)}")
    if banned:
        violations.append(f"banned public names present: {sorted(banned)}")
    return violations


def check_stamp_hygiene() -> list[str]:
    from ux_behavior.domains import default_table

    violations: list[str] = []
    table = default_table()
    for ns, name in sorted(table.stamp):
        if "." in name:
            violations.append(f"stamped pair {ns}.{name} has dotted name")
        if not ns or not name:
            violations.append(f"stamped pair has empty ns/name: {(ns, name)!r}")
    required = {
        ("kv", "set"),
        ("ui.dom", "morph"),
        ("log", "append"),
        ("nav", "push"),
    }
    missing = required - set(table.stamp)
    if missing:
        violations.append(f"default stamp missing S pairs: {sorted(missing)}")
    return violations


def doctor(package_root: Path | None = None) -> list[str]:
    import ux_behavior

    violations = check_public_surface(ux_behavior.__all__)
    violations.extend(check_stamp_hygiene())
    root = package_root or Path(ux_behavior.__file__).resolve().parent
    paths = list(root.rglob("*.py"))
    violations.extend(scan_imports(paths))
    violations.extend(scan_banned_tokens(paths))
    return violations
