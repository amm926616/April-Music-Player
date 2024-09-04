from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt


class NoteTaking():
    def __init__(self):
        self.window = QDialog()        
        self.window.keyPressEvent = self.keyPressEvent
        
    def createUI(self):
        self.window.setWindowTitle("Note Taking Window")
        self.window.setGeometry(500, 300, 400, 300)

        # Layout
        layout = QVBoxLayout()

        # Text edit area
        self.textBox = QTextEdit()
        layout.addWidget(self.textBox)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveToFile)
        layout.addWidget(saveButton)

        self.window.setLayout(layout)
        self.window.exec()

    def saveToFile(self):
        text = self.textBox.toPlainText()
        # Open a file dialog to choose the file path
        file_path = "text.txt"
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(text)
                print(f"File saved successfully to {file_path}")
            except Exception as e:
                print(f"Failed to save file: {e}")
        self.textBox.clear()
        self.window.close()
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            # Handle Ctrl + S
            print("Ctrl + S pressed")
            self.saveToFile()
