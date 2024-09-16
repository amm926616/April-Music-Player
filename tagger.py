from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QWidget, QLabel, QPushButton, QTreeWidgetItem
from PyQt6.QtCore import Qt
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, TRCK


def tag_file(file_path, metadata):
    # Determine the file type and initialize the appropriate audio object
    if file_path.lower().endswith('.mp3'):
        audio = ID3(file_path)
        # Update metadata using ID3 frames
        audio['TIT2'] = TIT2(encoding=3, text=metadata.get('title', ''))
        audio['TPE1'] = TPE1(encoding=3, text=metadata.get('artist', ''))
        audio['TALB'] = TALB(encoding=3, text=metadata.get('album', ''))
        audio['TCON'] = TCON(encoding=3, text=metadata.get('genre', ''))
        audio['TDRC'] = TDRC(encoding=3, text=metadata.get('year', ''))
        audio['TRCK'] = TRCK(encoding=3, text=metadata.get('track_number', ''))
        audio.save()

    elif file_path.lower().endswith('.flac'):
        audio = FLAC(file_path)
        # Update metadata using FLAC fields
        audio['title'] = metadata.get('title', '')
        audio['artist'] = metadata.get('artist', '')
        audio['album'] = metadata.get('album', '')
        audio['genre'] = metadata.get('genre', '')
        audio['date'] = metadata.get('year', '')
        audio['tracknumber'] = metadata.get('track_number', '')
        audio.save()

    elif file_path.lower().endswith('.ogg'):
        audio = OggVorbis(file_path)
        # Update metadata using OggVorbis fields
        audio['title'] = metadata.get('title', '')
        audio['artist'] = metadata.get('artist', '')
        audio['album'] = metadata.get('album', '')
        audio['genre'] = metadata.get('genre', '')
        audio['date'] = metadata.get('year', '')
        audio['tracknumber'] = metadata.get('track_number', '')
        audio.save()

    else:
        print("Unsupported file type.")
        return

class TagDialog(QDialog):
    def __init__(self, parent=None, file_path=None, songTableWidget=None, albumTreeWidget=None, db_cursor=None):
        super().__init__(parent)
        self.tracknumber_edit = None
        self.year_edit = None
        self.genre_edit = None
        self.album_edit = None
        self.artist_edit = None
        self.title_edit = None
        self.songTableWidget = songTableWidget
        self.albumTreeWidget = albumTreeWidget  # Reference to your QTreeWidget
        self.db_cursor = db_cursor  # Database cursor for updating the metadata
        self.setWindowTitle("Edit Metadata")
        self.file_path = file_path
        self.metadata = {}

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create input fields for metadata
        self.title_edit = QLineEdit(self)
        self.artist_edit = QLineEdit(self)
        self.album_edit = QLineEdit(self)
        self.genre_edit = QLineEdit(self)
        self.year_edit = QLineEdit(self)
        self.tracknumber_edit = QLineEdit(self)

        layout.addWidget(QLabel("Title:", self))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("Artist:", self))
        layout.addWidget(self.artist_edit)
        layout.addWidget(QLabel("Album:", self))
        layout.addWidget(self.album_edit)
        layout.addWidget(QLabel("Genre:", self))
        layout.addWidget(self.genre_edit)
        layout.addWidget(QLabel("Year:", self))
        layout.addWidget(self.year_edit)
        layout.addWidget(QLabel("Track Number:", self))
        layout.addWidget(self.tracknumber_edit)

        # Add OK and Cancel buttons
        buttons = QWidget(self)
        buttons_layout = QVBoxLayout(buttons)
        
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.on_accept)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Pre-fill the dialog with existing metadata
        if self.file_path:
            self.populate_metadata()

    def populate_metadata(self):
        # Determine the file type
        if self.file_path.lower().endswith('.mp3'):
            audiofile = ID3(self.file_path)
            
            # Fetch metadata using ID3 tags
            title = audiofile.get('TIT2')  # Title
            artist = audiofile.get('TPE1')  # Artist
            album = audiofile.get('TALB')  # Album
            genre = audiofile.get('TCON')  # Genre
            year = audiofile.get('TDRC')  # Year/Date
            track_number = audiofile.get('TRCK')  # Track number

            # Set text fields, safely extracting text from ID3 tags
            self.title_edit.setText(title.text[0] if title else '')
            self.artist_edit.setText(artist.text[0] if artist else '')
            self.album_edit.setText(album.text[0] if album else '')
            self.genre_edit.setText(genre.text[0] if genre else '')
            
            # For the year (TDRC), convert ID3TimeStamp to string if it exists
            self.year_edit.setText(str(year.text[0]) if year else '')
            
            # Track number (TRCK) is also handled the same way
            self.tracknumber_edit.setText(track_number.text[0] if track_number else '')

        elif self.file_path.lower().endswith('.flac'):
            audiofile = FLAC(self.file_path)
            self.title_edit.setText(audiofile.get('title', [''])[0] if 'title' in audiofile else '')
            self.artist_edit.setText(audiofile.get('artist', [''])[0] if 'artist' in audiofile else '')
            self.album_edit.setText(audiofile.get('album', [''])[0] if 'album' in audiofile else '')
            self.genre_edit.setText(audiofile.get('genre', [''])[0] if 'genre' in audiofile else '')
            self.year_edit.setText(audiofile.get('date', [''])[0] if 'date' in audiofile else '')
            self.tracknumber_edit.setText(audiofile.get('tracknumber', [''])[0] if 'tracknumber' in audiofile else '')

        elif self.file_path.lower().endswith('.ogg'):
            audiofile = OggVorbis(self.file_path)
            self.title_edit.setText(audiofile.get('title', [''])[0] if 'title' in audiofile else '')
            self.artist_edit.setText(audiofile.get('artist', [''])[0] if 'artist' in audiofile else '')
            self.album_edit.setText(audiofile.get('album', [''])[0] if 'album' in audiofile else '')
            self.genre_edit.setText(audiofile.get('genre', [''])[0] if 'genre' in audiofile else '')
            self.year_edit.setText(audiofile.get('date', [''])[0] if 'date' in audiofile else '')
            self.tracknumber_edit.setText(audiofile.get('tracknumber', [''])[0] if 'tracknumber' in audiofile else '')

        else:
            print("Unsupported file type.")
            return

    def get_user_added_metadata(self):
        return {
            'title': self.title_edit.text(),
            'artist': self.artist_edit.text(),
            'album': self.album_edit.text(),
            'genre': self.genre_edit.text(),
            'year': self.year_edit.text(),
            'track_number': self.tracknumber_edit.text()
        }

    def on_accept(self):
        # Tag the file with the new metadata
        metadata = self.get_user_added_metadata()
        tag_file(self.file_path, metadata)

        # Update the current row in the song table
        self.albumTreeWidget.updateSongMetadata(self.file_path, metadata)
        
        # Accept the dialog
        self.accept()
        


            
