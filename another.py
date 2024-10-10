import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QPushButton
from PyQt6.QtCore import QPropertyAnimation, QRect, Qt

class AnimatedGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QLabel Animation Example")
        self.setGeometry(100, 100, 600, 400)
        
        # Set up the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Create labels and add them to the layout
        self.labels = []
        for row in range(3):
            for col in range(3):
                label = QLabel(f"Label {row * 3 + col + 1}", self)
                label.setStyleSheet("background-color: lightblue; border: 1px solid black; padding: 10px;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.labels.append(label)
                self.layout.addWidget(label, row, col)

        # Button to trigger animation
        self.animate_button = QPushButton("Animate Labels", self)
        self.animate_button.clicked.connect(self.animate_labels)
        self.layout.addWidget(self.animate_button, 3, 0, 1, 3)  # Span across 3 columns

    def animate_labels(self):
        # Create animations for each label
        for index, label in enumerate(self.labels):
            animation = QPropertyAnimation(label, b"geometry")
            # Original position
            original_geometry = label.geometry()
            # New position (moving down and right)
            new_geometry = QRect(original_geometry.x() + 50, original_geometry.y() + 50, original_geometry.width(), original_geometry.height())
            
            animation.setStartValue(original_geometry)
            animation.setEndValue(new_geometry)
            animation.setDuration(1000)  # 1 second duration
            animation.start()

            # Update layout to prevent reset during animation
            label.setGeometry(original_geometry)  # Set the geometry to original before animating

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnimatedGrid()
    window.show()
    sys.exit(app.exec())
