import sys
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout


class LyricsDisplay(QDialog):
    def __init__(self, lyrics, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lyrics Display")
        self.setFixedSize(400, 300)
        self.lyrics = lyrics
        self.current_index = 0

        # Create a QVBoxLayout to arrange the labels vertically
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

        # Initialize three labels for displaying the previous, current, and next lyrics
        self.previous_label = QLabel(self.lyrics[self.current_index - 1] if self.current_index > 0 else "")
        self.current_label = QLabel(self.lyrics[self.current_index])
        self.next_label = QLabel(
            self.lyrics[self.current_index + 1] if self.current_index + 1 < len(self.lyrics) else "")

        # Set styles for the labels
        self.update_labels_style()

        # Add labels to the layout
        self.layout.addWidget(self.previous_label)
        self.layout.addWidget(self.current_label)
        self.layout.addWidget(self.next_label)

        self.set_initial_positions()

    def set_initial_positions(self):
        """Set the initial positions of the previous, current, and next labels."""
        # Manually set the positions of each label within the dialog
        self.previous_label.move(105, 50)  # Top position
        self.current_label.move(105, 137)  # Center position
        self.next_label.move(105, 224)     # Bottom position

    def update_labels_style(self):
        """Set styles for the previous, current, and next labels."""
        self.previous_label.setStyleSheet("color: gray; font-size: 16px;")
        self.previous_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_label.setStyleSheet("color: red; font-size: 18px; font-weight: bold;")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_label.setStyleSheet("color: gray; font-size: 16px;")
        self.next_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, event):
        """
        Override keyPressEvent to capture arrow key presses.
        - Up arrow: move lyrics down.
        - Down arrow: move lyrics up.
        """
        if event.key() == Qt.Key.Key_Up:
            self.move_lyrics(direction="down")
        elif event.key() == Qt.Key.Key_Down:
            self.move_lyrics(direction="up")
        else:
            super().keyPressEvent(event)

    def move_lyrics(self, direction="up"):
        """
        Move the lyrics up or down based on the direction.
        Update the labels accordingly and animate the change.
        """
        # Create the animations
        anim_current = QPropertyAnimation(self.current_label, b"pos")
        anim_previous = QPropertyAnimation(self.previous_label, b"pos")
        anim_next = QPropertyAnimation(self.next_label, b"pos")

        # Extract the positions of the labels
        previous_pos = self.current_label.pos()
        current_pos = self.current_label.pos()
        next_pos = self.current_label.pos()

        print("previous pos ", previous_pos)
        print("current pos", current_pos)
        print("next pos", next_pos)

        # Set the starting positions for all animations
        anim_current.setStartValue(current_pos)
        anim_previous.setStartValue(previous_pos)
        anim_next.setStartValue(next_pos)

        # Determine the end positions based on the movement direction
        if direction == "up" and self.current_index + 1 < len(self.lyrics):
            print("direction up")
            # Move the current label to the top position
            anim_current.setEndValue(self.previous_label.pos())

            # Move the next label to the center position
            anim_next.setEndValue(self.current_label.pos())

            # Previous label stays in its current position
            anim_previous.setEndValue(self.previous_label.pos())

            # Update the current index and labels after movement
            self.current_index += 1

        elif direction == "down" and self.current_index > 0:
            print("direction down")
            # Move the current label to the bottom position
            anim_current.setEndValue(self.next_label.pos())

            # Move the previous label to the center position
            anim_previous.setEndValue(self.current_label.pos())

            # Next label stays in its current position
            anim_next.setEndValue(self.next_label.pos())

            # Update the current index and labels after movement
            self.current_index -= 1

        else:
            return

        # Set the duration for all animations
        anim_current.setDuration(3000)
        anim_previous.setDuration(3000)
        anim_next.setDuration(3000)

        # Start all animations
        anim_current.start()
        anim_previous.start()
        anim_next.start()

        # Update the styles after moving the lyrics
        self.update_lyrics_after_movement()
        self.update_labels_style()

    def update_lyrics_after_movement(self):
        """Update the lyrics' text based on the current index."""
        self.previous_label.setText(self.lyrics[self.current_index - 1] if self.current_index > 0 else "")
        self.current_label.setText(self.lyrics[self.current_index])
        self.next_label.setText(
            self.lyrics[self.current_index + 1] if self.current_index + 1 < len(self.lyrics) else "")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    lyrics_list = [
        "First line of the song",
        "Second line of the song",
        "Third line of the song",
        "Fourth line of the song",
        "Fifth line of the song",
        "Sixth line of the song",
        "Seventh line of the song",
        "Eighth line of the song",
        "Ninth line of the song",
        "Tenth line of the song"
    ]

    # Create an instance of the LyricsDisplay dialog
    dialog = LyricsDisplay(lyrics_list)
    dialog.show()

    sys.exit(app.exec())
