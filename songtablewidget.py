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
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("UP key pressed")
            current_item = self.currentItem()
            if current_item:
                self.rowSingleClick(current_item)
                    
        elif event.key() == Qt.Key.Key_Down:
            super().keyPressEvent(event) # activate the normal behaviour of qtablewidget first where it moves the focus on item
            print("DOWN key pressed")            
            current_item = self.currentItem()
            if current_item:            
                self.rowSingleClick(current_item)            
            
        elif event.key() == Qt.Key.Key_Right:
            self.seekRight()
        
        elif event.key() == Qt.Key.Key_Left:
            self.seekLeft()    
            
        elif event.key() == Qt.Key.Key_Space:
            self.play_pause()    
            
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)
