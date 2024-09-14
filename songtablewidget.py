from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

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
        self.verticalHeader().setVisible(False) # hide the row numbers
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
    def get_previous_song_object(self):
        if self.parent.player.music_on_shuffle:
            self.parent.play_random_song()
            return 
        
        if self.parent.player.music_on_repeat:
                self.parent.player.player.setPosition(0)
                self.parent.player.player.play() 
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
        
        
    def get_next_song_object(self):
        if self.parent.player.music_on_shuffle:
            self.parent.play_random_song()
            return 
        
        if self.parent.player.music_on_repeat:
                self.parent.player.player.setPosition(0)
                self.parent.player.player.play() 
                return
        
        current_row = self.song_playing_row
        next_row = current_row + 1
        
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
        
        # Create a set to keep track of rows to remove
        rows_to_remove = set()
        
        # Collect all rows to be removed, including any empty album title rows
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
        
        # Check for any remaining "Album Title:" rows without songs
        row_count = self.rowCount()
        i = 0
        while i < row_count:
            item = self.item(i, 0)  # Assuming album title is in the first column (index 0)
            if item and item.text().startswith("Album Title:"):
                album_title_text = item.text()
                album_title = album_title_text[len("Album Title: "):]  # Extract the album title part
                
                # Check if the album has remaining songs
                has_songs = False
                j = i + 1
                while j < row_count:
                    next_item = self.item(j, 0)  # Check next rows for song items
                    if next_item and not next_item.text().startswith("Album Title:"):
                        has_songs = True
                        break
                    j += 1
                
                if not has_songs:
                    # Remove the album title row if no songs are left
                    self.removeRow(i)
                    row_count -= 1  # Adjust row count because we removed a row
                    i -= 1  # Adjust index because we removed a row

            i += 1
            
        self.files_on_playlist = [i for i in rows_to_remove if i not in self.files_on_playlist]
        
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
