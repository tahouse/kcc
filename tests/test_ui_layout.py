import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def find_grid_overlaps(root, ui_name):
    overlaps = []

    for layout in root.iterfind('.//layout[@class="QGridLayout"]'):
        occupied = {}
        for item in layout.findall("./item"):
            row = int(item.get("row", 0))
            column = int(item.get("column", 0))
            row_span = int(item.get("rowspan", 1))
            column_span = int(item.get("colspan", 1))
            child = next(iter(item), None)
            child_name = child.get("name", "unnamed") if child is not None else "unnamed"

            for cell_row in range(row, row + row_span):
                for cell_column in range(column, column + column_span):
                    cell = (cell_row, cell_column)
                    if cell in occupied:
                        overlaps.append(
                            f"{ui_name}:{layout.get('name')} cell {cell} is shared by "
                            f"{occupied[cell]} and {child_name}"
                        )
                    else:
                        occupied[cell] = child_name

    return overlaps


class UiGridLayoutTest(unittest.TestCase):
    def test_grid_layout_cells_do_not_overlap(self):
        overlaps = []

        for ui_path in sorted((REPOSITORY_ROOT / "gui").glob("*.ui")):
            root = ElementTree.parse(ui_path).getroot()
            overlaps.extend(find_grid_overlaps(root, ui_path.name))

        self.assertEqual([], overlaps, "\n".join(overlaps))

    def test_overlap_detector_reports_reused_cells(self):
        root = ElementTree.fromstring(
            """<ui><layout class="QGridLayout" name="settingsGrid">
            <item row="2" column="1"><widget name="firstWidget"/></item>
            <item row="2" column="1"><widget name="secondWidget"/></item>
            </layout></ui>"""
        )

        self.assertEqual(
            [
                "example.ui:settingsGrid cell (2, 1) is shared by "
                "firstWidget and secondWidget"
            ],
            find_grid_overlaps(root, "example.ui"),
        )


if __name__ == "__main__":
    unittest.main()
