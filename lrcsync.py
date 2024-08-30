import re
import os
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QDialog, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeyEvent
from getfont import GetFont

def extract_time_and_lyric(line):
    match = re.match(r'\[(\d{2}:\d{2}\.\d{2})\](.*)', line)
    if match:
        time_str = match.group(1)
        lyric = match.group(2).strip()
        return time_str, lyric
    return None, None

def convert_time_to_seconds(time_str):
    minutes, seconds = map(float, time_str.split(":"))
    return minutes * 60 + seconds

class LRCSync:
    def __init__(self, player):
        self.lrc_display = None
        self.file = None
        self.player = player
        self.lyric_label = None
        self.lyrics = None
        self.current_time = 0.0
        self.media_lyric = QLabel()
        self.media_lyric.setWordWrap(True)
        self.media_font = GetFont(13)
        self.lrc_font = GetFont(50)

    def updateFileandParse(self, file):
        if file is None:
            pass
        else:
            self.file = file

        self.parse_lrc()

    def startUI(self, parent, file):
        self.lrc_display = QDialog(parent)
        self.lrc_display.setWindowTitle(file)

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the icon file
        icon_path = os.path.join(script_dir, 'icons', 'lrc.png')

        self.lrc_display.setWindowIcon(QIcon(icon_path))
        
        # Calculate the width and height of the dialog
        dialog_width = int(parent.width() * 0.9)
        dialog_height = int(parent.height() * 0.8)

        # Calculate the top-left position of the dialog relative to the parent widget
        relative_x = int((parent.width() - dialog_width) / 2)
        relative_y = int((parent.height() - dialog_height) / 2)

        # Convert the relative position to global screen coordinates
        global_position = parent.mapToGlobal(parent.rect().topLeft())

        # Add the relative position to the global position to get the final coordinates
        positionx = global_position.x() + relative_x
        positiony = global_position.y() + relative_y

        # Set the geometry of the dialog
        self.lrc_display.setGeometry(positionx, positiony, dialog_width, dialog_height)


        self.player.player.positionChanged.connect(self.update_lyrics)

        main_layout = QVBoxLayout(self.lrc_display)
        self.setup_button_layout(main_layout)

        self.updateFileandParse(file)
        self.update_lyrics()

        # Properly connect the close event
        self.lrc_display.closeEvent = self.closeEvent
        self.lrc_display.keyPressEvent = self.keyPressEvent

        self.lrc_display.exec()
        
    def closeEvent(self, event):
        print("QDialog closed")
        self.lyric_label = None
        self.lrc_display = None
        event.accept()  # To accept the close event
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.player.seek_backward()
            
        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.player.seek_forward()
            
        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.player.play_pause()

    def setup_button_layout(self, main_layout):       
        # Initialize lyric label as a class attribute for potential updates
        self.lyric_label = QLabel("Current Lyrics")
        self.lyric_label.setWordWrap(True)
        self.lyric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prev_button = QPushButton("Previous Line")
        play_pause_button = QPushButton("Play/Pause")
        forward_button = QPushButton("Forward Line")

        prev_button.clicked.connect(self.player.seek_backward)
        play_pause_button.clicked.connect(self.player.play_pause_music)
        forward_button.clicked.connect(self.player.seek_forward)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(prev_button)
        button_layout.addWidget(play_pause_button)
        button_layout.addWidget(forward_button)

        # Add widgets to the main layout
        main_layout.addWidget(self.lyric_label)
        # main_layout.addLayout(button_layout)
        
    def go_to_previous_lyrics(self):
        pass
    
    def next_lyric(self):
        pass

    def parse_lrc(self):
        lyrics_dict = {}

        if self.file is None:
            self.lyrics = None
        else:
            with open(self.file, 'r', encoding='utf-8') as file:
                for line in file:
                    time_str, lyric = extract_time_and_lyric(line)
                    if time_str and lyric:
                        time_in_seconds = convert_time_to_seconds(time_str)
                        lyrics_dict[time_in_seconds] = lyric
            self.lyrics = lyrics_dict

    def get_current_playback_time(self):
        return self.player.get_current_time()

    def update_lyrics(self):
        if self.lyric_label is not None:
            if self.file is not None:
                self.current_time = self.get_current_playback_time()
                lyrics_keys = sorted(self.lyrics.keys())
                for i in range(len(lyrics_keys)):
                    if self.current_time < lyrics_keys[i]:
                        if i == 0:
                            self.lyric_label.setText(self.lrc_font.get_formatted_text(self.lyrics[lyrics_keys[0]]))  # Handle the first lyric
                        else:
                            self.lyric_label.setText(self.lrc_font.get_formatted_text(self.lyrics[lyrics_keys[i - 1]]))
                        break
                else:
                    self.lyric_label.setText(self.lrc_font.get_formatted_text(self.lyrics[lyrics_keys[-1]]))
            else:
                self.lyric_label.setText("No lrc file found on the disk")

    def update_media_lyric(self):
        if self.file is not None:
            self.current_time = self.get_current_playback_time()
            lyrics_keys = sorted(self.lyrics.keys())
            for i in range(len(lyrics_keys)):
                if self.current_time < lyrics_keys[i]:
                    if i == 0:
                        self.media_lyric.setText(self.media_font.get_formatted_text(self.lyrics[lyrics_keys[0]]))  # Handle the first lyric
                    else:
                        self.media_lyric.setText(self.media_font.get_formatted_text(self.lyrics[lyrics_keys[i - 1]]))
                    break
            else:
                self.media_lyric.setText(self.media_font.get_formatted_text(self.lyrics[lyrics_keys[-1]]))
        else:
            self.media_lyric.setText("No lrc file found on the disk")

    def sync_lyrics(self, file):
        self.updateFileandParse(file)
        self.player.player.positionChanged.connect(self.update_media_lyric)
        self.update_media_lyric()
