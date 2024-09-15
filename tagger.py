from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

class TagDialog(QDialog):
    def __init__(self, parent=None, file_path=None, songTableWidget=None, albumTreeWidget=None, db_cursor=None):
        super().__init__(parent)
        self.songtablewidget = songTableWidget
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
        elif self.file_path.lower().endswith('.flac'):
            audiofile = FLAC(self.file_path)
        elif self.file_path.lower().endswith('.ogg'):
            audiofile = OggVorbis(self.file_path)
        else:
            print("Unsupported file type.")
            return

        self.title_edit.setText(audiofile.get('title', [''])[0] if 'title' in audiofile else '')
        self.artist_edit.setText(audiofile.get('artist', [''])[0] if 'artist' in audiofile else '')
        self.album_edit.setText(audiofile.get('album', [''])[0] if 'album' in audiofile else '')
        self.genre_edit.setText(audiofile.get('genre', [''])[0] if 'genre' in audiofile else '')
        self.year_edit.setText(audiofile.get('date', [''])[0] if 'date' in audiofile else '')
        self.tracknumber_edit.setText(audiofile.get('track_number', [''])[0] if 'track_number' in audiofile else '')

    def get_metadata(self):
        return {
            'title': self.title_edit.text(),
            'artist': self.artist_edit.text(),
            'album': self.album_edit.text(),
            'genre': self.genre_edit.text(),
            'year': self.year_edit.text(),
            'track_number': self.tracknumber_edit.text()
        }

    def tag_file(self, file_path, metadata):
        if file_path.lower().endswith('.mp3'):
            audio = ID3(file_path)
        elif file_path.lower().endswith('.flac'):
            audio = FLAC(file_path)
        elif file_path.lower().endswith('.ogg'):
            audio = OggVorbis(file_path)
        else:
            print("Unsupported file type.")
            return

        audio['title'] = metadata['title']
        audio['artist'] = metadata['artist']
        audio['album'] = metadata['album']
        audio['genre'] = metadata['genre']
        audio['date'] = metadata['year']
        audio['track_number'] = metadata['track_number']
        audio.save()

    def update_current_row(self):
        # Retrieve updated metadata from the dialog
        metadata = self.get_metadata()
        
        # Update each column in the current row of the song table widget
        row = self.songtablewidget.currentRow()
        self.songtablewidget.item(row, 0).setText(metadata['title'])
        self.songtablewidget.item(row, 1).setText(metadata['artist'])
        self.songtablewidget.item(row, 2).setText(metadata['album'])
        self.songtablewidget.item(row, 3).setText(metadata['genre'])
        self.songtablewidget.item(row, 4).setText(metadata['year'])
        self.songtablewidget.item(row, 5).setText(metadata['track_number'])

    def update_tree_and_database(self):
        # Retrieve the updated metadata
        metadata = self.get_metadata()

        # Update the QTreeWidgetItem
        tree_items = self.albumTreeWidget.tree_widget.findItems(self.file_path, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive, 2)
        if tree_items:
            tree_item = tree_items[0]  # Assuming only one match
            tree_item.setText(0, metadata['title'])
            tree_item.setText(1, metadata['artist'])
            tree_item.setText(2, metadata['album'])

        # Update the database
        query = """
        UPDATE songs 
        SET title = ?, artist = ?, album = ?, genre = ?, year = ?, track_number = ? 
        WHERE file_path = ?
        """
        self.db_cursor.execute(query, (
            metadata['title'], metadata['artist'], metadata['album'],
            metadata['genre'], metadata['year'], metadata['track_number'],
            self.file_path
        ))

    def on_accept(self):
        # Tag the file with the new metadata
        metadata = self.get_metadata()
        self.tag_file(self.file_path, metadata)

        # Update the current row in the song table
        self.update_current_row()

        # Update the tree widget and database
        self.update_tree_and_database()

        # Accept the dialog
        self.accept()
