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
    
    def setNextRow(self):       
        current_item = self.currentItem()
        if current_item:
            if "Album Title:" in current_item.text():    
                self.setCurrentCell(self.currentRow() - 1, 7)
        else:
            pass
            
    def setPreviousRow(self):
        current_item = self.currentItem()
        if current_item:        
            if "Album Title:" in current_item.text():    
                self.setCurrentCell(self.currentRow() + 1, 7)
        else:
            pass
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("UP key pressed")
            self.setNextRow()
                    
        elif event.key() == Qt.Key.Key_Down:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("DOWN key pressed")    
            self.setPreviousRow()        
            
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
            
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
