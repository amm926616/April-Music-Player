from musicplayerui import MusicPlayerUI
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSharedMemory
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
import signal
import sys
import os

APP_KEY = 'AprilMusicPlayer'
SERVER_NAME = 'MusicPlayerServer'


def cleanup_stale_server():
    """Remove any existing server with the same name to avoid conflicts."""
    QLocalServer.removeServer(SERVER_NAME)


def setup_signal_handlers():
    """Setup signal handlers to ensure cleanup on crash or termination."""
    signal.signal(signal.SIGINT, cleanup_stale_server)
    signal.signal(signal.SIGTERM, cleanup_stale_server)


def load_stylesheet():
    """Load the QSS file from the specified path."""
    script_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_path, "style.qss")
    with open(file_path, "r") as f:
        return f.read()


def bring_up_main_window():
    # Connect to the local server and send a message to bring up the window
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(1000):
        socket.write(b'activate_window')
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
    else:
        print("Failed to connect to server:", socket.errorString())
    socket.close()


class SingleInstanceApp:
    def __init__(self):
        self.shared_memory = QSharedMemory(APP_KEY)
        self.server = None

    def is_another_instance_running(self):
        if self.shared_memory.attach():
            return True
        if self.shared_memory.create(1):
            return False
        else:
            print("Error creating shared memory:", self.shared_memory.errorString())
            return True

    def create_local_server(self, ui):
        self.server = QLocalServer()
        if self.server.listen(SERVER_NAME):
            self.server.newConnection.connect(lambda: self.handle_new_connection(ui))
        else:
            print("Error starting server:", self.server.errorString())

    def handle_new_connection(self, ui):
        socket = self.server.nextPendingConnection()
        if socket and socket.waitForReadyRead(1000):
            message = socket.readAll().data().decode()
            if message == 'activate_window':
                ui.showMaximized()
                ui.activateWindow()
                ui.raise_()
        socket.disconnectFromServer()
        socket.close()

    def run(self):
        app = QApplication(sys.argv)

        # Load QSS stylesheet
        stylesheet = load_stylesheet()
        app.setStyleSheet(stylesheet)

        # Set up signal handlers for cleanup
        setup_signal_handlers()

        # Clean up stale server from previous crash
        cleanup_stale_server()

        # If no other instance is running, create the UI and the local server
        ui = MusicPlayerUI(app)
        ui.createUI()

        # Set up the local server for future instances to communicate with
        self.create_local_server(ui)

        # Run the application
        exit_code = app.exec()

        # Cleanup
        self.shared_memory.detach()
        sys.exit(exit_code)


if __name__ == "__main__":
    instance_app = SingleInstanceApp()

    if instance_app.is_another_instance_running():
        bring_up_main_window()
        sys.exit(1)  # Exit the new instance
    else:
        instance_app.run()
