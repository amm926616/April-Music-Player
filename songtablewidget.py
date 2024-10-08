from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt6.QtGui import QKeyEvent, QFont
from PyQt6.QtCore import Qt
import os
import json


class SongTableWidget(QTableWidget):
    def __init__(self, parent=None, rowDoubleClick=None, seekRight=None, seekLeft=None, play_pause=None,
                 config_path=None, screenheight=None):
        self.parent = parent
        self.rowDoubleClick = rowDoubleClick
        self.seekRight = seekRight
        self.seekLeft = seekLeft
        self.play_pause = play_pause
        self.song_playing_row = None
        self.files_on_playlist = []
        self.config_path = config_path
        self.json_file = os.path.join(self.config_path, "configs", "table_data.json")
        super().__init__(parent)

        # Hide the vertical header (row numbers)
        self.verticalHeader().setVisible(False)

        # Always show the vertical scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        background_image = "700x700.png"

        if screenheight > 1200:
            background_image = "900x900.png"
        elif 1080 <= screenheight < 1200:
            background_image = "700x700.png"
        elif 700 <= screenheight < 800:
            background_image = "500x500.png"
                        
        # Set the background image on the viewport (the visible area of the table)        
        background_image_path = os.path.join(self.parent.script_path, "icons", background_image)
        print(background_image_path)

        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            background_image_path = background_image_path.replace("\\", "/")  # တော်တော်သောက်လုပ်ရှပ်တဲ့ window

        self.viewport().setStyleSheet(f"""
            background-image: url({background_image_path});
            background-repeat: no-repeat;
            background-position: center;
            background-size: fill;  /* Ensures the SVG fits within the viewport */
        """)

        # load the previous tabledata from init method. 
        self.load_table_data()
        self.setSortingEnabled(False)  # Disable default sorting to use custom sorting

    def save_currently_playing_song(self):
        currently_playing_song = self.parent.music_file
        current_position_in_second = self.parent.music_player.get_current_time()
        data = {currently_playing_song: current_position_in_second}
        if currently_playing_song is None:
            return
        else:
            self.parent.ej.edit_value("last_played_song", data)
            print(f"saved {currently_playing_song} to config file")

    def load_table_data(self):
        print("Started loading table data")

        # Check if the JSON file exists
        if not os.path.exists(self.json_file):
            print(f"File {self.json_file} does not exist.")
            return 0

        try:
            # Open and load the JSON data
            with open(self.json_file, 'r') as file:
                data = json.load(file)
                if not data:
                    print("Empty data in JSON file.")
                    return 0

        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.json_file}")
            return 0

        # Clear existing table content
        self.clearContents()
        self.setRowCount(0)

        # Set up the row and column counts based on the loaded data
        row_count = len(data)
        if row_count == 0:
            print("No data to load.")
            return 0

        column_count = len(data[0]["items"]) if data else 0
        self.setColumnCount(column_count)

        # Populate the table widget with the loaded data
        for row, row_data in enumerate(data):
            self.insertRow(row)

            for column, item_text in enumerate(row_data["items"]):
                table_item = QTableWidgetItem(item_text)

                if row_data["row_type"] == "album_title":
                    # Album Title row: Set font, colspan, and disable selection
                    table_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

                    # Restore the font
                    if row_data.get("font"):
                        font = QFont()
                        font.fromString(row_data["font"])
                        table_item.setFont(font)

                    # Restore the colspan
                    if row_data.get("colspan"):
                        self.setSpan(row, 0, 1, row_data["colspan"])

                    # Add the item to the first column (since it spans all columns)
                    self.setItem(row, column, table_item)

                else:
                    # Normal rows: Add items and disable editing
                    table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.setItem(row, column, table_item)

            if row_data["row_type"] != "album_title":
                file = row_data["items"][7]  # making sure None is not passed
                if file is not None:
                    self.files_on_playlist.append(file)

        print("Finished loading table data.")
        print("Trying to load last played song.")

    def save_table_data(self):
        # Get the current data from the table widget
        data = []

        row_count = self.rowCount()
        column_count = self.columnCount()

        # Iterate over rows and columns to extract data and metadata
        for row in range(row_count):
            row_data = {
                "items": [],
                "row_type": "normal",  # Default is a normal row
                "font": None,  # Default is no special font
                "colspan": None  # Default is no colspan
            }

            for column in range(column_count):
                item = self.item(row, column)
                if item:
                    row_data["items"].append(item.text())

                    # If this is an "Album Title" row, capture its metadata
                    if item.text().startswith("Album Title:"):
                        row_data["row_type"] = "album_title"
                        row_data["font"] = item.font().toString()  # Save font settings as string
                        row_data["colspan"] = self.columnSpan(row, column)
                else:
                    row_data["items"].append("")  # Handle empty cells

            data.append(row_data)

        # Save the data and metadata to a file
        try:
            with open(self.json_file, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"Data successfully saved to {self.json_file}")
            file.close()
        except IOError as e:
            print(f"Failed to save data to {self.json_file}: {e}")

        self.save_currently_playing_song()

    @staticmethod
    def get_table_data(table_widget):
        # Get the number of rows and columns
        row_count = table_widget.rowCount()
        column_count = table_widget.columnCount()

        # Create a list to store table data
        table_data = []

        # Iterate over rows and columns to extract the data
        for row in range(row_count):
            row_data = []
            for column in range(column_count):
                item = table_widget.item(row, column)  # Get the QTableWidgetItem
                if item:
                    row_data.append(item.text())  # Get the text from the item
                else:
                    row_data.append('')  # Handle empty cells
            table_data.append(row_data)

        return table_data

    def get_previous_song_object(self, clicking=False):
        if self.parent.music_player.music_on_repeat and not clicking:
            self.parent.music_player.music_player.setPosition(0)
            self.parent.music_player.music_player.play()
            return

        if self.song_playing_row is None:
            return

        current_row = self.song_playing_row
        previous_row = current_row - 1

        # Ensure next_row is within bounds
        if previous_row < 0:
            print("The row count is", self.rowCount())
            print("previous row is ", previous_row)
            if self.parent.music_player.playlist_on_loop or self.parent.music_player.music_on_repeat:
                print("The row count is ", self.rowCount())
                previous_row = self.rowCount()
            elif self.parent.music_player.music_on_shuffle:
                self.parent.play_random_song()
            else:
                self.parent.stop_song()
                self.parent.lrcPlayer.media_lyric.setText(
                    self.parent.lrcPlayer.media_font.get_formatted_text(self.parent.music_player.eop_text))

                # Check if the item exists
        item = self.item(previous_row, 0)

        if item is None:
            print("In previous song, the item is none")
            self.parent.stop_song()
            self.parent.lrcPlayer.media_lyric.setText(
                self.parent.lrcPlayer.media_font.get_formatted_text(self.parent.music_player.eop_text))
            return

        if "Album Title:" in item.text():
            previous_row -= 1
            if previous_row < 0:
                return None  # Or handle the case where no more rows are available
            item = self.item(previous_row, 7)

        # Set the new current row
        self.setCurrentCell(previous_row, 7)

        return item

    def get_next_song_object(self, fromstart=False, clicking=None):
        if self.parent.music_player.music_on_repeat and not clicking:
            self.parent.music_player.music_player.setPosition(0)
            self.parent.music_player.music_player.play()
            return

        if self.song_playing_row is None:
            return

        current_row = self.song_playing_row
        next_row = current_row + 1

        if fromstart:
            next_row = 0

        # Ensure next_row is within bounds
        if next_row >= self.rowCount():
            if self.parent.music_player.playlist_on_loop or self.parent.music_player.music_on_repeat:
                next_row = 0
            elif self.parent.music_player.music_on_shuffle:
                self.parent.play_random_song()
            else:
                self.parent.stop_song()
                self.parent.lrcPlayer.media_lyric.setText(
                    self.parent.lrcPlayer.media_font.get_formatted_text(self.parent.music_player.eop_text))

                # Check if the item exists
        item = self.item(next_row, 0)

        if item is None:
            self.parent.stop_song()
            self.parent.lrcPlayer.media_lyric.setText(
                self.parent.lrcPlayer.media_font.get_formatted_text(self.parent.music_player.eop_text))
            return

        if "Album Title:" in item.text():
            next_row += 1
            if next_row >= self.rowCount():
                return None  # Or handle the case where no more rows are available
            item = self.item(next_row, 7)

        # Set the new current row
        self.setCurrentCell(next_row, 7)

        return item

    def setNextRow(self, currentItem):
        if currentItem:
            if "Album Title:" in currentItem.text():
                next_row = self.currentRow() - 1  # Get the previous row index
                self.setCurrentCell(next_row, 7)  # Set the current cell in the next row and column 7

                # Return the item at next_row and column 7
                return self.item(next_row, 7)
        else:
            return None

    def setPreviousRow(self, currentItem):
        if currentItem:
            if "Album Title:" in currentItem.text():
                previous_row = self.currentRow() + 1
                self.setCurrentCell(previous_row, 7)

                return self.item(previous_row, 7)
        else:
            return None

    def scroll_to_current_row(self):
        """Scroll to and highlight the current row."""
        if self.song_playing_row is not None:
            current_item = self.item(self.song_playing_row, 7)
            if current_item:
                # Scroll to the item
                self.scrollToItem(current_item, self.ScrollHint.PositionAtCenter)
                self.setCurrentCell(self.song_playing_row, 7)
        else:
            return

    def scroll_to_and_highlight_multiple_rows(self, rows: list[int]):
        """
        Scrolls to and highlights multiple rows in the QTableWidget.

        :param rows: A list of row indices to scroll to and highlight
        """
        self.setFocus()

        # Set to MultiSelection mode
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        for row in rows:
            # Scroll to the row and position it at the center
            self.scrollToItem(self.item(row, 7), self.ScrollHint.PositionAtCenter)

            # Select the row
            self.selectRow(row)

        # Restore the original selection mode
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def delete_selected_rows(self):
        # Get a list of selected rows
        selected_rows = set(index.row() for index in self.selectedIndexes())
        selected_album_names = set()
        album_title_rows = []

        # Collect album names and corresponding album title rows
        for i in selected_rows:
            album_name_item = self.item(i, 2)  # Assuming album name is in column 2
            if album_name_item:  # Check if the item exists
                album_name = album_name_item.text()  # Extract the text (album name)
                selected_album_names.add(album_name)
                album_title_rows.append(f"Album Title: [{album_name}]")

        # Create a set to keep track of rows to remove
        rows_to_remove = set()

        # Collect all rows to be removed
        for row in sorted(selected_rows, reverse=True):
            # Get the file path from the hidden column (assuming file path is in the 7th column, index 7)
            file_path_item = self.item(row, 7)
            if file_path_item:
                file_path = file_path_item.text()
                # Remove the file path from files_on_playlist
                if file_path in self.files_on_playlist:
                    self.files_on_playlist.remove(file_path)
                    # removing songs from random_song_list on the way
                    if self.parent.random_song_list:
                        self.parent.random_song_list.remove(file_path)

            # Add the row to the set of rows to remove
            rows_to_remove.add(row)

        # Remove the selected rows
        for row in sorted(rows_to_remove, reverse=True):
            self.removeRow(row)

        # Check for any remaining album title rows without related songs
        for album_name in selected_album_names:
            album_title_row_text = f"Album Title: [{album_name}]"
            matched_songs_with_same_album_name = self.findItems(album_name, Qt.MatchFlag.MatchExactly)

            # Collect rows that still have songs with the same album name
            same_album_name_songs = set()
            for item in matched_songs_with_same_album_name:
                if item.column() == 2:
                    same_album_name_songs.add(item.row())

            # If no related songs are left, remove the album title row
            if not same_album_name_songs:
                matched_album_title_row = self.findItems(album_title_row_text, Qt.MatchFlag.MatchExactly)
                for item in matched_album_title_row:
                    self.removeRow(item.row())

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            super().keyPressEvent(
                event)  # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("UP key pressed")
            self.setNextRow(self.currentItem())

        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected_rows()

        elif event.key() == Qt.Key.Key_0 or event.key() == Qt.Key.Key_Home:
            print("keyboard r pressing")
            self.parent.music_player.music_player.setPosition(0)  # set position to start

        elif event.key() == Qt.Key.Key_Down:
            super().keyPressEvent(
                event)  # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("DOWN key pressed")
            self.setPreviousRow(self.currentItem())

        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.hasFocus():
                self.rowDoubleClick(self.item(self.currentRow(), 7))
            else:
                pass

        elif event.key() == Qt.Key.Key_Right:
            self.seekRight()

        elif event.key() == Qt.Key.Key_Left:
            self.seekLeft()

        elif event.key() == Qt.Key.Key_Space:
            self.parent.play_pause()

        elif event.key() == Qt.Key.Key_Enter:
            self.rowDoubleClick()

        elif event.key() == Qt.Key.Key_G and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.clearSelection()
            self.scroll_to_current_row()

        elif event.key() == Qt.Key.Key_F2:
            self.parent.activate_file_tagger()

        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
