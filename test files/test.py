import sys
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the dialog
        self.setWindowTitle("Key Press Example in QDialog")
        self.setGeometry(100, 100, 300, 200)

        # Create a label to display which key was pressed
        self.label = QLabel("Press any key...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def keyPressEvent(self, event: QKeyEvent):
        # Handle key presses here
        if event.key() == Qt.Key.Key_A:
            self.label.setText("You pressed the 'A' key!")
        elif event.key() == Qt.Key.Key_Left:
            self.label.setText("You pressed the 'Left Arrow' key!")
        elif event.key() == Qt.Key.Key_Right:
            self.label.setText("You pressed the 'Right Arrow' key!")
        elif event.key() == Qt.Key.Key_Escape:
            self.close()  # Close the dialog when Escape is pressed
        else:
            self.label.setText(f"You pressed the '{event.text()}' key!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show the custom dialog
    dialog = CustomDialog()
    dialog.exec()
    
    sys.exit(app.exec())
