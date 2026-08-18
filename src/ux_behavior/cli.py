"""CLI — uxbehavior doctor | new component | new action.

Not a product surface. Scaffold + fail-closed checks.
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

from ux_behavior import Component, action


class {class_name}(Component):
    id = "{component_id}"

    def render(self):
        return f"<div id='{component_id}'></div>"

    @action(caps=())
    def example(self):
        return None
'''


def _action_stub(method: str) -> str:
    return f'''
    @action(caps=())
    def {method}(self):
        """TODO: return list[Op] or mutate state for dirty projection."""
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
    _write(out, _component_stub(class_name, component_id), force=args.force)
    print(f"wrote {out}")
    return 0


def cmd_new_action(args: argparse.Namespace) -> int:
    target = args.name
    if not _ACTION.match(target):
        print(
            "action name must be Component.method (identifiers only)",
            file=sys.stderr,
        )
        return 2
    _class, method = target.split(".", 1)
    path = Path(args.file)
    if not path.is_file():
        print(f"file not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    if f"def {method}(" in text:
        print(f"method {method!r} already present in {path}", file=sys.stderr)
        return 1
    if "from ux_behavior import" in text and "action" not in text:
        text = text.replace(
            "from ux_behavior import",
            "from ux_behavior import action,",
            1,
        )
    stub = _action_stub(method)
    # Append before end of file
    if not text.endswith("\n"):
        text += "\n"
    text += stub
    path.write_text(text, encoding="utf-8")
    print(f"appended {method} to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="uxbehavior",
        description="ux-behavior tooling",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    doctor_p = sub.add_parser("doctor", help="Isolation + surface + stamp hygiene")
    doctor_p.add_argument("--fail", action="store_true")
    doctor_p.add_argument("--root", type=Path, default=None)
    doctor_p.set_defaults(func=cmd_doctor)

    new_p = sub.add_parser("new", help="Scaffold component or action")
    new_sub = new_p.add_subparsers(dest="kind", required=True)

    comp_p = new_sub.add_parser("component", help="Write a Component stub file")
    comp_p.add_argument("name", help="Class name (e.g. CartBadge)")
    comp_p.add_argument("--id", default=None, help="Component id (default: lower name)")
    comp_p.add_argument("--out", default=None, help="Output path")
    comp_p.add_argument("--force", action="store_true")
    comp_p.set_defaults(func=cmd_new_component)

    act_p = new_sub.add_parser("action", help="Append an @action method to a file")
    act_p.add_argument("name", help="Component.method (e.g. CartBadge.add)")
    act_p.add_argument("--file", required=True, help="Target .py file")
    act_p.set_defaults(func=cmd_new_action)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
