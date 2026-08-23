"""OWN/REG — ux-behavior ownership and isolation (library-tailored).

ux-behavior owns: Behavior, Component, @action, MorphState, ops.
CLI is doctor | new component | new action only — not product lifecycle.
Public surface must not expose Channel/CEK/app-layer product names.
"""
from __future__ import annotations

import importlib
import unittest

import ux_behavior
from ux_behavior.cli import main as cli_main
from ux_behavior.isolation import BANNED_PUBLIC_NAMES, BANNED_IMPORT_PREFIXES


class TestCliIsScaffoldNotProduct(unittest.TestCase):
    def test_no_product_cli_submodules(self):
        for banned in ("create_app", "serve", "deploy", "tunnel"):
            with self.assertRaises((ImportError, ModuleNotFoundError)):
                importlib.import_module(f"ux_behavior.cli.{banned}")

    def test_doctor_exit_zero(self):
        self.assertEqual(cli_main(["doctor"]), 0)

    def test_product_verb_rejected(self):
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["create-app", "x"])
        self.assertNotEqual(ctx.exception.code, 0)


class TestPublicSurfaceOwnership(unittest.TestCase):
    def test_core_behavior_symbols_present(self):
        for core in ("Behavior", "Component", "action", "MorphState", "Op", "update"):
            self.assertIn(core, ux_behavior.__all__)
            self.assertTrue(hasattr(ux_behavior, core))

    def test_product_and_app_layer_leaks_absent(self):
        names = set(ux_behavior.__all__)
        for leak in (
            "create_app",
            "serve",
            "deploy",
            "Channel",
            "Intent",
            "App",
            "Result",
            "compose",
            "lower",
        ):
            self.assertNotIn(leak, names)
        for name in BANNED_PUBLIC_NAMES:
            self.assertNotIn(name, names)

    def test_banned_import_prefixes_include_channel(self):
        joined = " ".join(BANNED_IMPORT_PREFIXES)
        self.assertIn("ux_channel", joined)
        self.assertTrue(any(p.startswith("cek") for p in BANNED_IMPORT_PREFIXES))
