"""CLI — uxbehavior doctor | new component | new action.

Scaffold + fail-closed package checks. Not a product runtime surface.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ACTION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")


def _component_stub(class_name: str, component_id: str) -> str:
    return f'''from __future__ import annotations

from ux_behavior import Component, MorphState, action


class {class_name}(Component):
    id = "{component_id}"

    def render(self):
        return f"<div id='{component_id}'></div>"

    @action(caps=())
    def example(self):
        """Public action — mutate MorphState and/or return list[Op]."""
        return None
'''


def _action_stub(method: str) -> str:
    return f'''
    @action(caps=())
    def {method}(self):
        """Public action — mutate MorphState and/or return list[Op]."""
        return None
'''


def _write(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {path} (use --force)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def cmd_doctor(args: argparse.Namespace) -> int:
    from ux_behavior.isolation import doctor

    violations = doctor(package_root=args.root)
    if not violations:
        print("ux-behavior doctor: ok")
        return 0
    print("ux-behavior doctor: FAIL")
    for v in violations:
        print(f"  - {v}")
    return 1 if args.fail else 0


def cmd_new_component(args: argparse.Namespace) -> int:
    name = args.name
    if not _IDENT.match(name):
        print(f"invalid component class name: {name!r}", file=sys.stderr)
        return 2
    class_name = name if name[0].isupper() else name[:1].upper() + name[1:]
    component_id = args.id or class_name.lower()
    out = Path(args.out or f"{component_id.replace('.', '_')}.py")
    try:
        _write(out, _component_stub(class_name, component_id), force=args.force)
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0


def cmd_new_action(args: argparse.Namespace) -> int:
    spec = args.spec
    if not _ACTION.match(spec):
        print(
            f"invalid action spec {spec!r} (expected Component.method)",
            file=sys.stderr,
        )
        return 2
    _, method = spec.split(".", 1)
    out_s = getattr(args, "file", None) or getattr(args, "out", None) or "actions_stub.py"
    out = Path(out_s)
    try:
        if out.exists() and not args.force:
            text = out.read_text(encoding="utf-8")
            if f"def {method}(" in text:
                print(f"action {method!r} already in {out}", file=sys.stderr)
                return 1
            out.write_text(text.rstrip() + "\n" + _action_stub(method), encoding="utf-8")
        else:
            _write(
                out,
                "from ux_behavior import action\n" + _action_stub(method),
                force=args.force,
            )
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"wrote {method} -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="uxbehavior", description="ux-behavior tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="isolation / package health check")
    d.add_argument("--root", default=None, help="package root to scan")
    d.add_argument("--fail", action="store_true", help="exit 1 on violations")
    d.set_defaults(func=cmd_doctor)

    nc = sub.add_parser("new", help="scaffold")
    nc_sub = nc.add_subparsers(dest="what", required=True)

    c = nc_sub.add_parser("component", help="new Component file")
    c.add_argument("name", help="class name")
    c.add_argument("--id", default=None, help="component id (default: lower name)")
    c.add_argument("--out", default=None, help="output path")
    c.add_argument("--force", action="store_true")
    c.set_defaults(func=cmd_new_component)

    a = nc_sub.add_parser("action", help="append action stub")
    a.add_argument("spec", help="Component.method")
    a.add_argument("--out", default=None, help="output path")
    a.add_argument("--file", default=None, help="alias for --out (append into file)")
    a.add_argument("--force", action="store_true")
    a.set_defaults(func=cmd_new_action)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
