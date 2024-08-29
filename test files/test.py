from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QFont, QTextDocument

def apply_fonts_to_text(text, font_english, font_korean):
    doc = QTextDocument()
    cursor = QTextCursor(doc)

    format_english = QTextCharFormat()
    format_english.setFont(font_english)

    format_korean = QTextCharFormat()
    format_korean.setFont(font_korean)

    for char in text:
        if 'a' <= char <= 'z' or 'A' <= char <= 'Z':
            cursor.setCharFormat(format_english)
        elif '\uAC00' <= char <= '\uD7A3':
            cursor.setCharFormat(format_korean)
        cursor.insertText(char)

    return doc.toHtml()

def main():
    app = QApplication([])

    widget = QWidget()
    layout = QVBoxLayout(widget)

    label = QLabel()

    # Fonts for English and Korean
    font_english = QFont("Noto Sans", 14)
    font_korean = QFont("Noto Serif CJK KR", 20)

    # Mixed language text
    mixed_text = "안녕하세요, Hello, 이건 한국어 텍스트입니다, this is English text."

    # Apply fonts based on language
    html_text = apply_fonts_to_text(mixed_text, font_english, font_korean)

    label.setText(html_text)
    layout.addWidget(label)

    widget.show()
    app.exec()

if __name__ == "__main__":
    main()
