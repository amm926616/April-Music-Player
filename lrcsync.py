import bisect
import re
import os
import sys
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QDialog, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeyEvent
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
    def __init__(self, app, music_player, config_path, on_off_lyrics=None, uishowMaximized=None):
        self.uiShowMaximized = uishowMaximized
        self.on_off_lyrics = on_off_lyrics
        self.app = app
        self.config_path = config_path
        self.ej = EasyJson()
        self.lrc_display = None
        self.file = None
        self.music_file = None
        self.music_player = music_player
        self.lyric_label = None
        self.lyrics = None
        self.lyrics_keys = None
        self.current_time = 0.0
        self.media_font = GetFont(13)
        self.media_lyric = ClickableLabel()
        self.media_lyric.setWordWrap(True)
        self.lrc_font = GetFont(int(self.ej.get_value("lrc_font_size")))
        self.show_lyrics = self.ej.get_value("show_lyrics")
        self.dictionary = None

        if self.show_lyrics:
            self.current_lyric = "April Music Player"
        else:
            self.current_lyric = "Lyrics Disabled"

        self.media_lyric.setText(self.media_font.get_formatted_text(self.current_lyric))

        self.lyric_sync_connected = None
        self.media_sync_connected = None
        self.current_lyrics_time = 0.0
        self.last_update_time = 0.0  # Initialize with 0 or None
        self.update_interval = float(self.ej.get_value("sync_threshold"))  # Minimum interval in seconds    
        self.script_path = os.path.dirname(os.path.abspath(__file__))
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
        font_size = int(self.app.height() * 0.06)  # Set your desired font size here
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
        dialog_width = int(parent.width() * 0.9)
        dialog_height = int(parent.height() * 0.8)

        # Calculate the top-left position of the dialog relative to the parent widget
        relative_x = int((parent.width() - dialog_width) / 2)
        relative_y = int((parent.height() - dialog_height) / 2)

        # Convert the relative position to global screen coordinates
        global_position = parent.mapToGlobal(parent.rect().topLeft())

        # Add the relative position to the global position to get the final coordinates
        position_x = global_position.x() + relative_x
        position_y = global_position.y() + relative_y

        # Set the geometry of the dialog
        self.lrc_display.setGeometry(position_x, position_y, dialog_width, dialog_height)

        main_layout = QVBoxLayout(self.lrc_display)
        self.setup_button_layout(main_layout)

        if self.show_lyrics:
            if self.started_player:
                self.lyric_label.setText(self.lrc_font.get_formatted_text(self.current_lyric))
            else:
                self.lyric_label.setText(self.lrc_font.get_formatted_text("April Music Player"))

            self.music_player.player.positionChanged.connect(self.update_display_lyric)
            self.lyric_sync_connected = True
        else:
            self.lyric_label.setText(self.lrc_font.get_formatted_text("Lyrics Disabled"))

        # Properly connect the close event
        self.lrc_display.closeEvent = self.closeEvent
        self.lrc_display.keyPressEvent = self.keyPressEvent

        self.lrc_display.exec()

    def closeEvent(self, event):
        self.uiShowMaximized()
        print("QDialog closed")
        self.lyric_label = None
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
                self.dictionary = VocabularyManager(self)                      
            self.dictionary.exec()

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
                self.lyric_label.setText(self.lrc_font.get_formatted_text("Lyrics Disabled"))
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

    def setup_button_layout(self, main_layout):
        # Initialize lyric label as a class attribute for potential updates
        self.lyric_label = QLabel()
        self.lyric_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.lyric_label.setWordWrap(True)

        lyrics_color = self.ej.get_value("lyrics_color")

        # Check if the image path is not set or the file does not exist
        if not lyrics_color:
            self.ej.setupLyricsColor()
            lyrics_color = self.ej.get_value("lyrics_color")

        self.lyric_label.setStyleSheet(f"color: {lyrics_color};")
        self.lyric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prev_button = QPushButton("Previous Line")
        play_pause_button = QPushButton("Play/Pause")
        forward_button = QPushButton("Forward Line")

        prev_button.clicked.connect(self.music_player.seek_backward)
        play_pause_button.clicked.connect(self.music_player.play_pause_music)
        forward_button.clicked.connect(self.music_player.seek_forward)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(prev_button)
        button_layout.addWidget(play_pause_button)
        button_layout.addWidget(forward_button)

        # Add widgets to the main layout
        main_layout.addWidget(self.lyric_label)
        # main_layout.addLayout(button_layout)

    def go_to_previous_lyric(self):
        if self.lyrics and self.lyric_sync_connected:
            previous_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) - 1
            if not previous_lyric_index < 0:
                previous_lyrics_key = self.lyrics_keys[previous_lyric_index]
                self.music_player.player.setPosition(int(previous_lyrics_key * 1000))

                # fix the late to set current time due to slower sync time                                
                self.current_lyrics_time = self.lyrics_keys[previous_lyric_index]
                self.current_lyric = self.lyrics[self.current_lyrics_time]

            else:
                self.current_lyrics_time = self.lyrics_keys[-1]
                previous_lyrics_key = self.lyrics_keys[-1]
                self.music_player.player.setPosition(int(previous_lyrics_key * 1000))

            if self.music_player.in_pause_state:
                self.music_player.paused_position = int(previous_lyrics_key * 1000)

    def go_to_next_lyric(self):
        if self.lyrics and self.lyric_sync_connected:
            if self.current_lyric == "(Instrumental Intro)":
                next_lyric_index = 0
            else:
                next_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) + 1

            if not len(self.lyrics_keys) < (next_lyric_index + 1):
                next_lyric_key = self.lyrics_keys[next_lyric_index]
                print("next line, ", next_lyric_key)
                self.music_player.player.setPosition(int(next_lyric_key * 1000))

                # fix the late to set current time due to slower sync time                                                
                self.current_lyrics_time = self.lyrics_keys[next_lyric_index]
                self.current_lyric = self.lyrics[self.current_lyrics_time]
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
            self.current_time = self.music_player.get_current_time()

            # Only update if the current time has moved beyond the update interval
            abs_value = abs(self.current_time - self.last_update_time)
            if abs_value < self.update_interval:
                return  # Skip updating if within the interval

            self.last_update_time = self.current_time  # Update the last updated time

            # Use binary search to find the correct lyrics time
            index = bisect.bisect_right(self.lyrics_keys, self.current_time)
            self.current_index = index  # pass it for lyric index in note-taking

            if index == 0:
                if self.current_time < self.lyrics_keys[0]:  # for instrument section before first lyric
                    self.current_lyrics_time = self.lyrics_keys[0]
                    self.current_lyric = "(Instrumental Intro)"
                else:
                    # If the current time is before the first lyric
                    self.current_lyrics_time = self.lyrics_keys[0]
                    self.current_lyric = self.lyrics[self.current_lyrics_time]

            else:
                if index >= len(self.lyrics_keys):
                    # If the current time is after the last lyric
                    self.current_lyrics_time = self.lyrics_keys[-1]
                    self.current_lyric = self.lyrics[self.current_lyrics_time]
                else:
                    # Otherwise, the correct lyric is at the previous index
                    self.current_lyrics_time = self.lyrics_keys[index - 1]
                    self.current_lyric = self.lyrics[self.current_lyrics_time]

        else:
            self.current_lyric = "No Lyrics Found on the Disk"

    def update_media_lyric(self):
        self.get_current_lyric()
        self.media_lyric.setText(self.media_font.get_formatted_text(self.current_lyric))

    def update_display_lyric(self):
        if self.lyric_label is not None:
            self.lyric_label.setText(self.lrc_font.get_formatted_text(self.current_lyric))

    def sync_lyrics(self, file):
        self.update_file_and_parse(file)
        if self.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_media_lyric)
            self.media_sync_connected = False

        self.music_player.player.positionChanged.connect(self.update_media_lyric)
        self.media_sync_connected = True
