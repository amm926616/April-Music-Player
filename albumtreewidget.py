from PyQt6.QtWidgets import QTreeWidget, QVBoxLayout, QWidget, QLineEdit

class AlbumTreeWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create QTreeWidget
        # Create a search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")

        # Create a QTreeWidget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)  # Hide the header

        # Set up the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tree_widget)

        # Connect search bar text change signal to filter function
        self.search_bar.textChanged.connect(self.filter_items)
        
        
    def filter_items(self):
        search_text = self.search_bar.text().lower()

        # Loop through all top-level items (artists)
        for i in range(self.tree_widget.topLevelItemCount()):
            artist_item = self.tree_widget.topLevelItem(i)
            artist_visible = False

            # Loop through each album under the artist
            for j in range(artist_item.childCount()):
                album_item = artist_item.child(j)
                album_visible = search_text in album_item.text(0).lower()

                # Show/Hide the album based on the search text
                album_item.setHidden(not album_visible)

                if album_visible:
                    artist_visible = True

            # Show/Hide the artist based on whether any of their albums are visible
            artist_item.setHidden(not artist_visible)        



