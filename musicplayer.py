from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl


class MusicPlayer:
    def __init__(self):
        self.lrc_file = None
        self.file_name = None
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.started_playing = False
        self.in_pause_state = False
        # Connect the mediaStatusChanged signal to a slot
        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)

    def update_files(self, file, lrc):
        self.file_name = file
        self.lrc_file = lrc
        self.player.setSource(QUrl.fromLocalFile(self.file_name))

    def play(self):
        self.player.play()
        self.started_playing = True

    def play_pause_music(self):
        if self.started_playing:
            if not self.in_pause_state:
                self.player.pause()
                self.in_pause_state = True
            else:
                # Pre-buffer the next part before playing
                self.player.play()
                self.in_pause_state = False

    def pause(self):
        self.player.pause()

    def get_current_time(self):
        position = self.player.position() / 1000.0
        return position

    def seek_forward(self):
        self.player.setPosition(self.player.position() + 1000)

    def seek_backward(self):
        self.player.setPosition(self.player.position() - 1000)

    def get_duration(self):
        return self.player.duration()

    def get_position(self):
        return self.player.position()

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Restart playback
            self.player.setPosition(0)
            self.player.play()
