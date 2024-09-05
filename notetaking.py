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
        self.window.setWindowTitle("Note Taking Window")
        self.window.setGeometry(500, 300, 400, 300)

        # Layout
        self.layout = QVBoxLayout()

        # Text edit area
        self.textBox = QTextEdit()
        
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
        print(text)
        
        # Split the notes into lines
        lines = text.split('\n')

        # Add the notes to the database
        self.add_notes(lines)
        
        # Clear the text box
        self.textBox.clear()
        self.window.close()

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
                    print("in row if")
                    # Load existing JSON notes
                    existing_notes = json.loads(row[0])
                    print("existing_notes ", existing_notes)
                else:
                    print('in row else')
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
                print("row ", row)
                print(type(row))
                
                if row:
                    json_notes = row[0]
                    print("json_notes ", json_notes)
                    print(type(json_notes))
                    
                    # Load existing notes from JSON
                    notes_data = json.loads(json_notes)
                    print("notes_data ", notes_data)
                    print(type(notes_data))
                    
                    index = str(self.lrcSync.current_index)
                    
                    # Extract notes for the current index
                    if index in notes_data:
                        notes_html = notes_data[index]
                        
                        # Ensure notes_html is a string
                        if isinstance(notes_html, list):
                            notes_html = "<br>".join(notes_html)  # Convert list to HTML string
                    else:
                        notes_html = ""
                        
                    print("notes_html ", notes_html)
                    print(type(notes_html))
                    
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
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            # Handle Ctrl + S
            print("Ctrl + S pressed")
            self.saveToDatabase()

