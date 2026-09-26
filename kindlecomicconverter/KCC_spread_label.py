import os

from PySide6.QtCore import (QSize, Qt)
from PySide6.QtGui import (QColor, QFont, QIcon, QKeyEvent, QPainter, QPen, QPixmap)
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSlider, QSpinBox, QVBoxLayout
)

class LabelSpreadsDialog(QDialog):
    def __init__(self, available_height, images, spreads, match_scores, preview_guides, pair_offset=0,
                 preview_percent=20, match_threshold=0, parent=None):
        super().__init__(parent)
        self.index = 0
        self.all_images = images
        self.images = []
        self.spreads = spreads
        self.match_scores = match_scores
        self.preview_guides = preview_guides
        self.preview_percent = preview_percent
        self.stop_requested = False

        self.setWindowTitle("TODO: Filename goes here")
        # self.setGeometry(APP.primaryScreen().availableGeometry())
        # self.setMaximumSize(APP.primaryScreen().availableSize())
        self.available_height = available_height

        layout = QVBoxLayout()
        self.setLayout(layout)

        controls = QHBoxLayout()
        layout.addLayout(controls)

        controls.addWidget(QLabel("Preview width:"))
        self.preview_slider = QSlider(Qt.Orientation.Horizontal)
        self.preview_slider.setRange(5, 100)
        self.preview_slider.setValue(self.preview_percent)
        self.preview_slider.setTickInterval(5)
        self.preview_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.preview_slider.valueChanged.connect(self.previewWidthChanged)
        controls.addWidget(self.preview_slider)
        self.preview_input = QSpinBox()
        self.preview_input.setRange(5, 100)
        self.preview_input.setSuffix("%")
        self.preview_input.setValue(self.preview_percent)
        self.preview_input.valueChanged.connect(self.preview_slider.setValue)
        controls.addWidget(self.preview_input)

        controls.addWidget(QLabel("Match threshold:"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 1000)
        self.threshold_slider.setValue(match_threshold)
        self.threshold_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.threshold_slider.setToolTip("Minimum dark and light pixel share on both inner page edges")
        self.threshold_slider.valueChanged.connect(self.filterChanged)
        controls.addWidget(self.threshold_slider)
        self.threshold_input = QDoubleSpinBox()
        self.threshold_input.setRange(0, 10)
        self.threshold_input.setDecimals(2)
        self.threshold_input.setSingleStep(0.05)
        self.threshold_input.setSuffix("%")
        self.threshold_input.setValue(match_threshold / 100)
        self.threshold_input.valueChanged.connect(
            lambda value: self.threshold_slider.setValue(round(value * 100))
        )
        controls.addWidget(self.threshold_input)

        controls.addWidget(QLabel("Pairing:"))
        self.offset_input = QComboBox()
        self.offset_input.addItems(["Pages 1-2, 3-4, ...", "Pages 2-3, 4-5, ..."])
        self.offset_input.setCurrentIndex(pair_offset)
        self.offset_input.setToolTip(
            "Choose which pages form candidate pairs. Spread shift only sets the initial choice."
        )
        self.offset_input.currentIndexChanged.connect(self.filterChanged)
        controls.addWidget(self.offset_input)

        self.show_all = QCheckBox("Show all for offset")
        self.show_all.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.show_all.setToolTip("Ignore the match threshold for the currently selected pair offset")
        self.show_all.toggled.connect(self.filterChanged)
        controls.addWidget(self.show_all)

        content = QHBoxLayout()
        layout.addLayout(content)

        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(150, 100))
        self.thumbnail_list.setMinimumWidth(205)
        self.thumbnail_list.setMaximumWidth(225)
        self.thumbnail_list.setSpacing(4)
        self.thumbnail_list.currentRowChanged.connect(self.thumbnailSelected)
        content.addWidget(self.thumbnail_list)
        
        label = QLabel()
        label2 = QLabel()
        match_label = QLabel()
        self.label = label
        self.label2 = label2
        self.match_label = match_label
        content.addWidget(label)
        status = QVBoxLayout()
        content.addLayout(status)
        status.addWidget(match_label)
        status.addWidget(label2)
        match_font = QFont()
        match_font.setPointSize(22)
        match_font.setBold(True)
        match_label.setFont(match_font)
        match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label2.setText("not a spread")

        help_text = [
            "Cyan bands: regions sampled for matching.",
            "Red line: page split.",
            "Use arrows to change index.",
            "Use space bar to confirm spreads.",
            "Choose Pairing above; pairs update immediately.",
            "Spread shift only sets the initial pairing.",
            "Use enter key to confirm all spreads.",
            "Close window to cancel."
        ]
        buttonLabel = QLabel('\n'.join(help_text))
        content.addWidget(buttonLabel)
        self.stop_button = QPushButton("Stop Label Spreads")
        self.stop_button.clicked.connect(self.stopLabeling)
        layout.addWidget(self.stop_button, alignment=Qt.AlignmentFlag.AlignRight)
        # print(label.size())
        # print(label.maximumSize())
        # l, t, r, b = layout.getContentsMargins()
        
        #label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.filterChanged()
        #label.setScaledContents(True)
        

    def stopLabeling(self):
        self.stop_requested = True
        self.reject()
        #label2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # pixmap2 = QPixmap(images[0]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
        # label2.setPixmap(pixmap2)
        #label2.setScaledContents(True)
        #self.resize(pixmap2.width(), pixmap2.height())
    
    def filterChanged(self):
        threshold = self.threshold_slider.value() / 100
        self.threshold_input.blockSignals(True)
        self.threshold_input.setValue(threshold)
        self.threshold_input.blockSignals(False)
        current_page = os.path.basename(self.images[self.index]) if self.images else None
        offset_images = [
            image for image in self.all_images
            if int(os.path.basename(image)[6:10]) % 2 == self.offset_input.currentIndex()
        ]
        if self.show_all.isChecked():
            self.images = offset_images
        else:
            self.images = [
                image for image in offset_images
                if self.match_scores[os.path.basename(image)] > threshold
            ]
        self.index = 0
        if current_page:
            for index, image in enumerate(self.images):
                if os.path.basename(image) == current_page:
                    self.index = index
                    break
        self.rebuildThumbnails()
        self.updatePreview()

    def previewWidthChanged(self, value):
        self.preview_percent = value
        self.preview_input.blockSignals(True)
        self.preview_input.setValue(value)
        self.preview_input.blockSignals(False)
        self.updatePreview()

    def thumbnailSelected(self, row):
        if 0 <= row < len(self.images):
            self.index = row
            self.updatePreview()

    def rebuildThumbnails(self):
        self.thumbnail_list.blockSignals(True)
        self.thumbnail_list.clear()
        for image in self.images:
            page = os.path.basename(image)
            start = int(page[6:10]) + 1
            status = "SPREAD" if page in self.spreads else f"{self.match_scores[page]:.2f}%"
            item = QListWidgetItem(
                QIcon(self.guidedPixmap(image, 150)),
                f"Pages {start}/{start + 1}  {status}"
            )
            item.setToolTip(f"Pages {start}/{start + 1} - match {self.match_scores[page]:.2f}%")
            self.thumbnail_list.addItem(item)
        if self.images:
            self.thumbnail_list.setCurrentRow(self.index)
        self.thumbnail_list.blockSignals(False)

    def guidedPixmap(self, image, width=None):
        pixmap = QPixmap(image)
        original_width = pixmap.width()
        if width:
            pixmap = pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
        scale = pixmap.width() / original_width
        guides = self.preview_guides[os.path.basename(image)]
        painter = QPainter(pixmap)
        match_color = QColor(0, 210, 255, 90)
        for original_start, original_end in (guides['left_match'], guides['right_match']):
            start = round(original_start * scale)
            end = round(original_end * scale)
            painter.fillRect(start, 0, max(1, end - start), pixmap.height(), match_color)
            painter.setPen(QPen(QColor(0, 170, 220), max(1, round(2 * scale))))
            painter.drawRect(start, 0, max(1, end - start), pixmap.height() - 1)
        split = round(guides['split'] * scale)
        painter.setPen(QPen(QColor(255, 50, 50), max(2, round(5 * scale))))
        painter.drawLine(split, 0, split, pixmap.height())
        painter.end()
        return pixmap

    def updatePreview(self):
        if not self.images:
            self.label.clear()
            self.match_label.setText("No match")
            self.label2.setText("No pairs match the current threshold")
            return
        image = self.images[self.index]
        page = os.path.basename(image)
        score = self.match_scores[page]
        self.match_label.setText(f"{score:.2f}% MATCH")
        self.label2.setText(
            f"{'spread' if page in self.spreads else 'not a spread'}\n"
            f"Pair {self.index + 1}/{len(self.images)}"
        )
        pixmap = self.guidedPixmap(image)
        crop_width = max(1, int(pixmap.width() * self.preview_percent / 100))
        crop_x = (pixmap.width() - crop_width) // 2
        pixmap = pixmap.copy(crop_x, 0, crop_width, pixmap.height())
        self.label.setPixmap(pixmap.scaledToHeight(int(self.available_height * 0.8)))
        self.thumbnail_list.blockSignals(True)
        self.thumbnail_list.setCurrentRow(self.index)
        current_item = self.thumbnail_list.currentItem()
        if current_item:
            self.thumbnail_list.scrollToItem(current_item)
        self.thumbnail_list.blockSignals(False)

    def keyReleaseEvent(self, event):
        # t = 20
        # b = 20
        if isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_Left:
                self.index = max(0, self.index - 1)
                self.updatePreview()
                # pixmap2 = QPixmap(images[self.index]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
                # self.label2.setPixmap(pixmap2)
            elif event.key() == Qt.Key.Key_Right:
                self.index = min(self.index + 1, len(self.images) - 1)
                self.updatePreview()
                # pixmap2 = QPixmap(images[self.index]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
                # self.label2.setPixmap(pixmap2)
            elif event.key() == Qt.Key.Key_Space:
                if not self.images:
                    return
                page = os.path.basename(self.images[self.index])
                if page not in self.spreads:
                    page_index = int(page[6:10])
                    self.spreads[:] = [
                        spread for spread in self.spreads
                        if abs(int(spread[6:10]) - page_index) > 1
                    ]
                    self.spreads.append(page)
                else:
                    self.spreads.remove(page)
                self.rebuildThumbnails()
                self.updatePreview()
            elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.accept()
            else:
                super().keyReleaseEvent(event)
        else:
            super().keyReleaseEvent(event)