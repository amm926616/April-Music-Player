from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt6.QtGui import QKeyEvent, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtCore import Qt
import sqlite3
import os
import json

class NoteTaking():
    def __init__(self, lrcSync):
        self.lrcSync = lrcSync
        self.window = QDialog()        
        self.window.keyPressEvent = self.keyPressEvent
        self.window.setWindowTitle("Text Editor/Note Book")
        self.window.setGeometry(500, 300, 400, 300)

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
                
        self.layout.addWidget(self.textBox)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveToDatabase)
        self.layout.addWidget(saveButton)

        self.window.setLayout(self.layout)
        
    def saveToDatabase(self):
        # Retrieve the notes from the text box
        text = self.textBox.toHtml()
        
        # Add the notes to the database
        self.add_notes(text)
        
        # Clear the text box
        self.textBox.clear()
        self.window.close()
        self.lrcSync.player.play_pause_music()

    def add_notes(self, html_text):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(os.path.join(self.lrcSync.config_path, "songs.db")) as conn:
                cursor = conn.cursor()

                # Fetch the existing notes for the current file
                cursor.execute('''
                    SELECT json_notes FROM notes WHERE lrc_filename = ?
                ''', (self.lrcSync.file,))
                
                row = cursor.fetchone()
                if row:
                    # Load existing JSON notes
                    existing_notes = json.loads(row[0])
                else:
                    # No existing notes, initialize an empty dictionary
                    existing_notes = {}
                    
                index = str(self.lrcSync.current_index)

                # Store the HTML text for the current index
                existing_notes[index] = html_text

                # Convert the updated dictionary to JSON format
                json_notes = json.dumps(existing_notes)

                # Replace the notes in the database
                cursor.execute('''
                    REPLACE INTO notes (lrc_filename, json_notes)
                    VALUES (?, ?)
                ''', (self.lrcSync.file, json_notes))
                
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def createUI(self):
        # Load existing notes
        try:
            # Connect to the SQLite database
            with sqlite3.connect(os.path.join(self.lrcSync.config_path, "songs.db")) as conn:
                cursor = conn.cursor()
                
                # Query to fetch JSON notes based on file_path
                cursor.execute('''
                    SELECT json_notes FROM notes
                    WHERE lrc_filename = ?
                ''', (self.lrcSync.file,))
                
                row = cursor.fetchone()
                
                if row:
                    json_notes = row[0]                    
                    # Load existing notes from JSON
                    notes_data = json.loads(json_notes)                    
                    index = str(self.lrcSync.current_index)
                    
                    # Extract notes for the current index
                    if index in notes_data:
                        notes_html = notes_data[index]
                        
                        # Ensure notes_html is a string
                        if isinstance(notes_html, list):
                            notes_html = "<br>".join(notes_html)  # Convert list to HTML string
                    else:
                        notes_html = ""
                                            
                    # Set the HTML content in the QTextEdit
                    self.textBox.setHtml(notes_html)
                else:
                    print("No notes found for the specified file_path.")
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")

        # Show the dialog
        if not self.window.isVisible():
            self.window.exec()
            
    def keyPressEvent(self, event: QKeyEvent):            
        # Handle Ctrl + S (save to database)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            print("Ctrl + S pressed")
            self.saveToDatabase()
            
        # Handle Exit key (example: Esc key)
        elif event.key() == Qt.Key.Key_Escape:
            print("Escape pressed, exiting application")
            self.lrcSync.player.play_pause_music()            
            self.window.close()  # You can use sys.exit() here if you want to exit the entire app
            
    def textBoxClose(self, event):
        self.lrcSync.play_pause_music()
        event.accept()

