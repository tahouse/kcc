import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kindlecomicconverter import startup


class StartupEnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.original_value = os.environ.pop("KCC_SHOW_SUPPORT_CONTENT", None)

    def tearDown(self):
        os.environ.pop("KCC_SHOW_SUPPORT_CONTENT", None)
        if self.original_value is not None:
            os.environ["KCC_SHOW_SUPPORT_CONTENT"] = self.original_value

    def test_frozen_app_loads_bundled_environment(self):
        with tempfile.TemporaryDirectory() as executable_directory, tempfile.TemporaryDirectory() as bundle_directory:
            Path(bundle_directory, ".env").write_text("KCC_SHOW_SUPPORT_CONTENT=0\n", encoding="utf-8")

            with patch.object(startup.sys, "frozen", True, create=True), \
                    patch.object(startup.sys, "executable", str(Path(executable_directory, "KCC.exe"))), \
                    patch.object(startup.sys, "_MEIPASS", bundle_directory, create=True):
                startup.loadEnvironment()

        self.assertEqual("0", os.environ["KCC_SHOW_SUPPORT_CONTENT"])

    def test_external_environment_overrides_bundled_default(self):
        with tempfile.TemporaryDirectory() as executable_directory, tempfile.TemporaryDirectory() as bundle_directory:
            Path(executable_directory, ".env").write_text("KCC_SHOW_SUPPORT_CONTENT=1\n", encoding="utf-8")
            Path(bundle_directory, ".env").write_text("KCC_SHOW_SUPPORT_CONTENT=0\n", encoding="utf-8")

            with patch.object(startup.sys, "frozen", True, create=True), \
                    patch.object(startup.sys, "executable", str(Path(executable_directory, "KCC.exe"))), \
                    patch.object(startup.sys, "_MEIPASS", bundle_directory, create=True):
                startup.loadEnvironment()

        self.assertEqual("1", os.environ["KCC_SHOW_SUPPORT_CONTENT"])


if __name__ == "__main__":
    unittest.main()
