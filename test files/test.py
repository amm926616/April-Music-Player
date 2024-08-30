import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMainWindow
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QCoreApplication

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.ico'))
        self.tray_icon.setVisible(True)

        # Create a context menu for the system tray icon
        self.tray_menu = QMenu()
        
        # Add an "Open" action
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        self.tray_menu.addAction(open_action)
        
        # Add an "Exit" action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        self.tray_menu.addAction(exit_action)
        
        # Set the context menu
        self.tray_icon.setContextMenu(self.tray_menu)

    def closeEvent(self, event):
        # Hide the window instead of quitting the application
        self.hide()
        event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())