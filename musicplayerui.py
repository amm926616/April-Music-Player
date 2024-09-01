import json
from base64 import b64decode
import sqlite3
import os
import sys
import platform
from collections import defaultdict

from PyQt6.QtGui import QAction, QIcon, QFont, QFontDatabase, QAction, QCursor, QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QMessageBox, QSystemTrayIcon, QMenu,
    QLabel, QPushButton, QListWidget, QSlider, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QCoreApplication
from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
from PyQt6.QtGui import QPixmap
from album_image_window import AlbumImageWindow
from lrcsync import LRCSync
from musicplayer import MusicPlayer
from clickable_progressbar import DoubleClickableProgressBar
from clickable_label import ClickableLabel
from easy_json import EasyJson

def extract_mp3_album_art(audio_file):
    """Extract album art from an MP3 file."""
    if audio_file.tags is None:
        return None

    for tag in audio_file.tags.values():
        if isinstance(tag, APIC):
            return tag.data
    return None


def extract_mp4_album_art(audio_file):
    """Extract album art from an MP4 file."""
    covers = audio_file.tags.get('covr')
    if covers:
        return covers[0] if isinstance(covers[0], bytes) else covers[0].data
    return None


def extract_flac_album_art(audio_file):
    """Extract album art from a FLAC file."""
    if audio_file.pictures:
        return audio_file.pictures[0].data
    return None


def extract_ogg_album_art(audio_file):
    """Extract album art from an OGG file."""
    if 'metadata_block_picture' in audio_file:
        picture_data = audio_file['metadata_block_picture'][0]
        picture = Picture(b64decode(picture_data))
        return picture.data
    return None


def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"


def extract_track_number(track_number):
    """
    Extracts the track number from a string, handling cases like "1/6" or "02/12".
    Returns the integer part before the slash, or the whole number if there's no slash.
    """
    if '/' in track_number:
        return int(track_number.split('/')[0])
    elif track_number.isdigit():
        return int(track_number)
    return float('inf')  # For non-numeric track numbers, place them at the end


class MusicPlayerUI(QMainWindow):
    def __init__(self, app):
        super().__init__()

        # Define the config path
        self.script_path = os.path.dirname(os.path.abspath(__file__))
        self.central_widget = None
        self.songTableWidget = None
        self.songListWidget = None
        self.search_bar = None
        self.track_display = None
        self.song_details = None
        self.image_display = None
        self.progress_bar = None
        self.slider = None
        self.prev_button = None
        self.play_pause_button = None
        self.click_count = 0
        self.forw_button = None
        self.config_path = None
        self.app = app
        self.file_path = None
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.getenv('APPDATA'), 'April Music Player')
        else:
            self.config_path = os.path.join(os.path.expanduser("~"), '.config', 'april-music-player')
                        
        config_file = os.path.join(self.config_path, "config.json")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        # Check if the file exists
        if not os.path.isfile(config_file):
            # Create an empty configuration
            default_config = {
                "directory": None
            }

            # Write the default configuration to the file
            with open(config_file, 'w') as file:
                json.dump(default_config, file, indent=4)

        self.config_file = config_file
        self.ej = EasyJson(self.config_file) # give config path to ej after setting up            

        self.directory = None
        self.load_config()

        self.music_file = None
        self.lrc_file = None
        self.player = MusicPlayer()
        self.lrcPlayer = LRCSync(self.player, self.config_file)

    def load_config(self):
        """Load configuration from a JSON file."""
        if os.path.exists(self.config_file):
            self.directory = self.ej.get_value("music_directory")
        else:
            self.directory = None        

    def save_config(self, key, value):
        self.ej.edit_value(key, value)

    def ask_for_directory(self, loadAgain):
        """Prompt the user to select a music directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Your Main Music Directory Where You Put All Of Your Musics", "")
        print("dir ", dir_path)
        if dir_path:
            self.directory = dir_path
            self.save_config("music_directory", self.directory)
            self.loadSongs(loadAgain)
        else:
            # If the user cancels, show a message and close the app or ask again
            QMessageBox.warning(self, "No Directory Selected", "A music directory is required to proceed.")
            return

    def createUI(self):
        self.setWindowTitle("April Music Player - Digest Lyrics")
        self.setGeometry(100, 100, 800, 400)

        # Construct the full path to the icon file
        self.icon_path = os.path.join(self.script_path, 'icons', 'april.png')

        self.setWindowIcon(QIcon(self.icon_path))
        self.createMenuBar()        
        self.createWidgetAndLayouts()
        self.showMaximized()             
        self.setupTrayIcon()
        
    def setupTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.icon_path))
        self.tray_icon.setVisible(True)
        
        self.tray_menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        self.tray_menu.addAction(open_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_clicked)
        
    def on_tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Handle the left-click (Trigger) event here
            print("Tray icon was left-clicked!")
            if self.isHidden():
                self.show()
            else:
                self.hide()  # Optionally, you can toggle between showing and hiding
                        
    def closeEvent(self, event):
        print("hiding window")
        self.hide()
        if self.lrcPlayer.lrc_display is not None:
            self.lrcPlayer.lrc_display.close()
        event.ignore()
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.seekBack()
            
        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.seekForward()
            
        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.play_pause()
            
        elif event.key() == Qt.Key.Key_L and Qt.KeyboardModifier.ControlModifier:
            self.on_progress_bar_double_click()            
            
        elif event.key() == Qt.Key.Key_Q and Qt.KeyboardModifier.ControlModifier:
            sys.exit()
            
        elif event.key() == Qt.Key.Key_S and Qt.KeyboardModifier.ControlModifier:
            print("serach")
            self.search_bar.setFocus()
            self.search_bar.setCursorPosition(len(self.search_bar.text()))
            
    def folder_load_again(self):
        self.ask_for_directory(True)
            
    def createMenuBar(self):
        # this is the menubar that will hold all together
        menubar = self.menuBar()

        # Actions that will become buttons for each menu
        load_folder = QAction("Load folder", self)
        load_folder.triggered.connect(self.folder_load_again)

        close_action = QAction("Exit", self)
        close_action.triggered.connect(self.close)
        
        show_shortcuts_action = QAction("Show Shortcuts", self)
        show_shortcuts_action.triggered.connect(self.show_shortcuts)
        
        add_lrc_background = QAction("Add Lrc Background Image", self)
        add_lrc_background.triggered.connect(self.ask_for_background_image)

        # These are main menus in the menu bar
        file_menu = menubar.addMenu("File")
        options_menu = menubar.addMenu("Options")
        help_menu = menubar.addMenu("Help")

        # Linking actions and menus
        file_menu.addAction(load_folder)
        file_menu.addAction(close_action)
        help_menu.addAction(show_shortcuts_action)      
        options_menu.addAction(add_lrc_background) 
        
    def show_shortcuts(self):
        shortcuts_text = """
        <b>Keyboard Shortcuts</b><br><br>
        
        <b>General:</b><br>
        - <b>Left Arrow, Right Arrow, Spacebar:</b> Seek backward, seek forward, and play/pause, respectively.<br>
        - <b>Ctrl + L:</b> Activate LRC display, or double-click the progress bar.<br>
        - <b>Ctrl + S:</b> Focus and place cursor on search bar.<br>
        - <b>Ctrl + Q:</b> Quit the program (The program runs in the background even if the main window is closed).<br><br>
        
        <b>In LRC View:</b><br>
        - <b>F:</b> Toggle full-screen mode.<br>
        - <b>D:</b> Go to the start of the current lyric.<br>
        - <b>Up Arrow, Down Arrow:</b> Seek to the previous or next lyric line.<br>
        """
        QMessageBox.information(self, "Shortcuts", shortcuts_text)

 
        
    def ask_for_background_image(self):
        # Open a file dialog and get the selected file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File")
        
        if file_path:
            # Show the selected file path in a QMessageBox
            QMessageBox.information(self, "Load Background Image", f"You selected: {file_path}")
        else:
            QMessageBox.warning(self, "No File Selected", "You did not select any file.")
            
        self.save_config("background_image", file_path)  
        
    def show_context_menu(self, pos):
        # Get the item at the clicked position
        item = self.songTableWidget.itemAt(pos)
        
        if item:
            # Create the context menu
            context_menu = QMenu(self)
            
            # Add an action to copy the file path
            copy_action = context_menu.addAction("Copy Path")
            
            # Connect the action to a method
            copy_action.triggered.connect(lambda: self.copy_item_path(item))
            
            # Show the context menu at the cursor position
            context_menu.exec(QCursor.pos())

    def copy_item_path(self, item):
        print("in copy item path")
        file = self.get_music_file_from_click(item)
        self.app.clipboard().setText(file)

    def createWidgetAndLayouts(self):
        """ The main layout of the music player ui"""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout()
        self.central_widget.setLayout(main_layout)

        # Initialize the table widget
        self.songTableWidget = QTableWidget(self)  
        self.songTableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.songTableWidget.customContextMenuRequested.connect(self.show_context_menu)      
        self.songTableWidget.setColumnCount(9)  # 7 for metadata + 1 for file path
        self.songTableWidget.setHorizontalHeaderLabels(
            ['Title', 'Artist', 'Album', 'Year', 'Genre', 'Track Number', 'Duration', 'File Path', "Media Type"]
        )

        # Set selection behavior to select entire rows
        self.songTableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.songTableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Adjust column resizing
        header = self.songTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Stretch all columns

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.songTableWidget)

        # Connect the itemClicked signal to the custom slot
        self.songTableWidget.itemDoubleClicked.connect(self.handleRowDoubleClick)
        self.songTableWidget.itemClicked.connect(self.handleRowSingleClick)

        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(5, 0, 0, 0)  # 5 pixels to the left
        main_layout.addLayout(leftLayout, 4)
        main_layout.addLayout(rightLayout, 1)
        
        self.setupSongListWidget(leftLayout)
        self.setupMediaPlayerWidget(rightLayout)

    def setupSongListWidget(self, left_layout):
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFocus()  # Place the cursor in the search bar

        # Connect search bar returnPressed signal to the search method
        self.search_bar.returnPressed.connect(self.filterSongs)

        self.songListWidget = QListWidget()
        left_layout.addWidget(self.search_bar)
        if self.ej.get_value("music_directory") is None:
            self.ask_for_directory(False)
        self.loadSongs()

    def setupMediaPlayerWidget(self, right_layout):
        # Create a widget to hold the media player components
        media_widget = QWidget()
        
        # Create and configure the layout for the media widget
        mediaLayout = QVBoxLayout(media_widget)

        # Create and configure the track display label
        self.track_display = QLabel("No Track Playing")
        self.track_display.setFont(QFont("Komika Axis"))
        self.track_display.setWordWrap(True)
        self.track_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.track_display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.track_display.setStyleSheet("font-size: 20px")

        # Create and configure the image display label
        self.image_display = ClickableLabel()
        self.image_display.doubleClicked.connect(self.double_click_on_image)
        
        # Create and configure the song details label
        self.song_details = QLabel()
        self.song_details.setWordWrap(True)  # Ensure the text wraps within the label

        # Make the song_details label scrollable by placing it inside a QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.song_details)
        
        # Add widgets to the vertical layout
        mediaLayout.addWidget(self.track_display)
        mediaLayout.addWidget(self.image_display)
        mediaLayout.addWidget(scroll_area)  # Add the scroll area instead of the label directly
        mediaLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add the media_widget to the right_layout
        right_layout.addWidget(media_widget)
        
        # Set up the media player controls panel
        self.setupMediaPlayerControlsPanel(right_layout)

    def setupMediaPlayerControlsPanel(self, right_layout):
        # Store progress bar in a class variable
        # Create a QProgressBar
        self.progress_bar = DoubleClickableProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #6f0e10;
                width: 10px;
            }
        """)

        # Connect the custom double-click signal to a function
        self.progress_bar.doubleClicked.connect(self.on_progress_bar_double_click)

        # Create a QSlider
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)

        # Connect the slider value to the progress bar
        self.slider.valueChanged.connect(self.progress_bar.setValue)

        # Connect the slider to the player's position
        self.slider.sliderMoved.connect(self.set_position)

        right_layout.addWidget(self.lrcPlayer.media_lyric)
        self.lrcPlayer.media_lyric.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.slider)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton()
        self.play_pause_button = QPushButton()
        self.forw_button = QPushButton()

        self.prev_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "seek-backward.ico")))
        self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "pause.ico")))
        self.forw_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "seek-forward.ico")))

        self.prev_button.clicked.connect(self.seekBack)
        self.play_pause_button.clicked.connect(self.play_pause)
        self.forw_button.clicked.connect(self.seekForward)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.forw_button)

        right_layout.addLayout(controls_layout)
        self.connect_progressbar_signals()

    def updateDisplayData(self):
        metadata = self.get_metadata()
        updated_text = f'{metadata["artist"]} - {metadata["title"]}'
        self.track_display.setText(updated_text)

    def updateSongDetails(self):
        metadata = self.get_metadata()
        minutes = metadata["duration"] // 60
        seconds = metadata["duration"] % 60
        # Define the bold HTML tag
        BOLD = '<b>'
        END = '</b>'
        
        updated_text = (
            f'<div>{BOLD}[Track Details]{END}</div>'
            f'<div>{BOLD}Title{END}: {metadata["title"]}</div>'
            f'<div>{BOLD}Artist{END}: {metadata["artist"]}</div>'
            f'<div>{BOLD}Album{END}: {metadata["album"]}</div>'
            f'<div>{BOLD}Release Date{END}: {metadata["year"]}</div>'
            f'<div>{BOLD}Genre{END}: {metadata["genre"]}</div>'
            f'<div>{BOLD}Track Number{END}: {metadata["track_number"]}</div>'
            f'<div>{BOLD}Comment{END}: {metadata["comment"]}</div>'
            f'<div>{BOLD}Duration{END}: {minutes}:{seconds:02d}</div>'
            f'<div>{BOLD}File Path{END}: {self.file_path}</div>'            
        )
    
        self.song_details.setText(updated_text)
        # Set text interaction to allow text selection
        self.song_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.song_details.setWordWrap(True)

    def get_metadata(self):
        file_extension = self.music_file.lower().split('.')[-1]

        metadata = {
            'title': 'Unknown Title',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'year': 'Unknown Year',
            'genre': 'Unknown Genre',
            'track_number': 'Unknown Track Number',
            'comment': 'No Comment',
            'duration': 0,  # Initialize duration as integer,
            'file_type': 'Unknown File Type',
        }

        try:
            if file_extension == 'mp3':
                audio = ID3(self.music_file)
                metadata['title'] = audio.get('TIT2', 'Unknown Title').text[0] if audio.get('TIT2') else 'Unknown Title'
                metadata['artist'] = audio.get('TPE1', 'Unknown Artist').text[0] if audio.get(
                    'TPE1') else 'Unknown Artist'
                metadata['album'] = audio.get('TALB', 'Unknown Album').text[0] if audio.get('TALB') else 'Unknown Album'
                metadata['year'] = audio.get('TDRC', 'Unknown Year').text[0] if audio.get('TDRC') else 'Unknown Year'
                metadata['genre'] = audio.get('TCON', 'Unknown Genre').text[0] if audio.get('TCON') else 'Unknown Genre'
                metadata['track_number'] = audio.get('TRCK', 'Unknown Track Number').text[0] if audio.get(
                    'TRCK') else 'Unknown Track Number'
                metadata['comment'] = audio.get('COMM', 'No Comment').text[0] if audio.get('COMM') else 'No Comment'

                # Extract duration
                mp3_audio = MP3(self.music_file)
                metadata['duration'] = int(mp3_audio.info.length)
                metadata['file_type'] = str(file_extension)

            elif file_extension == 'ogg':
                audio = OggVorbis(self.music_file)
                metadata['title'] = audio.get('title', ['Unknown Title'])[0]
                metadata['artist'] = audio.get('artist', ['Unknown Artist'])[0]
                metadata['album'] = audio.get('album', ['Unknown Album'])[0]
                metadata['year'] = audio.get('date', ['Unknown Year'])[0]
                metadata['genre'] = audio.get('genre', ['Unknown Genre'])[0]
                metadata['track_number'] = audio.get('tracknumber', ['Unknown Track Number'])[0]
                metadata['comment'] = audio.get('comment', ['No Comment'])[0]

                # Extract duration
                metadata['duration'] = int(audio.info.length)
                metadata['file_type'] = str(file_extension)
                metadata['file_type'] = str(file_extension)                                

            else:
                raise ValueError("Unsupported file format")

        except Exception as e:
            print(f"Error reading metadata: {e}")

        return metadata
    
    def filterSongs(self):
        search_text = self.search_bar.text().lower()
        
        for row in range(self.songTableWidget.rowCount()):
            match = False
            
            for column in range(self.songTableWidget.columnCount() - 1):
                item = self.songTableWidget.item(row, column)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.songTableWidget.setRowHidden(row, not match)
            
        # Clear the search bar and reset the placeholder text
        self.search_bar.clear()
        self.search_bar.setPlaceholderText("Search...")
        
    def cleanDetails(self):
        # clear the remaining from previous play
        self.lrcPlayer.file = None
        self.player.player.stop()
        self.track_display.setText("No Track Playing")
        self.image_display.clear()
        self.song_details.clear()

    def initialize_database(self):
        # Connect to the SQLite database (creates the file if it doesn't exist)
        self.conn = sqlite3.connect(os.path.join(self.config_path, "songs.db"))
        self.cursor = self.conn.cursor()

        # Create the table for storing song metadata if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                title TEXT,
                artist TEXT,
                album TEXT,
                year TEXT,
                genre TEXT,
                track_number TEXT,
                duration INTEGER,
                file_path TEXT PRIMARY KEY,
                file_type TEXT
            )
        ''')
        self.conn.commit()

    def loadSongs(self, load_again=False): # getting songs recursively
        self.initialize_database()

        if load_again:
            self.cleanDetails()
            self.songTableWidget.clear()
            self.songTableWidget.setRowCount(0)
            self.songTableWidget.setHorizontalHeaderLabels(
                ['Title', 'Artist', 'Album', 'Year', 'Genre', 'Track Number', 'Duration', 'Media Type']
            )
            
        if self.directory is None:
            return

        media_extensions = {'.mp3', '.ogg', '.wav', '.flac', '.aac', '.m4a'}
        media_files = []

        # Recursively find all media files
        for root, _, files in os.walk(self.directory):
            for file in files:
                if os.path.splitext(file)[1].lower() in media_extensions:
                    media_files.append(os.path.join(root, file))

        songs_by_artist = defaultdict(list)

        # Check if the database already has the songs stored
        for item_path in media_files:
            self.cursor.execute('SELECT * FROM songs WHERE file_path=?', (item_path,))
            result = self.cursor.fetchone()

            if result:
                # If the song is already in the database, use the stored metadata
                metadata = {
                    'title': result[0],
                    'artist': result[1],
                    'album': result[2],
                    'year': result[3],
                    'genre': result[4],
                    'track_number': result[5],
                    'duration': result[6],
                    'file_type': result[8]
                }
            else:
                # Otherwise, extract the metadata and store it in the database
                self.music_file = item_path
                metadata = self.get_metadata()

                self.cursor.execute('''
                    INSERT INTO songs (title, artist, album, year, genre, track_number, duration, file_path, file_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata['title'],
                    metadata['artist'],
                    metadata['album'],
                    str(metadata['year']),
                    metadata['genre'],
                    metadata['track_number'],
                    metadata['duration'],
                    item_path,
                    metadata['file_type']
                ))
                self.conn.commit()

            artist = metadata['artist'] if metadata['artist'] else 'Unknown Artist'
            album = metadata['album'] if metadata['album'] else 'Unknown Album'
            track_number = metadata['track_number']
            songs_by_artist[artist].append((album, track_number, item_path, metadata))

        # Sort artists alphabetically, then albums, and finally by track number
        for artist in sorted(songs_by_artist.keys()):
            songs_by_album = defaultdict(list)
            for album, track_number, item_path, metadata in songs_by_artist[artist]:
                songs_by_album[album].append((track_number, item_path, metadata))

            for album in sorted(songs_by_album.keys()):
                # Insert a row with the album name (same as your current implementation)
                row_position = self.songTableWidget.rowCount()
                self.songTableWidget.insertRow(row_position)
                album_name_item = QTableWidgetItem(f"Album Title: [{album}]")

                # funcky cool font for album title
                QFontDatabase.addApplicationFont(os.path.join(self.script_path, "fonts/KOMIKAX_.ttf"))
                font = QFont("Komika Axis", 10)

                album_name_item.setFont(font)
                album_name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

                # Disable item interaction
                album_name_item.setFlags(album_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

                # Set the text color to your desired color (e.g., blue)
                # album_name_item.setForeground(QColor('#403e3e'))

                # Optionally, set the background color too
                # album_name_item.setBackground(QColor('#302121'))

                self.songTableWidget.setSpan(row_position, 0, 1, self.songTableWidget.columnCount())
                self.songTableWidget.setItem(row_position, 0, album_name_item)

                sorted_songs = sorted(songs_by_album[album], key=lambda x: extract_track_number(x[0]))

                for track_number, item_path, metadata in sorted_songs:
                    # Insert song data into the QTableWide (same as your current implementation)
                    row_position = self.songTableWidget.rowCount()
                    self.songTableWidget.insertRow(row_position)

                    title_item = QTableWidgetItem(metadata['title'])
                    title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 0, title_item)

                    artist_item = QTableWidgetItem(metadata['artist'])
                    artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 1, artist_item)

                    album_item = QTableWidgetItem(metadata['album'])
                    album_item.setFlags(album_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 2, album_item)

                    year_item = QTableWidgetItem(str(metadata['year']))
                    year_item.setFlags(year_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 3, year_item)

                    genre_item = QTableWidgetItem(metadata['genre'])
                    genre_item.setFlags(genre_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 4, genre_item)

                    track_number_item = QTableWidgetItem(metadata['track_number'])
                    track_number_item.setFlags(track_number_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 5, track_number_item)

                    minutes, seconds = divmod(metadata['duration'], 60)
                    duration_formatted = f"{minutes}:{seconds:02d}"
                    duration_item = QTableWidgetItem(duration_formatted)
                    duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 6, duration_item)

                    # Add the file path to the hidden column
                    file_path_item = QTableWidgetItem(item_path)
                    file_path_item.setFlags(file_path_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 7, file_path_item)
                    
                    file_type_item = QTableWidgetItem(metadata['file_type'])
                    file_type_item.setFlags(file_type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.songTableWidget.setItem(row_position, 8, file_type_item)

        self.conn.close()
                    
    def updateInformations(self):
        self.updateDisplayData()
        self.extract_and_set_album_art()
        self.updateSongDetails()                                        
                                   
    def get_music_file_from_click(self, item):
        row = item.row()
        self.file_path = self.songTableWidget.item(row, 7).text()  # Retrieve the file path from the hidden column
        self.music_file = self.file_path
        
        return self.file_path
    
    def handleRowSingleClick(self, item):
        if "Album Title: " in item.text():
            return
        else:
            self.get_music_file_from_click(item)
            self.updateInformations()    

    def handleRowDoubleClick(self, item):
        if "Album Title: " in item.text():
            return
        else:
            self.get_music_file_from_click(item)
            self.updateInformations()
            self.get_lrc_file()
            self.player.update_music_file(self.music_file)
            self.play_song()
            
    def play_song(self):
        self.player.play()
        self.lrcPlayer.sync_lyrics(self.lrc_file)   
                    
            
    def on_progress_bar_double_click(self):
        print("Progress bar was double-clicked!")
        if self.lrcPlayer.lrc_display is not None: 
            pass 
        else:
            self.lrcPlayer.startUI(self, self.lrc_file)
            # Add your desired functionality here

    def seekBack(self):
        self.player.seek_backward()

    def seekForward(self):
        self.player.seek_forward()

    def play_pause(self):
        self.player.play_pause_music(self.play_pause_button)

    def connect_progressbar_signals(self):
        # Connect signals for the progress bar and slider
        self.player.player.positionChanged.connect(self.updateProgressBar)
        self.player.player.durationChanged.connect(self.updateProgressBarRange)

    def updateProgressBar(self, position):
        # Update the progress bar and slider values based on the current position
        self.progress_bar.setValue(position)
        self.slider.setValue(position)

        # Calculate current time and total time
        current_time = format_time(position // 1000)  # Convert from ms to seconds
        total_time = format_time(self.player.get_duration() // 1000)  # Total duration in seconds

        # Update the progress bar format to display time
        self.progress_bar.setFormat(f"{current_time} / {total_time}")

    def updateProgressBarRange(self, duration):
        # Set the range of the progress bar and slider based on the media duration
        self.progress_bar.setRange(0, duration)
        self.slider.setRange(0, duration)

    def set_position(self, position):
        # Set the media player position when the slider is moved
        self.player.player.setPosition(position)
        
    def get_lrc_file(self):
        if self.music_file.endswith(".ogg"):
            lrc = self.music_file.replace(".ogg", ".lrc")
        elif self.music_file.endswith(".mp3"):
            lrc = self.music_file.replace(".mp3", ".lrc")
        else:
            lrc = None

        if lrc and os.path.exists(lrc):
            self.lrc_file = lrc
        else:
            self.lrc_file = None
            self.lrcPlayer.file = None
            
    def double_click_on_image(self):
        album_window = AlbumImageWindow(self, self.passing_image, self.icon_path, self.music_file)
        album_window.exec()

    def extract_and_set_album_art(self):
        audio_file = File(self.music_file)
        if isinstance(audio_file, MP3):
            album_image_data = extract_mp3_album_art(audio_file)
        elif isinstance(audio_file, OggVorbis):
            album_image_data = extract_ogg_album_art(audio_file)
        elif isinstance(audio_file, FLAC):
            album_image_data = extract_flac_album_art(audio_file)
        elif audio_file.mime[0] == 'video/mp4':
            album_image_data = extract_mp4_album_art(audio_file)
        else:
            album_image_data = None

        if album_image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(album_image_data)
            self.passing_image = pixmap
            
            image_size = int(self.width() / 5) # extract image size from main window
            
            target_width = image_size
            target_height = image_size
            scaled_pixmap = pixmap.scaled(target_width, target_height,
                                          aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                          transformMode=Qt.TransformationMode.SmoothTransformation)

            self.image_display.setPixmap(scaled_pixmap)
            self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
        else:
            self.image_display.setText("No Album Art Found")