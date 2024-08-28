from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent

class DoubleClickableProgressBar(QProgressBar):
    doubleClicked = pyqtSignal()  # Custom signal for double-click

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.doubleClicked.emit()  # Emit the custom double-click signal
        super().mouseDoubleClickEvent(event)  # Call the base class implementation
