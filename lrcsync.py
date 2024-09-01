import json
import re
import os
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QDialog, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeyEvent
from getfont import GetFont
from easy_json import EasyJson

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
        self.lyrics_keys = None
        self.current_time = 0.0
        self.media_lyric = QLabel()
        self.media_lyric.setWordWrap(True)
        self.media_font = GetFont(13)
        self.lrc_font = GetFont(50)
        self.current_lyric = "....."
        self.current_lyrics_time = 0.0
        self.last_update_time = 0.0  # Initialize with 0 or None
        self.update_interval = 0.1  # Minimum interval in seconds      

    def updateFileandParse(self, file):
        if file is None:
            pass
        else:
            self.file = file

        self.parse_lrc()

    def startUI(self, parent, file, config_file):
        ejson = EasyJson(config_file)

        self.lrc_display = QDialog(parent)
        self.lrc_display.setWindowTitle(file)
        
        if not ejson.get_value("background_image"):
            ejson.setupDefaultFiles()  
            
        image_path = ejson.get_value("background_image")
                                        
        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            image_path = image_path.replace("\\", "/") # တော်တော်သောက်လုပ်ရှပ်တဲ့ window   

        self.lrc_display.setStyleSheet(f"""
            QDialog {{
                background-image: url({image_path});
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }}
        """)
        
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the icon file
        icon_path = os.path.join(script_dir, 'icons', 'april.png')

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

        # Properly connect the close event
        self.lrc_display.closeEvent = self.closeEvent
        self.lrc_display.keyPressEvent = self.keyPressEvent

        self.lrc_display.exec()
        
    def closeEvent(self, event):
        print("QDialog closed")
        self.lyric_label = None
        self.lrc_display = None
        self.player.player.positionChanged.disconnect(self.update_lyrics)        
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
        elif event.key() == Qt.Key.Key_Up:
            print("UP key pressed")
            self.go_to_previous_lyrics()
        elif event.key() == Qt.Key.Key_Down:
            print("down key pressed")
            self.go_to_next_lyrics()
        elif event.key() == Qt.Key.Key_D:
            self.go_to_the_start_of_current_lyric()           
        elif event.key() == Qt.Key.Key_F:
            print("pressed F")
            if self.is_full_screen():
                self.lrc_display.showNormal()  # Restore to normal mode
            else:
                self.lrc_display.showFullScreen()  # Enter full-screen mode

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
        self.lyric_label = QLabel("Current Lyrics")
        self.lyric_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

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
        previous_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) - 1
        if not previous_lyric_index < 0:
            previous_lyrics_key = self.lyrics_keys[previous_lyric_index]
            print("previous time, ", previous_lyrics_key)        
            self.player.player.setPosition(int(previous_lyrics_key * 1000))
        else:
            previous_lyrics_key = self.lyrics_keys[-1]
            self.player.player.setPosition(int(previous_lyrics_key * 1000))
            
        if self.player.in_pause_state:
            self.player.paused_position = int(previous_lyrics_key * 1000)
            
    
    def go_to_next_lyrics(self):
        next_lyric_index = self.lyrics_keys.index(self.current_lyrics_time) + 1
        if not len(self.lyrics_keys) < (next_lyric_index + 1):
            next_lyric_key = self.lyrics_keys[next_lyric_index]
            print("next line, ", next_lyric_key)        
            self.player.player.setPosition(int(next_lyric_key * 1000))
        else:
            next_lyric_key = self.lyrics_keys[0]
            print("next line, ", next_lyric_key)        
            self.player.player.setPosition(int(next_lyric_key * 1000))
            
        if self.player.in_pause_state:
            self.player.paused_position = int(next_lyric_key * 1000)            
        
    def go_to_the_start_of_current_lyric(self):
        self.player.player.setPosition(int(self.current_lyrics_time * 1000))

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
            self.lyrics_keys = sorted(self.lyrics.keys())
    
    def get_current_lyrics(self):
        if self.file is not None:
            self.current_time = self.player.get_current_time()

            # Only update if the current time has moved beyond the update interval
            abs_value = abs(self.current_time - self.last_update_time)
            if abs_value < self.update_interval:
                return  # Skip updating if within the interval

            self.last_update_time = self.current_time  # Update the last updated time

            for i in range(len(self.lyrics_keys)):
                if self.current_time < self.lyrics_keys[i]:
                    if i == 0:
                        self.current_lyrics_time = self.lyrics_keys[0]
                        self.current_lyric = self.lyrics[self.current_lyrics_time]
                    else:
                        self.current_lyrics_time = self.lyrics_keys[i - 1]
                        self.current_lyric = self.lyrics[self.current_lyrics_time]
                    break
            else:
                self.current_lyrics_time = self.lyrics_keys[-1]
                self.current_lyric = self.lyrics[self.current_lyrics_time]
        else:
            self.current_lyrics_time = 0.0
            self.current_lyric = "No lyrics"       
                                                            
    def update_media_lyric(self):
        self.get_current_lyrics()
        self.media_lyric.setText(self.media_font.get_formatted_text(self.current_lyric))
                        
    def update_lyrics(self):
        if self.lyric_label is not None:
            self.lyric_label.setText(self.lrc_font.get_formatted_text(self.current_lyric))
            
    def sync_lyrics(self, file):
        self.updateFileandParse(file)
        self.player.player.positionChanged.connect(self.update_media_lyric)