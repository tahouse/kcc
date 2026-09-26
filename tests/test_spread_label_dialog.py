import json
import os
import tempfile
import unittest

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from kindlecomicconverter.KCC_gui import hasSavedSpreadLabels, loadSpreadLabels, shouldSkipSpreadLabeling
from kindlecomicconverter.KCC_spread_label import LabelSpreadsDialog


class SpreadLabelDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_enter_accepts_without_stopping_batch(self):
        dialog = LabelSpreadsDialog(800, [], [], {}, {})
        QTimer.singleShot(0, lambda: QTest.keyClick(dialog, Qt.Key.Key_Return))

        result = dialog.exec()

        self.assertEqual(result, QDialog.DialogCode.Accepted)
        self.assertFalse(dialog.stop_requested)

    def test_stop_button_rejects_and_stops_batch(self):
        dialog = LabelSpreadsDialog(800, [], [], {}, {})
        QTimer.singleShot(0, dialog.stop_button.click)

        result = dialog.exec()

        self.assertEqual(result, QDialog.DialogCode.Rejected)
        self.assertTrue(dialog.stop_requested)

    def test_saved_spread_labels_are_loaded_and_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, 'book.epub')
            with open(source + '.json', 'w', encoding='utf-8') as sidecar:
                json.dump({'spreads': [4, 1, 4, -1, 9, '2', True]}, sidecar)

            self.assertEqual(
                loadSpreadLabels(source, 6),
                ['label-0001.png', 'label-0004.png'],
            )

    def test_missing_spread_sidecar_loads_no_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, 'book.epub')

            self.assertEqual(loadSpreadLabels(source, 6), [])
            self.assertFalse(hasSavedSpreadLabels(source))

    def test_empty_spread_sidecar_counts_as_already_labeled(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, 'book.epub')
            with open(source + '.json', 'w', encoding='utf-8') as sidecar:
                json.dump({'spreads': []}, sidecar)

            self.assertTrue(hasSavedSpreadLabels(source))
            self.assertTrue(shouldSkipSpreadLabeling(source, True, False))
            self.assertFalse(shouldSkipSpreadLabeling(source, True, True))
            self.assertFalse(shouldSkipSpreadLabeling(source, False, False))

    def test_non_object_spread_sidecar_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, 'book.epub')
            with open(source + '.json', 'w', encoding='utf-8') as sidecar:
                json.dump([1, 2], sidecar)

            with self.assertRaisesRegex(ValueError, 'JSON object'):
                loadSpreadLabels(source, 6)


if __name__ == '__main__':
    unittest.main()