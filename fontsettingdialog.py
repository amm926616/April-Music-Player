from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QWidget, QPushButton, QLabel)

class FontSettingsDialog(QDialog):
    def __init__(self, languages, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Font Settings')
        layout = QVBoxLayout()

        # Table for language, font display, and font size controls
        self.table = QTableWidget(len(languages), 3)  # Rows = number of languages, Columns = 3
        self.table.verticalHeader().setVisible(False)  
        self.table.horizontalHeader().setVisible(False)  
        

        self.languages = languages
        self.font_labels = []  # To store the QLabel for each language's font
        self.font_size_spins = []

        for row, language in enumerate(languages):
            # Set the language name
            self.table.setItem(row, 0, QTableWidgetItem(language))

            # Display current font in a QLabel
            font_layout = QHBoxLayout()
            font_label = QLabel("")
            self.font_labels.append(font_label)

            # Button to change font
            change_font_button = QPushButton("Change Font")
            change_font_button.clicked.connect(lambda: self.change_font(row))  # Change font for the current row

            font_layout.addWidget(font_label)
            font_layout.addWidget(change_font_button)

            # Create a QWidget to hold QLabel and QPushButton
            font_widget = QWidget()
            font_widget.setLayout(font_layout)
            self.table.setCellWidget(row, 1, font_widget)

            # Font size with + and - buttons
            size_layout = QHBoxLayout()
            decrease_button = QPushButton("−")
            increase_button = QPushButton("+")
            font_size_spin = QLabel("12")  # Initialize font size to 12
            self.font_size_spins.append(font_size_spin)

            decrease_button.clicked.connect(lambda: self.adjust_font_size(row, -1))
            increase_button.clicked.connect(lambda: self.adjust_font_size(row, 1))

            size_layout.addWidget(decrease_button)
            size_layout.addWidget(font_size_spin)
            size_layout.addWidget(increase_button)

            size_widget = QWidget()
            size_widget.setLayout(size_layout)
            self.table.setCellWidget(row, 2, size_widget)

        layout.addWidget(self.table)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def change_font(self, row):
        # Handle the font change logic (open a font picker or similar)
        # For now, we'll just simulate a font change
        self.font_labels[row].setText("New Font Selected")

    def adjust_font_size(self, row, change):
        current_size = int(self.font_size_spins[row].text())
        new_size = max(8, min(current_size + change, 72))  # Font size between 8 and 72
        self.font_size_spins[row].setText(str(new_size))

    def get_font_settings(self):
        settings = []
        for i, language in enumerate(self.languages):
            settings.append({
                'language': language,
                'font_name': self.font_labels[i].text(),
                'font_size': int(self.font_size_spins[i].text())
            })
        return settings

