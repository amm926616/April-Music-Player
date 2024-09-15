from PyQt6.QtGui import QFontDatabase, QFont, QTextDocument, QTextCursor, QTextCharFormat
from fontTools.ttLib import TTFont
from easy_json import EasyJson
import os

"""
preformatted fonts for different languages
method will get text. return html text which is accessable by qlabel

in getfont class
setup fonts with language, setup Qdatabase, Qfont
apply format, return html text
"""

from PyQt6.QtGui import QFont, QFontDatabase, QTextCharFormat, QTextDocument, QTextCursor

class GetFont:
    def __init__(self, font_size=14):
        self.script_path = os.path.dirname(os.path.abspath(__file__))        
        self.ej = EasyJson()
        self.font_size = font_size
        self.load_font_settings()  # Initialize the font settings
        self.fonts_loaded = False
        self.formats = {}

    def load_font_settings(self):
        english_font = self.ej.get_value("english_font")
        korean_font = self.ej.get_value("korean_font")
        japanese_font = self.ej.get_value("japanese_font")
        chinese_font = self.ej.get_value("chinese_font")

        self.language_dict = {
            "korean": {"font_name": self.get_font_name(korean_font), "file_path": korean_font, "size": self.font_size},
            "english": {"font_name": self.get_font_name(english_font), "file_path": english_font, "size": self.font_size},
            "japanese": {"font_name": self.get_font_name(japanese_font), "file_path": japanese_font, "size": self.font_size}, 
            "chinese": {"font_name": self.get_font_name(chinese_font), "file_path": chinese_font, "size": self.font_size}           
        }

    def get_font_name(self, font_path):
        font = TTFont(font_path)
        name_records = font['name'].names
        for record in name_records:
            if record.nameID == 4:  # Full font name
                font_name = record.toStr()
                print(font_name)
                return font_name
        return None

    def loadFonts(self):
        for lang, font_info in self.language_dict.items():
            if font_info["file_path"]:  # Load from file if path exists
                QFontDatabase.addApplicationFont(font_info["file_path"])
            self.formats[lang] = self.create_text_format(font_info["font_name"], font_info["size"])
        self.fonts_loaded = True

    def create_text_format(self, font_name, font_size):
        font = QFont(font_name, font_size)
        text_format = QTextCharFormat()
        text_format.setFont(font)
        return text_format

    def detect_language(self, char):
        if 'a' <= char <= 'z' or 'A' <= char <= 'Z':
            return "english"
        elif '\uAC00' <= char <= '\uD7A3':
            return "korean"
        elif '\u3040' <= char <= '\u309F':  # Hiragana
            return "japanese"
        elif '\u30A0' <= char <= '\u30FF':  # Katakana
            return "japanese"
        elif '\u4E00' <= char <= '\u9FFF':  # Kanji
            return "japanese"
        return None

    def apply_fonts_to_text(self, text):
        if not self.fonts_loaded:
            self.loadFonts()

        doc = QTextDocument()
        cursor = QTextCursor(doc)

        for char in text:
            language = self.detect_language(char) or "english"
            cursor.setCharFormat(self.formats.get(language, self.formats["english"]))
            cursor.insertText(char)

        return doc.toHtml()

    def get_formatted_text(self, text):
        return self.apply_fonts_to_text(text)

    def reloadFont(self):
        """Reloads the font settings and applies them again."""
        self.load_font_settings()  # Re-fetch font settings from EasyJson
        self.fonts_loaded = False  # Mark fonts as not loaded
        self.loadFonts()  # Reload the fonts with the new settings
