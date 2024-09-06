from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtGui import QKeyEvent, QFont, QTextCharFormat, QTextCursor, QIcon
from PyQt6.QtCore import Qt
from getfont import GetFont
import sqlite3
import os
import json
import base64
import zlib

class NoteTaking():
    def __init__(self, lrcSync):
        self.lrcSync = lrcSync
        self.window = QDialog()        
        self.window.keyPressEvent = self.keyPressEvent
        self.window.setWindowTitle("Current Lyric's Notebook")
        
        self.lyric_label_font = GetFont(13)

        # Layout
        self.layout = QVBoxLayout()

        # Text edit area
        self.textBox = QTextEdit()
        self.textBox.closeEvent = self.textBoxClose
        
        # Create a QTextCharFormat object
        format = QTextCharFormat()

        # Set the font size
        font = QFont()
        font.setPointSize(14)  # Set the desired font size
        format.setFont(font)

        # Apply the format to the text
        cursor = self.textBox.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)  # Use QTextCursor.SelectionType.Document
        cursor.mergeCharFormat(format)
        self.textBox.setTextCursor(cursor)
        
        self.current_lyric_label = QLabel()
        self.layout.addWidget(self.current_lyric_label)
        self.layout.addWidget(self.textBox)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveToDatabase)
        self.layout.addWidget(saveButton)

        self.window.setLayout(self.layout) 
        
    def saveToDatabase(self):
        # Retrieve the notes from the text box
        text = self.textBox.toHtml()

        # Compress and encode to Base64
        compressed_html = zlib.compress(text.encode('utf-8'))
        compressed_html_base64 = base64.b64encode(compressed_html).decode('utf-8')  # Convert to Base64 string

        # Add the notes to the database
        self.push_note_to_database(compressed_html_base64)

        # Clear the text box
        self.textBox.clear()
        self.window.close()
        self.lrcSync.player.play_pause_music()

    def push_note_to_database(self, compressed_html_base64):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(os.path.join(self.lrcSync.config_path, "songs.db")) as conn:
                cursor = conn.cursor()

                # Fetch the existing notes for the current file
                cursor.execute('''
                    SELECT json_notes FROM notes WHERE lrc_filename = ?
                ''', (self.lrcSync.player.file_name,))
                
                row = cursor.fetchone()
                if row:
                    # Load existing JSON notes
                    existing_notes = json.loads(row[0])
                else:
                    # No existing notes, initialize an empty dictionary
                    existing_notes = {}

                index = str(self.lrcSync.current_index)

                # Store the Base64-encoded compressed HTML for the current index
                existing_notes[index] = compressed_html_base64

                # Convert the updated dictionary to JSON format
                json_notes = json.dumps(existing_notes)

                # Replace the notes in the database
                cursor.execute('''
                    REPLACE INTO notes (lrc_filename, json_notes)
                    VALUES (?, ?)
                ''', (self.lrcSync.player.file_name, json_notes))
                
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def createUI(self):
        # update current lyric label
        self.current_lyric_label.setText(self.lyric_label_font.get_formatted_text(f"Current Lyric: {self.lrcSync.current_lyric}"))
        self.current_lyric_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) # make it selectable
        
        # setting window's title as current index
        self.window.setWindowTitle(f"Notebook for [Lyric Line {self.lrcSync.current_index}]")        
        self.window.setGeometry(500, 300, 800, 400)
        
        # Load existing notes
        try:
            # Connect to the SQLite database
            with sqlite3.connect(os.path.join(self.lrcSync.config_path, "songs.db")) as conn:
                cursor = conn.cursor()
                
                # Query to fetch JSON notes based on file_path
                cursor.execute('''
                    SELECT json_notes FROM notes
                    WHERE lrc_filename = ?
                ''', (self.lrcSync.player.file_name,))
                
                row = cursor.fetchone()
                
                if row:
                    json_notes = row[0]
                    
                    # Load existing notes from JSON
                    notes_data = json.loads(json_notes)
                    index = str(self.lrcSync.current_index)
                    
                    # Extract notes for the current index
                    if index in notes_data:
                        # Retrieve the Base64-encoded compressed HTML string
                        compressed_html_base64 = notes_data[index]
                        
                        # Decode Base64 to get compressed bytes
                        compressed_html = base64.b64decode(compressed_html_base64)
                        
                        # Decompress the compressed HTML
                        decompressed_html = zlib.decompress(compressed_html).decode('utf-8')
                        
                        # Ensure decompressed_html is a string (if not, handle appropriately)
                        if isinstance(decompressed_html, list):
                            decompressed_html = "<br>".join(decompressed_html)  # Convert list to HTML string
                    else:
                        decompressed_html = ""
                                        
                    # Set the HTML content in the QTextEdit
                    self.textBox.setHtml(decompressed_html)
                else:
                    print("No notes found for the specified file_path.")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error while loading notes: {e}")

        # Show the dialog
        if not self.window.isVisible():
            self.window.exec()                  
            
                  
    def keyPressEvent(self, event: QKeyEvent):            
        # Handle Ctrl + S (save to database)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            print("Ctrl + S pressed")
            self.saveToDatabase()

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            print("pressed ctrl + F")
            if self.is_full_screen():
                self.window.showNormal()  # Restore to normal mode
            else:
                self.window.showFullScreen()  # Enter full-screen mode            

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            print("pressed ctrl + w")     
            self.lrcSync.player.play_pause_music()            
            self.window.close()  # You can use sys.exit() here if you want to exit the entire app
            
        # Handle Exit key (example: Esc key)
        elif event.key() == Qt.Key.Key_Escape:
            print("Escape pressed, exiting application")
            self.lrcSync.player.play_pause_music()            
            self.window.close()  # You can use sys.exit() here if you want to exit the entire app

    def is_full_screen(self):
        # Check if the dialog is in full-screen mode

        current_window_state = self.window.windowState()
        
        # Define the full-screen flag
        full_screen_flag = Qt.WindowState.WindowFullScreen
        
        # Check if the current window state includes the full-screen flag
        is_full_screen_mode = (current_window_state & full_screen_flag) == full_screen_flag
        
        # Return the result
        return is_full_screen_mode
            
    def textBoxClose(self, event):
        self.lrcSync.play_pause_music()
        event.accept()

