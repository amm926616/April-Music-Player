import bisect
import re
import os
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QDialog, QVBoxLayout, QApplication, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt6.QtGui import QIcon, QKeyEvent, QColor
from getfont import GetFont
from easy_json import EasyJson
from PIL import Image, ImageDraw, ImageFont
from notetaking import NoteTaking
from clickable_label import ClickableLabel
import threading
from dictionary import VocabularyManager


def extract_time_and_lyric(line):
    match = re.match(r'\[(\d{2}:\d{2}\.\d+)](.*)', line)
    if match:
        time_str = match.group(1)
        lyric = match.group(2).strip()
        return time_str, lyric
    return None, None


def convert_time_to_seconds(time_str):
    minutes, seconds = map(float, time_str.split(":"))
    return minutes * 60 + seconds


class LRCSync:
    def __init__(self, parent, music_player, config_path, on_off_lyrics=None, ui_show_maximized=None):
        self.dialog_width = None
        self.dialog_height = None
        self.first_time_update_text = True
        self.during_animation = False
        self.animations = []
        self.animation_duration = 200
        self.uiShowMaximized = ui_show_maximized
        self.on_off_lyrics = on_off_lyrics
        self.parent = parent
        self.config_path = config_path
        self.ej = EasyJson()
        self.lrc_display = None
        self.file = None
        self.music_file = None
        self.music_player = music_player

        # lyrics labels
        self.lyric_label1 = None
        self.lyric_label2 = None
        self.lyric_label3 = None
        self.lyric_label4 = None
        self.lyric_label5 = None

        self.lyrics = None
        self.lyrics_keys = None
        self.current_time = 0.0
        self.media_font = GetFont(13)
        self.media_lyric = ClickableLabel()
        self.media_lyric.setWordWrap(True)
        self.lrc_font = GetFont(int(self.ej.get_value("lrc_font_size")))
        self.show_lyrics = self.ej.get_value("show_lyrics")
        self.dictionary = None

        self.lyric_label1_text = None
        self.lyric_label3_text = None
        self.lyric_label4_text = None
        self.lyric_label2_text = None
        self.lyric_label5_text = None

        if self.show_lyrics:
            self.lyric_label3_text = "April Music Player"
        else:
            self.lyric_label3_text = "Lyrics Disabled"

        self.media_lyric.setText(self.media_font.get_formatted_text(self.lyric_label3_text))

        self.lyric_sync_connected = None
        self.media_sync_connected = None
        self.current_lyrics_time = 0.0
        self.last_update_time = 0.0  # Initialize with 0 or None
        self.update_interval = float(self.ej.get_value("sync_threshold"))  # Minimum interval in seconds
        self.script_path = os.path.dirname(os.path.abspath(__file__))
        self.previous_index = 0
        self.current_index = 0

        # Construct the full path to the icon file
        self.icon_path = os.path.join(self.script_path, 'icons', 'april-icon.png')
        self.notetaking = NoteTaking(self)
        self.started_player = False

    def disconnect_syncing(self):
        if self.lyric_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
            self.lyric_sync_connected = False
        if self.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_media_lyric)
            self.media_sync_connected = False

    def update_file_and_parse(self, file):
        if file is None:
            pass
        else:
            self.file = file

        self.parse_lrc()

    def resizeBackgroundImage(self, image_path):
        print("In resize Image method")
        image = Image.open(image_path)

        # Get the screen geometry
        app = QApplication.instance() or QApplication([])
        screen_geometry = app.primaryScreen().geometry()

        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Calculate the new dimensions to maintain the aspect ratio
        aspect_ratio = image.width / image.height
        new_width = int(screen_height * aspect_ratio)

        # Resize the image
        resized_image = image.resize((new_width, screen_height), Image.LANCZOS)

        # Create a new image with the screen dimensions and background color
        background_color = "black"  # Set your background color here
        final_image = Image.new("RGB", (screen_width, screen_height), background_color)

        # Calculate the position to paste the resized image onto the background
        x_position = (screen_width - new_width) // 2
        y_position = 0  # Keep the image vertically centered

        # Paste the resized image onto the background
        final_image.paste(resized_image, (x_position, y_position))

        # Add copyright text to the final image
        draw = ImageDraw.Draw(final_image)

        # Load a custom font with a specific size
        font_size = int(self.parent.height() * 0.06)  # Set your desired font size here
        font_path = os.path.join(self.script_path, "fonts",
                                 "Sexy Beauty.ttf")  # Replace with the path to your .ttf font file
        font = ImageFont.truetype(font_path, font_size)  # Load the font with the specified size

        # Define the text
        text = "April Music Player"

        # Get text size using text-box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Define the position for the text (bottom-right corner with padding)
        text_position = (screen_width - text_width - 10, screen_height - text_height - 10)

        # Define the stroke width and stroke color
        stroke_width = 2  # Adjust the stroke width as needed
        stroke_color = "black"  # Stroke color (outline)

        # Draw the stroke by drawing the text multiple times with a slight offset
        for offset in range(-stroke_width, stroke_width + 1):
            if offset == 0:
                continue
            draw.text((text_position[0] + offset, text_position[1]), text, font=font, fill=stroke_color)
            draw.text((text_position[0], text_position[1] + offset), text, font=font, fill=stroke_color)
            draw.text((text_position[0] + offset, text_position[1] + offset), text, font=font, fill=stroke_color)

        # Draw the main text
        draw.text(text_position, text, font=font, fill="white")  # Main text color

        # Save the final image
        final_image_path = os.path.join(self.config_path, "resized_image.png")
        final_image.save(final_image_path)

        return final_image_path

    def startUI(self, parent, file):
        self.lrc_display = QDialog(parent)
        self.lrc_display.setWindowTitle(file)
        if file is None:
            self.lrc_display.setWindowTitle("LRC Display")

        image_path = self.ej.get_value("background_image")

        # Check if the image path is not set or the file does not exist
        if not image_path or not os.path.exists(image_path):
            self.ej.setupBackgroundImage()
            image_path = self.ej.get_value("background_image")

        resized_image_path = os.path.join(self.config_path, "resized_image.png")
        if not os.path.exists(resized_image_path):
            resized_image_path = self.resizeBackgroundImage(image_path)

        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            resized_image_path = resized_image_path.replace("\\", "/")  # တော်တော်သောက်လုပ်ရှပ်တဲ့ window

        self.lrc_display.setStyleSheet(f"""
            QDialog {{
                background-color: black;  /* Black background color */
                background-image: url({resized_image_path});
                background-repeat: no-repeat;
                background-position: center;
                background-size: 100% auto;  /* Fix the image height to the dialog's height */                
            }}
        """)

        self.lrc_display.setWindowIcon(QIcon(self.icon_path))

        # Calculate the width and height of the dialog
        self.dialog_width = int(parent.width() * 0.9)
        self.dialog_height = int(parent.height() * 0.8)

        self.lrc_display.setFixedSize(dialog_width, dialog_height)

        # Calculate the top-left position of the dialog relative to the parent widget
        relative_x = int((parent.width() - self.dialog_width) / 2)
        relative_y = int((parent.height() - self.dialog_height) / 2)

        # Convert the relative position to global screen coordinates
        global_position = parent.mapToGlobal(parent.rect().topLeft())

        # Add the relative position to the global position to get the final coordinates
        position_x = global_position.x() + relative_x
        position_y = global_position.y() + relative_y

        # Set the geometry of the dialog
        self.lrc_display.setGeometry(position_x, position_y, self.dialog_width, self.dialog_height)
        self.lrc_display.setFixedSize(self.dialog_width, self.dialog_height)

        main_layout = QVBoxLayout(self.lrc_display)
        self.setup_lyrics_labels(main_layout)

        if self.show_lyrics:
            if self.started_player:
                self.lyric_label5.setText(self.lrc_font.get_formatted_text(self.lyric_label3_text))
            else:
                self.lyric_label5.setText(self.lrc_font.get_formatted_text("April Music Player"))

            self.music_player.player.positionChanged.connect(self.update_display_lyric)
            self.lyric_sync_connected = True
        else:
            self.lyric_label5.setText(self.lrc_font.get_formatted_text("Lyrics Disabled"))

        # Properly connect the close event
        self.lrc_display.closeEvent = self.closeEvent
        self.lrc_display.keyPressEvent = self.keyPressEvent

        self.lrc_display.exec()

    def closeEvent(self, event):
        self.uiShowMaximized()
        print("QDialog closed")
        self.lyric_label1 = None
        self.lyric_label2 = None
        self.lyric_label3 = None
        self.lyric_label4 = None
        self.lyric_label5 = None
        self.lrc_display = None

        if self.lyric_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
            self.lyric_sync_connected = False

        event.accept()  # To accept the close event

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.music_player.seek_backward()

        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.music_player.pause()  # pause the music first
            if self.dictionary is None:
                self.dictionary = VocabularyManager()
            self.dictionary.exec()

        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.parent.exit_app()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.music_player.seek_forward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.music_player.play_pause_music()

        elif event.key() == Qt.Key.Key_Up:
            print("UP key pressed")
            self.go_to_previous_lyric()

        elif event.key() == Qt.Key.Key_Down:
            print("down key pressed")
            self.go_to_next_lyric()

        elif event.key() == Qt.Key.Key_D:
            if self.music_player.in_pause_state:
                self.music_player.play_pause_music()
                self.music_player.in_pause_state = False
            self.go_to_the_start_of_current_lyric()

        elif event.key() == Qt.Key.Key_E:
            print("pressing e")
            self.music_player.pause()
            self.createNoteTakingWindow()

        elif event.key() == Qt.Key.Key_Escape:
            self.lrc_display.close()

        elif event.key() == Qt.Key.Key_R:
            if self.music_player.in_pause_state:
                self.music_player.play_pause_music()
                self.music_player.in_pause_state = False
            self.music_player.player.setPosition(0)

        elif event.key() == Qt.Key.Key_F:
            print("pressed F")
            if self.is_full_screen():
                self.lrc_display.showNormal()  # Restore to normal mode
            else:
                self.lrc_display.showFullScreen()  # Enter full-screen mode

        elif event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.parent.play_previous_song()

        elif event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.parent.play_next_song()

        elif event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("disabled lyrics")
            if self.show_lyrics:
                self.on_off_lyrics(False)
                self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
                self.lyric_label5.setText(self.lrc_font.get_formatted_text("Lyrics Disabled"))
                self.lyric_sync_connected = False
            else:
                self.on_off_lyrics(True)
                self.music_player.player.positionChanged.connect(self.update_display_lyric)
                self.lyric_sync_connected = True

    def createNoteTakingWindow(self):
        self.notetaking.createUI()

    def is_full_screen(self):
        # Check if the dialog is in full-screen mode

        current_window_state = self.lrc_display.windowState()

        # Define the full-screen flag
        full_screen_flag = Qt.WindowState.WindowFullScreen

        # Check if the current window state includes the full-screen flag
        is_full_screen_mode = (current_window_state & full_screen_flag) == full_screen_flag

        # Return the result
        return is_full_screen_mode

    def set_initial_positions(self):
        """Set the initial positions of all five labels."""
        self.lyric_label1.move(QPoint(105, 20))   # Top-most position
        self.lyric_label2.move(QPoint(105, 75))   # Previous position
        self.lyric_label3.move(QPoint(105, 137))  # Current position
        self.lyric_label4.move(QPoint(105, 199))  # Next position
        self.lyric_label5.move(QPoint(105, 261))  # Bottom-most position

    def setup_lyrics_labels(self, main_layout):
        self.lyric_label1 = QLabel()
        self.lyric_label1.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label1.setWordWrap(True)
        self.lyric_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label1
        self.lyric_label2 = QLabel()
        self.lyric_label2.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label2.setWordWrap(True)
        self.lyric_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label2
        self.lyric_label3 = QLabel()
        self.lyric_label3.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label3.setWordWrap(True)
        self.lyric_label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label3
        self.lyric_label4 = QLabel()
        self.lyric_label4.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label4.setWordWrap(True)
        self.lyric_label4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label3
        self.lyric_label5 = QLabel()
        self.lyric_label5.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label5.setWordWrap(True)
        self.lyric_label5.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label5.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.lyric_labels = [QLabel() for _ in range(5)]
        for i, label in enumerate(self.lyric_labels):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Add labels to vertical layout with minimal spacing
        vertical_layout = QVBoxLayout()
        vertical_layout.setSpacing(5)
        for label in self.lyric_labels:
            vertical_layout.addWidget(label)

        vertical_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(vertical_layout)

        # Assign the main label to a variable for easier access
        self.lyric_label3 = self.lyric_labels[3]  # The main lyric label in the center

        # Create a placeholder for current and previous animations
        self.current_animation = None

    def scroll_lyrics(self, direction="up"):
        """
        Scroll the lyrics in the specified direction ("up" or "down").
        """
        animation_duration = 1000  # 1 second duration for smooth scrolling
        if self.current_animation and self.current_animation.state() == QPropertyAnimation.State.Running:
            self.current_animation.stop()  # Stop any ongoing animation

        # Create a new animation for the layout's geometry
        self.current_animation = QPropertyAnimation(self.lyric_label3, b"geometry")
        start_rect = self.lyric_label3.geometry()

        if direction == "up":
            end_rect = QRect(start_rect.left(), start_rect.top() - start_rect.height(), start_rect.width(),
                             start_rect.height())
        else:  # direction == "down"
            end_rect = QRect(start_rect.left(), start_rect.top() + start_rect.height(), start_rect.width(),
                             start_rect.height())

        self.current_animation.setStartValue(start_rect)
        self.current_animation.setEndValue(end_rect)
        self.current_animation.setDuration(animation_duration)
        self.current_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Smooth easing
        self.current_animation.start()

    def go_to_previous_lyric(self):
        if self.lyrics and self.lyric_sync_connected:
            if self.lyric_label3_text == "(Instrumental Intro)":
                previous_lyric_index = 0
                self.go_to_the_start_of_current_lyric()
            else:
                previous_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) - 1

            if not previous_lyric_index < 0:
                previous_lyrics_key = self.lyrics_keys[previous_lyric_index]
                self.music_player.player.setPosition(int(previous_lyrics_key * 1000))

                # fix the late to set current time due to slower sync time
                self.current_lyrics_time = self.lyrics_keys[previous_lyric_index]
                self.lyric_label3_text = self.lyrics[self.current_lyrics_time]

            else:
                self.current_lyrics_time = self.lyrics_keys[-1]
                previous_lyrics_key = self.lyrics_keys[-1]
                self.music_player.player.setPosition(int(previous_lyrics_key * 1000))

            if self.music_player.in_pause_state:
                self.music_player.paused_position = int(previous_lyrics_key * 1000)

    def go_to_next_lyric(self):
        if self.lyrics and self.lyric_sync_connected:
            if self.lyric_label3_text == "(Instrumental Intro)":
                next_lyric_index = 0
            else:
                next_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) + 1

            if not len(self.lyrics_keys) < (next_lyric_index + 1):
                next_lyric_key = self.lyrics_keys[next_lyric_index]
                print("next line, ", next_lyric_key)
                self.music_player.player.setPosition(int(next_lyric_key * 1000))

                # fix the late to set current time due to slower sync time
                self.current_lyrics_time = self.lyrics_keys[next_lyric_index]
                self.lyric_label3_text = self.lyrics[self.current_lyrics_time]
            else:
                self.current_lyrics_time = self.lyrics_keys[0]
                next_lyric_key = self.lyrics_keys[0]
                self.music_player.player.setPosition(int(next_lyric_key * 1000))

            if self.music_player.in_pause_state:
                self.music_player.paused_position = int(next_lyric_key * 1000)

    def go_to_the_start_of_current_lyric(self):
        self.music_player.player.setPosition(int(self.current_lyrics_time * 1000))

    def parse_lrc(self):
        parse_thread = threading.Thread(target=self.parse_lrc_base)
        parse_thread.start()  # Starts the thread to run the method

    def parse_lrc_base(self):
        lyrics_dict = {}

        if self.file is None:
            print("lrc file not found, attempting to download")
            self.lyrics = None
            pass

        else:
            try:
                with open(self.file, 'r', encoding='utf-8-sig') as file:
                    for line in file:
                        time_str, lyric = extract_time_and_lyric(line)
                        if time_str and lyric:
                            time_in_seconds = convert_time_to_seconds(time_str)
                            lyrics_dict[time_in_seconds] = lyric

                if lyrics_dict:
                    self.lyrics = lyrics_dict
                    self.lyrics_keys = sorted(self.lyrics.keys())

            except Exception as e:
                print(f"Error occurred while parsing lrc file: {e}")
                self.lyrics = None

    def get_current_lyric(self):
        if self.file is not None and self.lyrics:
            print("Inside if condition in get_current_lyric")

            self.current_time = self.music_player.get_current_time()
            abs_time_diff = abs(self.current_time - self.last_update_time)

            # Skip update if within the update interval
            if abs_time_diff < self.update_interval:
                return

            self.last_update_time = self.current_time  # Update last time

            # Use binary search to find the correct lyric index
            index = bisect.bisect_right(self.lyrics_keys, self.current_time)
            self.current_index = index  # for note-taking

            if index == 0:
                # If before the first lyric
                if self.current_time < self.lyrics_keys[0]:
                    print("Before the first lyric")
                    self.set_lyrics_for_intro()
            elif index == 1:
                print("After the first lyric")
                self.set_lyrics_for_first_entry()
            else:
                print("The index is ", index)
                # If after the first lyric or in between lyrics
                if index >= len(self.lyrics_keys):
                    self.set_lyrics_for_after_last()
                else:
                    self.set_lyrics_for_middle(index)
        else:
            print("No lyrics found, setting empty lyrics")
            self.reset_lyrics()

    def set_lyrics_for_intro(self):
        self.current_lyrics_time = self.lyrics_keys[0]
        self.lyric_label1_text = ""
        self.lyric_label2_text = ""
        self.lyric_label3_text = "(Instrumental Intro)"
        self.lyric_label4_text = self.lyrics[self.lyrics_keys[0]]
        self.lyric_label5_text = self.lyrics[self.lyrics_keys[1]]

    def set_lyrics_for_first_entry(self):
        self.current_lyrics_time = self.lyrics_keys[0]
        self.lyric_label1_text = ""
        self.lyric_label2_text = "(Instrumental Intro)"
        self.lyric_label3_text = self.lyrics[self.current_lyrics_time]
        self.lyric_label4_text = self.lyrics[self.lyrics_keys[1]]
        self.lyric_label5_text = self.lyrics[self.lyrics_keys[2]]

    def set_lyrics_for_after_last(self):
        previous_index = len(self.lyrics_keys) - 1
        self.current_lyrics_time = self.lyrics_keys[-1]
        self.lyric_label1_text = self.lyrics[self.lyrics_keys[previous_index - 1]]
        self.lyric_label2_text = self.lyrics[self.lyrics_keys[previous_index]]
        self.lyric_label3_text = self.lyrics[self.current_lyrics_time]
        self.lyric_label4_text = self.lyrics[self.lyrics_keys[1]]
        self.lyric_label5_text = ""

    def set_lyrics_for_middle(self, index):
        self.current_lyrics_time = self.lyrics_keys[index - 1]
        self.lyric_label1_text = self.lyrics[self.lyrics_keys[index - 3]] if index - 3 >= 0 else ""
        self.lyric_label2_text = self.lyrics[self.lyrics_keys[index - 2]] if index - 2 >= 0 else ""
        self.lyric_label3_text = self.lyrics[self.current_lyrics_time]
        self.lyric_label4_text = self.lyrics[self.lyrics_keys[index]] if index < len(self.lyrics_keys) else ""
        self.lyric_label5_text = self.lyrics[self.lyrics_keys[index + 1]] if index + 1 < len(self.lyrics_keys) else ""

    def reset_lyrics(self):
        self.lyric_label1_text = ""
        self.lyric_label2_text = ""
        self.lyric_label3_text = "No Lyrics Found on the Disk"
        self.lyric_label4_text = ""
        self.lyric_label5_text = ""

    def update_media_lyric(self):
        self.get_current_lyric()
        self.media_lyric.setText(self.media_font.get_formatted_text(self.lyric_label3_text))

    def update_display_lyric(self):
        if self.current_index == self.previous_index:
            if self.first_time_update_text:
                self.first_time_update_text = False
                pass
            else:
                return

        # Update the text for each label only if the index has changed
        if self.lyric_label1 is not None:
            self.lyric_label1.setText(self.lrc_font.get_formatted_text(self.lyric_label1_text))
        if self.lyric_label2 is not None:
            self.lyric_label2.setText(self.lrc_font.get_formatted_text(self.lyric_label2_text))
        if self.lyric_label3 is not None:
            self.lyric_label3.setText(self.lrc_font.get_formatted_text(self.lyric_label3_text))
        if self.lyric_label4 is not None:
            self.lyric_label4.setText(self.lrc_font.get_formatted_text(self.lyric_label4_text))
        if self.lyric_label5 is not None:
            self.lyric_label5.setText(self.lrc_font.get_formatted_text(self.lyric_label5_text))

        # Set the position of lyric_label3 to always remain at a fixed vertical position
        if self.lyric_label3 is not None:
            fixed_y_position = 100  # Set the vertical position you want to lock
            self.lyric_label3.move(self.lyric_label3.x(), fixed_y_position)

        # Update the previous index after labels have been updated
        self.previous_index = self.current_index

    def create_animations(self, direction):
        """Create and start animations for the labels moving up or down."""
        # Create animations for all 5 labels
        anim_label1 = QPropertyAnimation(self.lyric_label1, b"pos")
        anim_label2 = QPropertyAnimation(self.lyric_label2, b"pos")
        anim_label3 = QPropertyAnimation(self.lyric_label3, b"pos")
        anim_label4 = QPropertyAnimation(self.lyric_label4, b"pos")
        anim_label5 = QPropertyAnimation(self.lyric_label5, b"pos")

        # Set the start positions for all labels
        anim_label1.setStartValue(self.lyric_label1.pos())
        anim_label2.setStartValue(self.lyric_label2.pos())
        anim_label3.setStartValue(self.lyric_label3.pos())
        anim_label4.setStartValue(self.lyric_label4.pos())
        anim_label5.setStartValue(self.lyric_label5.pos())

        # Define animation durations
        anim_label1.setDuration(self.animation_duration)
        anim_label2.setDuration(self.animation_duration)
        anim_label3.setDuration(self.animation_duration)
        anim_label4.setDuration(self.animation_duration)
        anim_label5.setDuration(self.animation_duration)

        # Define the end positions based on direction
        if direction == "up":
            # Move labels up
            anim_label1.setEndValue(self.lyric_label2.pos())
            anim_label2.setEndValue(self.lyric_label3.pos())
            anim_label3.setEndValue(self.lyric_label4.pos())
            anim_label4.setEndValue(self.lyric_label5.pos())
            anim_label5.setEndValue(QPoint(105, 305))  # Move label5 off the view

            # Connect animation completion to update labels
            anim_label3.finished.connect(lambda: self.update_lyrics_after_movement("up"))

        elif direction == "down":
            # Move labels down
            anim_label1.setEndValue(QPoint(105, -20))  # Move label1 off the view
            anim_label2.setEndValue(self.lyric_label1.pos())
            anim_label3.setEndValue(self.lyric_label2.pos())
            anim_label4.setEndValue(self.lyric_label3.pos())
            anim_label5.setEndValue(self.lyric_label4.pos())

            # Connect animation completion to update labels
            anim_label3.finished.connect(lambda: self.update_lyrics_after_movement("down"))

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
            self.lyric_label2.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from above label
        elif direction == "down":
            self.lyric_label4.setStyleSheet("color: gray; font-size: 16px;")  # Remove highlight from below label

        self.lyric_label3.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")  # Reapply highlight to current

        # Update text for each label based on the current index
        self.lyric_label1.setText(self.lyrics.get(self.current_index - 2, "") if self.current_index - 2 >= 0 else "")
        self.lyric_label2.setText(self.lyrics.get(self.current_index - 1, "") if self.current_index - 1 >= 0 else "")
        self.lyric_label3.setText(self.lyrics.get(self.current_index, ""))
        self.lyric_label4.setText(self.lyrics.get(self.current_index + 1, "") if self.current_index + 1 < len(self.lyrics) else "")
        self.lyric_label5.setText(self.lyrics.get(self.current_index + 2, "") if self.current_index + 2 < len(self.lyrics) else "")

        # Reset positions after the animation completes
        self.set_initial_positions()

    def sync_lyrics(self, file):
        self.update_file_and_parse(file)
        if self.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_media_lyric)
            self.media_sync_connected = False

        self.music_player.player.positionChanged.connect(self.update_media_lyric)
        self.media_sync_connected = True
