from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class SongTableWidget(QTableWidget):
    def __init__(self, parent=None, rowDoubleClick=None, seekRight=None, seekLeft=None, play_pause=None):
        self.rowDoubleClick = rowDoubleClick
        self.seekRight = seekRight
        self.seekLeft = seekLeft
        self.play_pause = play_pause
        self.song_playing_row = None
        super().__init__(parent)
        self.verticalHeader().setVisible(False) # hide the row numbers
        
        
    def get_previous_song_object(self):
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
        current_row = self.song_playing_row
        next_row = current_row + 1
        
        # Ensure next_row is within bounds
        if next_row >= self.rowCount():
            return None  # Or handle the case where no more rows are available
        
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
            
    def scrollToCurrentRow(self):
        """Scroll to and highlight the current row."""
        if self.song_playing_row is not None:
            current_item = self.item(self.song_playing_row, 7)
            if current_item:
                # Scroll to the item
                self.scrollToItem(current_item, self.ScrollHint.PositionAtCenter)
                self.setCurrentCell(self.song_playing_row, 7)    
        else:
            return 
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("UP key pressed")
            self.setNextRow(self.currentItem())
                    
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
            self.scrollToCurrentRow()                         
                                
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
