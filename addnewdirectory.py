from PyQt6.QtWidgets import (
    QFileDialog, QLabel, QPushButton,
    QVBoxLayout, QDialog, QSpinBox, QHBoxLayout
)
from PyQt6.QtGui import QFontDatabase, QIcon, QKeyEvent
from easy_json import EasyJson
from fontTools.ttLib import TTFont
from PyQt6.QtCore import Qt

class AddNewDirectory(QDialog):
    def __init__(self, parent):
        self.parent = parent 
        super().__init__(parent)
        self.ej = EasyJson()
        