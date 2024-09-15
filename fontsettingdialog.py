from PyQt6.QtWidgets import (
    QFileDialog, QLabel, QPushButton,
    QVBoxLayout, QWidget, QSpinBox, QHBoxLayout
)
from PyQt6.QtGui import QFontDatabase, QIcon
from easy_json import EasyJson

class FontSettingsWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.ej = EasyJson()
        self.setGeometry(200, 200, 400, 200)
        self.setWindowTitle("Font Settings")
        self.setWindowIcon(QIcon(parent.icon_path))

        # List of languages
        self.languages = ["English", "Korean", "Japanese", "Chinese"]

        # Dictionary to store widgets for each language
        self.font_labels = {}
        self.change_buttons = {}

        # Dictionary to store the current font for each language
        self.fonts = {language: None for language in self.languages}

        # Main layout
        main_layout = QVBoxLayout()

        # Create sections for each language using a loop
        for language in self.languages:
            current_font = self.ej.get_value(f"{language.lower()}_font")
            label = QLabel(f"{language}:", self)  # Language label
            font_label = QLabel(f"Current Font: {current_font}", self)  # Font display label
            change_button = QPushButton("Change Font", self)  # Change font button
            change_button.clicked.connect(lambda _, lang=language: self.load_font(lang))

            # Store the font label and button in dictionaries for future reference
            self.font_labels[language] = font_label
            self.change_buttons[language] = change_button

            # Add the created layout for each language to the main layout
            main_layout.addLayout(self.create_language_layout(label, font_label, change_button))

        # LRC Font size configuration
        self.lrc_font_size_label = QLabel("LRC Font Size:", self)
        self.lrc_font_size_spinbox = QSpinBox(self)
        self.lrc_font_size_spinbox.setRange(10, 50)
        self.lrc_font_size_spinbox.setValue(self.ej.get_value("lrc_font_size"))  # Default font size

        # LRC font size layout
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.lrc_font_size_label)
        font_size_layout.addWidget(self.lrc_font_size_spinbox)

        # Add the LRC font size layout to the main layout
        main_layout.addLayout(font_size_layout)

        self.setLayout(main_layout)

    def create_language_layout(self, language_label, font_label, change_button):
        """ Helper function to create a horizontal layout for each language section """
        layout = QHBoxLayout()
        layout.addWidget(language_label)
        layout.addWidget(font_label)
        layout.addWidget(change_button)
        return layout

    def load_font(self, language):
        """ Open a file dialog and load a font for the selected language """
        font_file, _ = QFileDialog.getOpenFileName(
            self, "Open Font File", "", "Font Files (*.ttf *.otf)"
        )
        if font_file:
            font_id = QFontDatabase.addApplicationFont(font_file)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    # Set the font for the selected language and update the QLabel
                    self.fonts[language] = font_families[0]
                    self.update_font_display(language)
                    self.ej.edit_value(f"{language.lower()}_font", font_file)

    def update_font_display(self, language):
        """ Update the QLabel for the selected language with the chosen font """
        self.font_labels[language].setText(f"Current Font: {self.fonts[language]}")
