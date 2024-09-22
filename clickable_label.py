from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()  # Signal to emit on double click

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()  # Emit signal on double click
            super().mouseDoubleClickEvent(event)
