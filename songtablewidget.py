from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
import os

class SongTableWidget(QTableWidget):
    def __init__(self, parent=None, rowDoubleClick=None, seekRight=None, seekLeft=None, play_pause=None):
        self.parent = parent
        self.rowDoubleClick = rowDoubleClick
        self.seekRight = seekRight
        self.seekLeft = seekLeft
        self.play_pause = play_pause
        self.song_playing_row = None  
        self.files_on_playlist = []                 
                        
        super().__init__(parent)
        
        # Enable sorting and connect signal
        self.setSortingEnabled(True)
        
        header = self.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self.sort_table)   
             
        # Hide the vertical header (row numbers)
        self.verticalHeader().setVisible(False)  
        
        # Always show the vertical scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # self.setStyleSheet("""
        #     QTableWidget {
        #         background-color: transparent;  /* Make sure the table background is transparent */
        #     }
        #     QTableWidget::item {
        #         background-color: transparent;  /* Ensure that all table items are transparent */
        #         border: none;  /* Remove borders around cells */
        #     }
        #     QTableWidget::item:hover {
        #         background-color: rgba(200, 200, 255, 100);  /* Hover effect */
        #     }
        #     QTableWidget::item:selected {
        #         background-color: rgba(100, 150, 250, 150);  /* Selection color */
        #     }
        # """)
        
        # Set the background image on the viewport (the visible area of the table)        
        svg_file = os.path.join(self.parent.script_path, "icons", "resized.png")
        
        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            svg_file = svg_file.replace("\\", "/") # တော်တော်သောက်လုပ်ရှပ်တဲ့ window  
            
        self.viewport().setStyleSheet(f"""
            background-image: url({svg_file});
            background-repeat: no-repeat;
            background-position: center;
            background-size: fill;  /* Ensures the SVG fits within the viewport */
        """)

    #     # Make sure the cells are transparent
    #     self.make_cells_transparent()

    # def make_cells_transparent(self):
    #     """Ensure all cells have a transparent background."""
    #     for row in range(self.rowCount()):
    #         for col in range(self.columnCount()):
    #             item = self.item(row, col)
    #             if item:
    #                 item.setBackground(Qt.transparent)   
    
    def populate_table(self):
        # Assume this method populates the table and updates self.table_data
        # Example: Clear the table and reinsert data
        self.clearContents()
        self.setRowCount(0)
        
        # Add rows to the table and update self.table_data
        for row_data in self.table_data:
            row_position = self.rowCount()
            self.insertRow(row_position)
            for col_idx, item in enumerate(row_data):
                self.setItem(row_position, col_idx, QTableWidgetItem(item))
    
    def set_table_data(self, data):
        # Set the table data and populate the table
        self.table_data = data
        self.populate_table()

    def sort_table(self, column, order):
        # Separate album rows and song rows
        album_rows = [row for row in self.table_data if row[0].startswith('Album Title: ')]
        song_rows = [row for row in self.table_data if not row[0].startswith('Album Title: ')]
        
        # Sort song rows based on the specified column
        if order == Qt.AscendingOrder:
            song_rows.sort(key=lambda x: x[column])
        else:
            song_rows.sort(key=lambda x: x[column], reverse=True)
        
        # Combine album rows and sorted song rows
        sorted_data = album_rows + song_rows
        
        # Update the table data and repopulate it
        self.table_data = sorted_data
        self.populate_table()    
        
    def get_previous_song_object(self):
        if self.parent.player.music_on_shuffle:
            self.parent.play_random_song()
            return 
        
        if self.parent.player.music_on_repeat:
                self.parent.player.player.setPosition(0)
                self.parent.player.player.play() 
                return
            
        if self.song_playing_row is None:
            return            
                
        previous_row = self.song_playing_row - 1
        
        # Ensure next_row is within bounds
        if previous_row <= 0:
            return None  # Or handle the case where no more rows are available
        
        # Check if the item exists
        item = self.item(previous_row, 7)  
                
        if item is None:
            previous_row -= 1
            if previous_row <= 0:
                return None  # Or handle the case where no more rows are available
            item = self.item(previous_row, 7)
        
        # Set the new current row
        self.setCurrentCell(previous_row, 7)
        
        return item            
        
        
    def get_next_song_object(self, fromstart=None):
        if self.parent.player.music_on_shuffle:
            self.parent.play_random_song()
            return 
        
        if self.parent.player.music_on_repeat:
                self.parent.player.player.setPosition(0)
                self.parent.player.player.play() 
                return
            
        if self.song_playing_row is None:
            return
        
        current_row = self.song_playing_row
        next_row = current_row + 1
        
        if fromstart:
            next_row = 0
        
        # Ensure next_row is within bounds
        if next_row >= self.rowCount():
            if self.parent.player.playlist_on_loop or self.parent.player.music_on_repeat:
                next_row = 0
            elif self.parent.player.music_on_shuffle:
                self.parent.play_random_song()
            else:
                self.parent.stop_song()      
                self.parent.lrcPlayer.media_lyric.setText(self.parent.lrcPlayer.media_font.get_formatted_text("End Of Playlist"))            
                    
        # Check if the item exists
        item = self.item(next_row, 7)
        
        if item is None:
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
                self.setCurrentCell(next_row, 7)   # Set the current cell in the next row and column 7
                print("Next row ", next_row)
                
                # Return the item at next_row and column 7
                return self.item(next_row, 7)
        else:
            return None

            
    def setPreviousRow(self, currentItem):
        if currentItem:        
            if "Album Title:" in currentItem.text():    
                previous_row  = self.currentRow() + 1                
                self.setCurrentCell(previous_row, 7)
                print("previous row ", previous_row)
                
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
                    print("Removing album title row ", item)
                    self.removeRow(item.row())
                            
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("UP key pressed")
            self.setNextRow(self.currentItem())
            
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected_rows()
                    
        elif event.key() == Qt.Key.Key_Down:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
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
            self.play_pause()    
            
        elif event.key() == Qt.Key.Key_Enter:
            self.rowDoubleClick()
                                
        elif event.key() == Qt.Key.Key_G and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.clearSelection()               
            self.scroll_to_current_row()                         
                                
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
