#!  usr/bin/env python

from musicplayerui import MusicPlayerUI
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MusicPlayerUI()
    ui.createUI()
    sys.exit(app.exec())
