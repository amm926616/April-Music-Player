from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QPushButton, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, QRect

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Create a grid layout and labels
        self.grid_layout = QGridLayout()
        self.lyric_label0 = QLabel("Lyric 0: Initial Text")
        self.lyric_label1 = QLabel("Lyric 1: Initial Text")
        self.lyric_label2 = QLabel("Lyric 2: Initial Text")
        self.lyric_label3 = QLabel("Lyric 3: Initial Text")
        self.lyric_label4 = QLabel("Lyric 4: Initial Text")

        # Add labels to the grid layout
        self.grid_layout.addWidget(self.lyric_label0, 0, 0)
        self.grid_layout.addWidget(self.lyric_label1, 1, 0)
        self.grid_layout.addWidget(self.lyric_label2, 2, 0)
        self.grid_layout.addWidget(self.lyric_label3, 3, 0)
        self.grid_layout.addWidget(self.lyric_label4, 4, 0)

        # Store the labels in a list for easier management
        self.labels = [self.lyric_label0, self.lyric_label1, self.lyric_label2,
                       self.lyric_label3, self.lyric_label4]

        # Create a button to start the animation
        self.animate_button = QPushButton("Animate Labels")
        self.animate_button.clicked.connect(self.animate_labels)

        # Set up the main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.grid_layout)
        main_layout.addWidget(self.animate_button)

    def animate_labels(self):
        """Animate labels to create the effect of shifting lyrics upwards."""
        animations = []

        # Iterate through the labels in reverse order to set up the animation
        for i in range(len(self.labels) - 1, 0, -1):
            current_label = self.labels[i]
            target_label = self.labels[i - 1]

            # Create an animation to move the current label to the target label's position
            animation = QPropertyAnimation(current_label, b"geometry")
            animation.setDuration(500)  # Duration of 500 milliseconds
            animation.setStartValue(current_label.geometry())
            animation.setEndValue(target_label.geometry())
            animation.start()

            # Store the animation reference to prevent garbage collection
            animations.append(animation)

        # Create an animation to move label0 off the screen
        disappearing_label = self.labels[0]
        animation0 = QPropertyAnimation(disappearing_label, b"geometry")
        animation0.setDuration(500)
        animation0.setStartValue(disappearing_label.geometry())
        animation0.setEndValue(QRect(disappearing_label.geometry().x(), -disappearing_label.height(),
                                     disappearing_label.width(), disappearing_label.height()))
        animation0.start()
        animations.append(animation0)

        # Connect to the last animation's finished signal to update text
        animation0.finished.connect(self.update_last_label)

        # Save the animations to an instance variable to prevent garbage collection
        self.animations = animations

    def update_last_label(self):
        """Update the text of the last label after animation completes."""
        # Update the text of the last label (label4)
        self.labels[-1].setText("Lyric 4: New text after animation.")

        # Restore the geometry of label0 to its original position
        self.lyric_label0.setGeometry(self.grid_layout.cellRect(0, 0))  # Restore label0's geometry

        # Rearrange the label references to reflect the change
        self.labels.insert(len(self.labels), self.labels.pop(0))

# Create the application and main window
app = QApplication([])
window = MainWindow()
window.setWindowTitle("Lyrics Shift Animation")
window.show()

# Run the application loop
app.exec()
