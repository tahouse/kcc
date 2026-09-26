import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from kindlecomicconverter import KCC_gui
from kindlecomicconverter.KCC_ui import Ui_mainWindow


class ProcessingControlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = QMainWindow()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self.window)
        self.controller = SimpleNamespace()
        self.gui_patch = patch.object(KCC_gui, "GUI", self.ui, create=True)
        self.gui_patch.start()

    def tearDown(self):
        self.gui_patch.stop()
        self.window.close()

    def test_disable_processing_greys_only_bypassed_controls(self):
        self.ui.rotateBox.setChecked(True)
        original_enabled_states = {
            name: getattr(self.ui, name).isEnabled()
            for name in KCC_gui.IMAGE_PROCESSING_WIDGETS
        }

        KCC_gui.KCCGUI.toggleDisableProcessing(
            self.controller, Qt.CheckState.Checked.value
        )
        KCC_gui.KCCGUI.toggleDisableProcessing(
            self.controller, Qt.CheckState.Checked.value
        )

        self.assertTrue(all(
            not getattr(self.ui, name).isEnabled()
            for name in KCC_gui.IMAGE_PROCESSING_WIDGETS
        ))
        self.assertTrue(self.ui.rotateBox.isChecked())
        self.assertTrue(self.ui.labelSpreadsButton.isEnabled())
        self.assertTrue(self.ui.mangaBox.isEnabled())
        self.assertTrue(self.ui.colorBox.isEnabled())
        self.assertTrue(self.ui.croppingBox.isEnabled())
        self.assertTrue(self.ui.keepSourceResolutionBox.isEnabled())

        KCC_gui.KCCGUI.toggleDisableProcessing(
            self.controller, Qt.CheckState.Unchecked.value
        )

        self.assertEqual(
            original_enabled_states,
            {
                name: getattr(self.ui, name).isEnabled()
                for name in KCC_gui.IMAGE_PROCESSING_WIDGETS
            },
        )
        self.assertTrue(self.ui.rotateBox.isChecked())

    def test_enabled_state_does_not_override_other_constraints(self):
        self.assertFalse(self.ui.noQuantizeBox.isEnabled())

        KCC_gui.KCCGUI.toggleDisableProcessing(
            self.controller, Qt.CheckState.Unchecked.value
        )

        self.assertFalse(self.ui.noQuantizeBox.isEnabled())


if __name__ == "__main__":
    unittest.main()
