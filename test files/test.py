from PyQt6.QtWidgets import QDialog, QApplication, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class FullScreenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the dialog window
        self.setWindowTitle("Full-Screen Dialog")

        # Add a label to demonstrate content
        label = QLabel("Press Esc to exit full-screen mode", self)
        label.setStyleSheet("color: white; font-size: 24px;")
        layout = QVBoxLayout(self)
        layout.addWidget(label)

        # Add a button to toggle full-screen mode
        toggle_button = QPushButton("Toggle Full-Screen", self)
        toggle_button.clicked.connect(self.toggle_full_screen)
        layout.addWidget(toggle_button)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.exit_full_screen()
        else:
            super().keyPressEvent(event)

    def toggle_full_screen(self):
        if self.is_full_screen():
            self.exit_full_screen()
        else:
            self.showFullScreen()

    def is_full_screen(self):
        # Check if the dialog is in full-screen mode
        return self.windowState() & Qt.WindowState.WindowFullScreen

    def exit_full_screen(self):
        # Restore the dialog to windowed mode
        self.showNormal()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Create and show the dialog
    dialog = FullScreenDialog()
    dialog.show()
    sys.exit(app.exec())
