from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QCheckBox, QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from easy_json import EasyJson

class AddNewDirectory(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ej = EasyJson()
        self.parent = parent
        self.directories = self.ej.get_value("music_directories")  # List to store added directories
        if self.directories:
            for directory in self.directories:
                checkbox = QCheckBox(directory)
                checkbox.setChecked(True)
                self.scroll_area_layout.addWidget(checkbox)

        """Sets up the UI components and layout."""
        self.setWindowTitle("Manage Music Directories")
        self.resize(400, 300)

        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.button_layout = QHBoxLayout()

        # Widgets
        self.info_label = QLabel("Choose directories to load music from:")
        self.add_button = QPushButton("Add New Directory")
        self.load_all_button = QPushButton("Load Directories")

        # "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.checkStateChanged.connect(self.select_all_directories)

        # Scroll area for directories
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align items to the top
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)

        # Adding widgets to layouts
        self.main_layout.addWidget(self.info_label)
        self.main_layout.addWidget(self.select_all_checkbox)
        self.main_layout.addWidget(self.scroll_area)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.load_all_button)
        self.main_layout.addLayout(self.button_layout)

        # Signals and slots
        self.add_button.clicked.connect(self.add_directory)
        self.load_all_button.clicked.connect(self.load_all_directories)

    def add_directory(self):
        """Allow user to select a directory and add it to the list with a checkbox."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            if directory not in self.directories:
                self.directories.append(directory)
                self.ej.edit_value("music_directories", self.directories)
                checkbox = QCheckBox(directory)
                checkbox.setChecked(True)
                self.scroll_area_layout.addWidget(checkbox)
            else:
                QMessageBox.information(self, "Directory Exists", "This directory is already added.")

    def load_all_directories(self):
        """Simulate loading all directories (this is where backend logic will go)."""
        selected_dirs = [cb.text() for cb in self.scroll_area_widget.findChildren(QCheckBox) if cb.isChecked()]
        if selected_dirs:
            self.parent.albumTreeWidget.loadSongsToCollection(self.directories, loadAgain=True)
        else:
            QMessageBox.warning(self, "No Directory Selected", "Please select at least one directory to load.")

    def select_all_directories(self, state):
        """Select or deselect all directories based on 'Select All' checkbox."""
        checkboxes = self.scroll_area_widget.findChildren(QCheckBox)
        for checkbox in checkboxes:
            checkbox.setChecked(state == Qt.CheckState.Checked)