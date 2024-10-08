from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout
import sys


class LyricsDisplay(QDialog):
    def __init__(self, lyrics_list, parent=None):
        super().__init__(parent)
        self.at_margin_index = None
        self.during_animation = False
        self.setWindowTitle("Lyrics Display")
        self.setFixedSize(400, 300)
        self.lyrics = lyrics_list
        self.current_index = 0
        self.animations = []  # Store active animations
        self.animation_duration = 200  # the animation duration in milliseconds

        # Create a QVBoxLayout to arrange the labels vertically
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

        # Initialize five labels for displaying lyrics context
        self.label1 = QLabel("")  # Top-most label
        self.label2 = QLabel(self.lyrics[self.current_index - 1] if self.current_index > 0 else "")  # Previous
        self.label3 = QLabel(self.lyrics[self.current_index])  # Current
        self.label4 = QLabel(self.lyrics[self.current_index + 1] if self.current_index + 1 < len(self.lyrics) else "")  # Next
        self.label5 = QLabel(self.lyrics[self.current_index + 2] if self.current_index + 2 < len(self.lyrics) else "")  # Bottom-most

        # Set styles for the labels
        self.update_labels_style()

        # Add labels to the layout
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.label3)
        self.layout.addWidget(self.label4)
        self.layout.addWidget(self.label5)

        self.set_initial_positions()

    def set_initial_positions(self):
        """Set the initial positions of all five labels."""
        # Manually set the positions of each label within the dialog
        self.label1.move(QPoint(105, 20))   # Top-most position
        self.label2.move(QPoint(105, 75))   # Previous position
        self.label3.move(QPoint(105, 137))  # Current position
        self.label4.move(QPoint(105, 199))  # Next position
        self.label5.move(QPoint(105, 261))  # Bottom-most position

    def update_labels_style(self):
        """Set styles for the five labels."""
        self.label1.setStyleSheet("color: gray; font-size: 16px;")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label2.setStyleSheet("color: gray; font-size: 16px;")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label3.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        self.label3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label4.setStyleSheet("color: gray; font-size: 16px;")
        self.label4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label5.setStyleSheet("color: gray; font-size: 16px;")
        self.label5.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, event):
        """
        Override keyPressEvent to capture arrow key presses.
        - Up arrow: move lyrics down.
        - Down arrow: move lyrics up.
        """
        if event.key() == Qt.Key.Key_Down:
            self.move_lyrics(key_press="down")
        elif event.key() == Qt.Key.Key_Up:
            self.move_lyrics(key_press="up")
        else:
            super().keyPressEvent(event)

    def move_lyrics(self, key_press="up"):
        """
        Move the lyrics up or down based on the direction.
        Update the labels accordingly and animate the change.
        """
        if self.during_animation:
            if self.at_margin_index:
                self.during_animation = False
            else:
                return

        self.during_animation = True  # Set flag to indicate animation is in progress

        self.animations.clear()

        # Determine end positions based on the movement direction
        if key_press == "up":
            print("pressed up")
            print("during animation state ", self.during_animation)
            if not self.current_index > 0:
                self.at_margin_index = True
                return
            self.at_margin_index = False
            self.label3.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from current
            self.label2.setStyleSheet("color: red; font-size: 22px; font-weight: bold;")  # Highlight above label

            # Set animation parameters for moving labels
            self.create_animations(direction="up")
            self.current_index -= 1  # Move to the previous lyric

        elif key_press == "down":
            print("pressed down")
            print("during animation state ", self.during_animation)
            if not self.current_index + 1 < len(self.lyrics):
                self.at_margin_index = True
                return
            self.at_margin_index = False
            self.label3.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from current
            self.label4.setStyleSheet("color: red; font-size: 22px; font-weight: bold;")  # Highlight below label

            # Set animation parameters for moving labels
            self.create_animations(direction="down")
            self.current_index += 1  # Move to the next lyric

        # Connect the finished signal to reset the animation flag
        self.animations[-1].finished.connect(lambda: self.reset_animation_flag())

    def reset_animation_flag(self):
        """ Reset the animation flag once animations are complete. """
        self.during_animation = False

    def create_animations(self, direction):
        """Create and start animations for the labels moving up or down."""
        # Create animations for all 5 labels
        anim_label1 = QPropertyAnimation(self.label1, b"pos")
        anim_label2 = QPropertyAnimation(self.label2, b"pos")
        anim_label3 = QPropertyAnimation(self.label3, b"pos")
        anim_label4 = QPropertyAnimation(self.label4, b"pos")
        anim_label5 = QPropertyAnimation(self.label5, b"pos")

        # Set the start positions for all labels
        anim_label1.setStartValue(self.label1.pos())
        anim_label2.setStartValue(self.label2.pos())
        anim_label3.setStartValue(self.label3.pos())
        anim_label4.setStartValue(self.label4.pos())
        anim_label5.setStartValue(self.label5.pos())

        # Define animation durations
        anim_label1.setDuration(self.animation_duration)
        anim_label2.setDuration(self.animation_duration)
        anim_label3.setDuration(self.animation_duration)
        anim_label4.setDuration(self.animation_duration)
        anim_label5.setDuration(self.animation_duration)

        # Define the end positions based on direction
        if direction == "up":
            # Move labels up
            anim_label1.setEndValue(self.label2.pos())
            anim_label2.setEndValue(self.label3.pos())
            anim_label3.setEndValue(self.label4.pos())
            anim_label4.setEndValue(self.label5.pos())
            anim_label5.setEndValue(QPoint(105, 305))  # Move label5 off the view

            # Connect animation completion to update labels
            anim_label4.finished.connect(lambda: self.update_lyrics_after_movement("up"))
        elif direction == "down":
            # Move labels down
            anim_label1.setEndValue(QPoint(105, -20))  # Move label1 off the view
            anim_label2.setEndValue(self.label1.pos())
            anim_label3.setEndValue(self.label2.pos())
            anim_label4.setEndValue(self.label3.pos())
            anim_label5.setEndValue(self.label4.pos())

            # Connect animation completion to update labels
            anim_label4.finished.connect(lambda: self.update_lyrics_after_movement("down"))

        # Add animations to the list and start them
        self.animations.extend([anim_label1, anim_label2, anim_label3, anim_label4, anim_label5])
        self.during_animation = True
        for anim in self.animations:
            anim.start()

    def update_lyrics_after_movement(self, direction):
        self.during_animation = False
        """
        Update the lyrics after the animation has finished.
        """
        # Update the label styles
        if direction == "up":
            self.label2.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from above label
        elif direction == "down":
            self.label4.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from below label

        self.label3.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")  # Reapply highlight to current

        # Update text for each label based on the current index
        self.label1.setText(self.lyrics[self.current_index - 2] if self.current_index - 2 >= 0 else "")
        self.label2.setText(self.lyrics[self.current_index - 1] if self.current_index - 1 >= 0 else "")
        self.label3.setText(self.lyrics[self.current_index])
        self.label4.setText(self.lyrics[self.current_index + 1] if self.current_index + 1 < len(self.lyrics) else "")
        self.label5.setText(self.lyrics[self.current_index + 2] if self.current_index + 2 < len(self.lyrics) else "")

        # Reset positions after the animation completes
        self.set_initial_positions()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    lyrics = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5", "Line 6", "Line 7", "Line 8", "Line 9", "Line 10"]
    window = LyricsDisplay(lyrics)
    window.show()
    sys.exit(app.exec())
