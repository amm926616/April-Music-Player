from PyQt6.QtWidgets import (
    QFileDialog, QLabel, QPushButton,
    QVBoxLayout, QDialog, QSpinBox, QHBoxLayout
)
from PyQt6.QtGui import QFontDatabase, QIcon, QKeyEvent
from easy_json import EasyJson
from fontTools.ttLib import TTFont
from PyQt6.QtCore import Qt

class FontSettingsWindow(QDialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)  # Initialize the parent QDialog
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
        label = QLabel("[Current Configured Fonts with Languages]", self)
        main_layout.addWidget(label)        

        # Create sections for each language using a loop
        for language in self.languages:
            current_font = self.ej.get_value(f"{language.lower()}_font")
            font_name = self.get_font_name_from_file(current_font)
            language_label = QLabel(f"{language}:", self)  # Language label
            font_label = QLabel(f"{font_name}", self)  # Font display label
            change_button = QPushButton("Change Font", self)  # Change font button
            change_button.clicked.connect(lambda _, lang=language: self.load_font(lang))

            # Store the font label and button in dictionaries for future reference
            self.font_labels[language] = font_label
            self.change_buttons[language] = change_button

            # Add the created layout for each language to the main layout
            main_layout.addLayout(self.create_language_layout(language_label, font_label, change_button))

        # LRC Font size configuration
        self.lrc_font_size_label = QLabel("LRC Font Size:", self)
        self.lrc_font_size_spinbox = QSpinBox(self)
        self.lrc_font_size_spinbox.setRange(10, 100)
        self.lrc_font_size_spinbox.setValue(self.ej.get_value("lrc_font_size"))  # Default font size
        self.lrc_font_size_spinbox.valueChanged.connect(self.update_lrc_font_size)

        # LRC font size layout
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(self.lrc_font_size_label)
        font_size_layout.addWidget(self.lrc_font_size_spinbox)

        # Add the LRC font size layout to the main layout
        main_layout.addLayout(font_size_layout)

        self.setLayout(main_layout)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()  
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.close()

    def update_lrc_font_size(self, value):
        self.ej.edit_value("lrc_font_size", value)
        self.parent.lrcPlayer.lrc_font.font_size = value
        self.parent.lrcPlayer.lrc_font.reloadFont()

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
                    self.parent.lrcPlayer.media_font.reloadFont()
                    self.parent.lrcPlayer.lrc_font.reloadFont()

    def update_font_display(self, language):
        """ Update the QLabel for the selected language with the chosen font """
        self.font_labels[language].setText(f"{self.fonts[language]}")

    def get_font_name_from_file(self, font_path):
        font = TTFont(font_path)
        name_records = font['name'].names
        for record in name_records:
            if record.nameID == 4:  # Name ID 4 usually contains the full font name
                font_name = record.toStr()
                return font_name
        return "Unknown Font"  # Default if nameID 4 is not found
