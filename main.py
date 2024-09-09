from musicplayerui import MusicPlayerUI
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSharedMemory
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
import sys

APP_KEY = 'music_player_unique_key'
SERVER_NAME = 'MusicPlayerServer'

shared_memory = QSharedMemory(APP_KEY)

def is_another_instance_running():
    if shared_memory.attach():
        return True
    
    if shared_memory.create(1):
        return False
    else:
        print("Error creating shared memory:", shared_memory.errorString())
        return True

def bring_up_main_window():
    # Connect to the local server and send a message to bring up the window
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(1000):
        # Send a simple message to trigger the main window
        socket.write(b'activate_window')
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()

def create_local_server(ui):
    # Create a local server to listen for incoming connections from other instances
    server = QLocalServer()
    
    if server.listen(SERVER_NAME):
        # Handle new connections by bringing up the main window
        server.newConnection.connect(lambda: handle_new_connection(server, ui))
    
    return server

def handle_new_connection(server, ui):
    socket = server.nextPendingConnection()
    if socket and socket.waitForReadyRead(1000):
        message = socket.readAll().data().decode()
        if message == 'activate_window':
            ui.showMaximized()  # Bring the window to normal state if minimized
            ui.activateWindow()  # Bring the window to the foreground
            ui.raise_()  # Ensure it is on top of other windows
    socket.disconnectFromServer()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if is_another_instance_running():
        # If another instance is running, bring up its main window
        bring_up_main_window()
        sys.exit(0)  # Exit the new instance
    
    # If no other instance is running, create the UI and the local server
    ui = MusicPlayerUI(app)
    ui.createUI()

    # Set up the local server for future instances to communicate with
    server = create_local_server(ui)
    
    exit_code = app.exec()
    shared_memory.detach()
    sys.exit(exit_code)
