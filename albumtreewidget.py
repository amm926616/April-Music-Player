from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QLineEdit, QTreeWidget, QVBoxLayout, QTableWidgetItem
from PyQt6.QtGui import QFontDatabase, QFont, QKeyEvent
from PyQt6.QtCore import Qt
from collections import defaultdict
import sqlite3
import os
from fuzzywuzzy import fuzz

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

class AlbumTreeWidget(QWidget):
    ARTIST_ROLE = Qt.ItemDataRole.UserRole + 1
    ALBUM_ROLE = Qt.ItemDataRole.UserRole + 2
    SONG_ROLE = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None, songTableWidget=None):
        super().__init__(parent)
        self.songTableWidget = songTableWidget
        self.matched_item = None
        self.config_path = os.path.join(os.path.expanduser("~"), '.config', 'april-music-player')
        self.conn = None
        self.cursor = None
        self.search_bar = QLineEdit()        
        self.initUI()
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.search_bar.hasFocus():
                self.on_item_double_clicked(self.matched_item)
                self.search_bar.clear()
                self.search_bar.setPlaceholderText("Search...")
            elif self.tree_widget.hasFocus():  # Check if the tree widget has focus
                selected_items = self.tree_widget.selectedItems()
                if selected_items:  # Make sure an item is selected
                    self.on_item_double_clicked(selected_items[0])  # Call the method for the selected item
        else:
            super().keyPressEvent(event)                    

    def filter_items(self):
        search_text = self.search_bar.text().lower()
        matched_songs = []  # List to store matched and visible songs
        matched_albums = []  # List to store matched and visible albums
        matched_artists = []  # List to store matched and visible artists

        def matches_search(text):
            if search_text in text.lower():
                return True
            if search_text and fuzz.partial_ratio(search_text, text.lower()) > 80:
                return True
            return False

        for i in range(self.tree_widget.topLevelItemCount()):
            artist_item = self.tree_widget.topLevelItem(i)
            artist_visible = False

            if matches_search(artist_item.text(0)):
                matched_artists.append(artist_item)

            for j in range(artist_item.childCount()):
                album_item = artist_item.child(j)
                album_visible = matches_search(album_item.text(0))
                artist_visible = artist_visible or album_visible

                if album_visible:
                    matched_albums.append(album_item)

                # Collect songs if they match the search text
                for k in range(album_item.childCount()):
                    song_item = album_item.child(k)
                    song_visible = matches_search(song_item.text(0))
                    song_item.setHidden(not song_visible)

                    if not song_item.isHidden():
                        matched_songs.append(song_item)

            artist_item.setHidden(not artist_visible)

        # Assign matched item
        if matched_songs:
            self.matched_item = matched_songs[0]
        elif matched_albums:
            self.matched_item = matched_albums[0]
        elif matched_artists:
            self.matched_item = matched_artists[0]
        else:
            self.matched_item = None
        
    def initUI(self):
        self.search_bar.setPlaceholderText("Search...")

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)  # Hide the header

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tree_widget)

        self.search_bar.textChanged.connect(self.filter_items)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)              
            
    def initialize_database(self):
        if self.conn:
            self.conn.close()  # Close the previous connection if it exists
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
                    
    def loadSongsToCollection(self, songs_by_artist):
        self.tree_widget.clear()  # Clear existing items

        for artist in sorted(songs_by_artist.keys()):
            artist_item = QTreeWidgetItem([artist])
            artist_item.setData(0, Qt.ItemDataRole.UserRole, self.ARTIST_ROLE)
            self.tree_widget.addTopLevelItem(artist_item)

            songs_by_album = defaultdict(list)
            for album, track_number, item_path, metadata in songs_by_artist[artist]:
                songs_by_album[album].append((track_number, item_path, metadata))

            for album in sorted(songs_by_album.keys()):
                album_item = QTreeWidgetItem([album])
                album_item.setData(0, Qt.ItemDataRole.UserRole, self.ALBUM_ROLE)
                artist_item.addChild(album_item)

                sorted_songs = sorted(songs_by_album[album], key=lambda x: extract_track_number(x[0]))
                for track_number, item_path, metadata in sorted_songs:
                    title = metadata['title']
                    track_item = QTreeWidgetItem([f"{track_number}. {title}"])
                    track_item.setData(0, Qt.ItemDataRole.UserRole, self.SONG_ROLE)
                    track_item.setData(0, Qt.ItemDataRole.UserRole + 4, item_path)  # Store file path
                    album_item.addChild(track_item)
                    
                    
    def on_item_double_clicked(self, item: QTreeWidgetItem):
        role = item.data(0, Qt.ItemDataRole.UserRole)
        file_path = item.data(0, Qt.ItemDataRole.UserRole + 4)  # Retrieve file path

        if role == self.ARTIST_ROLE:
            self.add_songs_by_artist(item.text(0))
        elif role == self.ALBUM_ROLE:
            self.add_songs_by_album(item.text(0))
        elif role == self.SONG_ROLE:
            if file_path:
                self.add_song_by_file_path(file_path)  # Use file path to add song
            else:
                print("No file path found for the selected song.")
        else:
            print(f"Unknown item double-clicked: {item.text(0)}")
            
        print("\nfiles_on_playlist:")    
        for i in self.songTableWidget.files_on_playlist:
            print(i)
                        
    def add_song_by_file_path(self, file_path):
        self.cursor.execute('SELECT * FROM songs WHERE file_path=?', (file_path,))
        song = self.cursor.fetchone()
        if song:
            
            file_path = song[7]  # file_path is at index 7

            # Check if the file_path is already in the playlist
            if file_path not in self.songTableWidget.files_on_playlist:
                self.songTableWidget.files_on_playlist.append(file_path)
                self.songTableWidget.insertRow(self.songTableWidget.rowCount())
                
            for i, data in enumerate(song):
                item = QTableWidgetItem(str(data))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.songTableWidget.setItem(self.songTableWidget.rowCount() - 1, i, item) 

    def add_songs_by_album(self, album):
        if not self.cursor:
            print("Database cursor is not initialized.")
            return

        self.cursor.execute('SELECT * FROM songs WHERE album=?', (album,))
        songs = self.cursor.fetchall()
        
        # Insert a row with the album name
        row_position = self.songTableWidget.rowCount()
        self.songTableWidget.insertRow(row_position)
        album_name_item = QTableWidgetItem(f"Album Title: [{album}]")

        # Set font for album title
        QFontDatabase.addApplicationFont(os.path.join(self.config_path, "fonts/KOMIKAX_.ttf"))
        font = QFont("Komika Axis", 10)
        album_name_item.setFont(font)
        album_name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        album_name_item.setFlags(album_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        self.songTableWidget.setSpan(row_position, 0, 1, self.songTableWidget.columnCount())
        self.songTableWidget.setItem(row_position, 0, album_name_item)

        sorted_songs = sorted(songs, key=lambda x: extract_track_number(x[5]))  # Sort by track_number

        for song in sorted_songs:
            self.add_song_row(song)

    def add_songs_by_artist(self, artist):
        if not self.cursor:
            print("Database cursor is not initialized.")
            return

        self.cursor.execute('SELECT * FROM songs WHERE artist=?', (artist,))
        songs = self.cursor.fetchall()
        
        sorted_albums = defaultdict(list)
        for song in songs:
            sorted_albums[song[2]].append(song)  # song[2] is the album

        for album, album_songs in sorted(sorted_albums.items()):
            # Insert a row with the album name
            row_position = self.songTableWidget.rowCount()
            self.songTableWidget.insertRow(row_position)
            album_name_item = QTableWidgetItem(f"Album Title: [{album}]")

            # Set font for album title
            QFontDatabase.addApplicationFont(os.path.join(self.config_path, "fonts/KOMIKAX_.ttf"))
            font = QFont("Komika Axis", 10)
            album_name_item.setFont(font)
            album_name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            album_name_item.setFlags(album_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            self.songTableWidget.setSpan(row_position, 0, 1, self.songTableWidget.columnCount())
            self.songTableWidget.setItem(row_position, 0, album_name_item)

            sorted_songs = sorted(album_songs, key=lambda x: extract_track_number(x[5]))  # Sort by track_number

            for song in sorted_songs:
                self.add_song_row(song)
                
    def add_song_row(self, song):
        # Insert song data into the QTableWidget
        row_position = self.songTableWidget.rowCount()
        self.songTableWidget.insertRow(row_position)

        # Assuming columns are: title, artist, album, year, genre, track_number, duration, file_path, file_type
        for i, data in enumerate(song):
            item = QTableWidgetItem(str(data))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songTableWidget.setItem(row_position, i, item)
            
        # Add the file path to the list
        file_path = song[7]  # Assuming file_path is at index 7
        if file_path not in self.songTableWidget.files_on_playlist:
            self.songTableWidget.files_on_playlist.append(file_path)                          