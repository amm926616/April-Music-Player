from musicplayerui import MusicPlayerUI
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # # Load and apply the QSS theme
    # with open("style.qss", "r") as style_file:
    #     app.setStyleSheet(style_file.read())

    ui = MusicPlayerUI(app)
    ui.createUI()
    sys.exit(app.exec())
