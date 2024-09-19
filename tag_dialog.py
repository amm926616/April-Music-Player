from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QLabel, QPushButton, QGroupBox, QHBoxLayout, QFormLayout
from PyQt6.QtGui import QKeyEvent, QIcon
from PyQt6.QtCore import Qt
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, TRCK, COMM


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

        # Add comment metadata (COMM frame) with required 'lang' and 'desc' fields
        audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata.get('comment', ''))

        # Save changes
        audio.save()

    elif file_path.lower().endswith('.flac'):
        audio = FLAC(file_path)
        # Update metadata using FLAC fields
        audio['title'] = metadata.get('title', '')
        audio['artist'] = metadata.get('artist', '')
        audio['album'] = metadata.get('album', '')
        audio['genre'] = metadata.get('genre', '')
        audio['date'] = metadata.get('year', '')
        audio['comment'] = metadata.get('comment', '')
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
        audio['comment'] = metadata.get('comment', '')        
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
        # Main layout
        layout = QVBoxLayout()

        # Group box for metadata input fields
        metadata_group = QGroupBox("Song's Metadata")
        metadata_layout = QFormLayout()

        # Create input fields for metadata with placeholder text
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter song title")
        self.artist_edit = QLineEdit(self)
        self.artist_edit.setPlaceholderText("Enter artist name")
        self.album_edit = QLineEdit(self)
        self.album_edit.setPlaceholderText("Enter album name")
        self.genre_edit = QLineEdit(self)
        self.genre_edit.setPlaceholderText("Enter genre")
        self.year_edit = QLineEdit(self)
        self.year_edit.setPlaceholderText("Enter year (e.g. 2024)")
        self.comment_edit = QLineEdit(self)
        self.comment_edit.setPlaceholderText("Add comment")
        self.tracknumber_edit = QLineEdit(self)
        self.tracknumber_edit.setPlaceholderText("Enter track number")

        # Add fields to form layout
        metadata_layout.addRow(QLabel("Title:"), self.title_edit)
        metadata_layout.addRow(QLabel("Artist:"), self.artist_edit)
        metadata_layout.addRow(QLabel("Album:"), self.album_edit)
        metadata_layout.addRow(QLabel("Genre:"), self.genre_edit)
        metadata_layout.addRow(QLabel("Year:"), self.year_edit)
        metadata_layout.addRow(QLabel("Comment"), self.comment_edit)
        metadata_layout.addRow(QLabel("Track Number:"), self.tracknumber_edit)

        # Add form layout to group box
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Add spacing between form and buttons
        layout.addSpacing(15)

        # Buttons layout (aligned horizontally)
        buttons_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK", self)
        ok_button.setIcon(QIcon("ok_icon.png"))  # Optional: Set icon if you have one
        ok_button.clicked.connect(self.on_accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.setIcon(QIcon("cancel_icon.png"))  # Optional: Set icon if you have one
        cancel_button.clicked.connect(self.close)

        # Add buttons to horizontal layout
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        # Add buttons layout to the main layout
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Pre-fill the dialog with existing metadata
        if self.file_path:
            self.populate_metadata()

    def populate_metadata(self):
        # Populate fields with existing metadata from file
        pass
                
    def keyPressEvent(self, event: QKeyEvent):            
        if event.key() == Qt.Key.Key_Escape:
            self.close()  
            
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.on_accept()
            
    def closeEvent(self, event):
        print("Cleaning up UI components")
        self.deleteLater()
        super(TagDialog, self).closeEvent(event)  # Call the base class closeEvent            

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
            comment = audiofile.get('COMM::eng')  # Comment (assuming language is 'eng')

            # Set text fields, safely extracting text from ID3 tags
            self.title_edit.setText(title.text[0] if title else '')
            self.artist_edit.setText(artist.text[0] if artist else '')
            self.album_edit.setText(album.text[0] if album else '')
            self.genre_edit.setText(genre.text[0] if genre else '')
            
            # For the year (TDRC), convert ID3TimeStamp to string if it exists
            self.year_edit.setText(str(year.text[0]) if year else '')
            
            # Track number (TRCK) is also handled the same way
            self.tracknumber_edit.setText(track_number.text[0] if track_number else '')
            
            # Set the comment if it exists (COMM::eng)
            self.comment_edit.setText(comment.text[0] if comment else '')

        elif self.file_path.lower().endswith('.flac'):
            audiofile = FLAC(self.file_path)
            self.title_edit.setText(audiofile.get('title', [''])[0] if 'title' in audiofile else '')
            self.artist_edit.setText(audiofile.get('artist', [''])[0] if 'artist' in audiofile else '')
            self.album_edit.setText(audiofile.get('album', [''])[0] if 'album' in audiofile else '')
            self.genre_edit.setText(audiofile.get('genre', [''])[0] if 'genre' in audiofile else '')
            self.year_edit.setText(audiofile.get('date', [''])[0] if 'date' in audiofile else '')
            self.tracknumber_edit.setText(audiofile.get('tracknumber', [''])[0] if 'tracknumber' in audiofile else '')
            self.comment_edit.setText(audiofile.get('comment', [''])[0] if 'comment' in audiofile else '')

        elif self.file_path.lower().endswith('.ogg'):
            audiofile = OggVorbis(self.file_path)
            self.title_edit.setText(audiofile.get('title', [''])[0] if 'title' in audiofile else '')
            self.artist_edit.setText(audiofile.get('artist', [''])[0] if 'artist' in audiofile else '')
            self.album_edit.setText(audiofile.get('album', [''])[0] if 'album' in audiofile else '')
            self.genre_edit.setText(audiofile.get('genre', [''])[0] if 'genre' in audiofile else '')
            self.year_edit.setText(audiofile.get('date', [''])[0] if 'date' in audiofile else '')
            self.tracknumber_edit.setText(audiofile.get('tracknumber', [''])[0] if 'tracknumber' in audiofile else '')
            self.comment_edit.setText(audiofile.get('comment', [''])[0] if 'comment' in audiofile else '')

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
            'comment': self.comment_edit.text(),
            'track_number': self.tracknumber_edit.text()
        }

    def on_accept(self):
        # Tag the file with the new metadata
        metadata = self.get_user_added_metadata()
        tag_file(self.file_path, metadata)

        # Update the current row in the song table
        self.albumTreeWidget.updateSongMetadata(self.file_path, metadata)
        
        self.parent.updateSongDetails()
        
        # Accept the dialog
        self.accept()
        self.close()