"""CLI — uxbehavior doctor.

Not a product surface. Fail-closed checks for isolation and frozen public API.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="uxbehavior",
        description="ux-behavior tooling",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    doctor_p = sub.add_parser(
        "doctor",
        help="Run isolation + public-surface checks (empty = healthy)",
    )
    doctor_p.add_argument(
        "--fail",
        action="store_true",
        help="Exit 1 when violations are found (default: always exit 0 after print)",
    )
    doctor_p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Optional package root to scan (defaults to installed package)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "doctor":
        from ux_behavior.isolation import doctor

        violations = doctor(package_root=args.root)
        if not violations:
            print("ux-behavior doctor: ok")
            return 0
        print("ux-behavior doctor: FAIL")
        for v in violations:
            print(f"  - {v}")
        return 1 if args.fail else 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
