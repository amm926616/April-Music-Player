from PyQt6.QtGui import QFontDatabase, QFont, QTextDocument, QTextCursor, QTextCharFormat
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
        self.language_dict = {
            "korean": {"font_name": "Noto Serif KR Bold", "file_path": os.path.join(self.script_path , "fonts/NotoSerifKR-Bold.otf"), "size": font_size},
            "english": {"font_name": "Positive Forward", "file_path": os.path.join(self.script_path , "fonts/PositiveForward.otf"), "size": font_size},
            "japanese": {"font_name": "NotoSans JP Bold", "file_path": os.path.join(self.script_path , "fonts/NotoSansJP-Bold.otf"), "size": font_size},
        }
        self.fonts_loaded = False
        self.formats = {}

    def loadFonts(self):
        for lang, font_info in self.language_dict.items():
            if font_info["file_path"]:  # If file path is provided, load from file
                QFontDatabase.addApplicationFont(font_info["file_path"])
            else:  # If no file path, use the font name from the local machine
                font_info["file_path"] = font_info["font_name"]

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
            cursor.setCharFormat(self.formats.get(language, self.formats[language]))
            cursor.insertText(char)

        return doc.toHtml()

    def get_formatted_text(self, text):
        return self.apply_fonts_to_text(text)

