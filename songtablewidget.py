from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class SongTableWidget(QTableWidget):
    def __init__(self, parent=None, rowSingleClick=None, seekRight=None, seekLeft=None, play_pause=None):
        self.rowSingleClick = rowSingleClick
        self.seekRight = seekRight
        self.seekLeft = seekLeft
        self.play_pause = play_pause
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            print("UP key pressed")
            # Get the current item and call the click handler if provided
            current_item = self.currentItem()
            if self.rowSingleClick and current_item:
                self.rowSingleClick(current_item)
            # Call the base class method to maintain default behavior
            super().keyPressEvent(event)
            
        elif event.key() == Qt.Key.Key_Down:
            print("DOWN key pressed")            
            current_item = self.currentItem()
            if self.rowSingleClick and current_item:
                self.rowSingleClick(current_item)            
            # Call the base class method to maintain default behavior
            super().keyPressEvent(event)
            
        elif event.key() == Qt.Key.Key_Right:
            self.seekRight()
        
        elif event.key() == Qt.Key.Key_Left:
            self.seekLeft()    
            
        elif event.key() == Qt.Key.Key_Space:
            self.play_pause()    
            
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
