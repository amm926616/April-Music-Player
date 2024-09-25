from PyQt6.QtCore import QThread, QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


def handle_buffer_status(percent_filled):
    print(f"Buffer status: {percent_filled}%")


class MusicPlayerWorker(QObject):
    # Define signals if needed (for future callbacks or status updates)
    started = pyqtSignal()

    def __init__(self, handle_media_status_changed):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Connect the buffer status signal to a custom method
        self.player.bufferProgressChanged.connect(handle_buffer_status)

        # Connect the mediaStatusChanged signal to a slot
        self.player.mediaStatusChanged.connect(handle_media_status_changed)

        self.positionChanged = self.player.positionChanged
        self.durationChanged = self.player.durationChanged

        self.MediaStatus = QMediaPlayer.MediaStatus

    def play(self):
        self.started.emit()  # Emit a signal when the player starts, if needed
        self.player.play()

    def pause(self):
        self.player.pause()

    def position(self):
        return self.player.position()

    def isPlaying(self):
        return self.player.isPlaying()

    def setSource(self, file):
        self.player.setSource(QUrl.fromLocalFile(file))

    def setPosition(self, position=int()):
        self.player.setPosition(position)

    def duration(self):
        return self.player.duration()
