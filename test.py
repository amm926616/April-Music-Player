from PyQt6.QtWidgets import QApplication, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from collections import defaultdict
import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Setup UI layout
        self.layout = QVBoxLayout(self)
        
        # Create and add search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.layout.addWidget(self.search_bar)

        # Create and add table widget
        self.songTableWidget = QTableWidget(self)
        self.layout.addWidget(self.songTableWidget)
        
        # Connect search bar textChanged signal to the search method
        self.search_bar.textChanged.connect(self.filterSongs)

        # Other initialization...
        
    def loadSongs(self, load_again=False):
        if load_again:
            # Clear the table before loading new items
            self.songTableWidget.clear()
            self.songTableWidget.setRowCount(0)
            self.songTableWidget.setHorizontalHeaderLabels(
                ['Title', 'Artist', 'Album', 'Year', 'Genre', 'Track Number', 'Duration', 'File Path']
            )

        if not self.directory:
            return

        media_extensions = {'.mp3', '.ogg', '.wav', '.flac', '.aac', '.m4a'}
        media_files = []

        # Recursively find all media files
        for root, _, files in os.walk(self.directory):
            for file in files:
                if os.path.splitext(file)[1].lower() in media_extensions:
                    media_files.append(os.path.join(root, file))

        songs_by_artist = defaultdict(list)

        for item_path in media_files:
            self.music_file = item_path
            metadata = self.get_metadata()

            # Group songs by artist and album
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
                # Insert a row with the album name
                row_position = self.songTableWidget.rowCount()
                self.songTableWidget.insertRow(row_position)
                album_name_item = QTableWidgetItem(f"[Album Title: {album}]")
                album_name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

                # Disable item interaction
                album_name_item.setFlags(album_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

                # Set the text color to your desired color (e.g., blue)
                # album_name_item.setForeground(QColor('#403e3e'))

                # Optionally, set the background color too
                album_name_item.setBackground(QColor('#302121'))

                self.songTableWidget.setSpan(row_position, 0, 1, self.songTableWidget.columnCount())
                self.songTableWidget.setItem(row_position, 0, album_name_item)

                sorted_songs = sorted(songs_by_album[album], key=lambda x: extract_track_number(x[0]))

                for track_number, item_path, metadata in sorted_songs:
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
        
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
