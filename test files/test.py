import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Key Press Example")
        self.setGeometry(100, 100, 400, 300)

        # Create a label to display which key was pressed
        self.label = QLabel("Press any key...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)

    def keyPressEvent(self, event: QKeyEvent):
        # Check which key was pressed and update the label text
        if event.key() == Qt.Key.Key_A:
            self.label.setText("You pressed the 'A' key!")
        elif event.key() == Qt.Key.Key_Escape:
            self.label.setText("You pressed the 'Escape' key!")
        else:
            self.label.setText(f"You pressed the '{event.text()}' key!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())
