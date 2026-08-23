"""OWN — behavior must not own product CLI or Document shell."""
from __future__ import annotations

import importlib
import unittest


class TestNoProductCliSurface(unittest.TestCase):
    def test_no_create_app_module(self):
        for name in (
            "ux_behavior.cli.create_app",
            "ux_behavior.create_app",
            "ux_behavior.cli.serve",
        ):
            with self.assertRaises((ImportError, ModuleNotFoundError)):
                importlib.import_module(name)


class TestPublicSurfaceImportable(unittest.TestCase):
    def test_package_imports(self):
        mod = importlib.import_module("ux_behavior")
        self.assertTrue(len(dir(mod)) >= 0)
