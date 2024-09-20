from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon
import os
from PyQt6.QtCore import QUrl


class MusicPlayer:
    def __init__(self, parent, play_pause_button, loop_playlist_button, repeat_button, shuffle_button, playNextSong=None, playRandomSong=None):
        self.parent = parent
        self.playNextSong = playNextSong
        self.playRandomSong = playRandomSong
        self.file_name = None
        self.eop_text = "End Of Playlist"
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
                
        # Connect the buffer status signal to a custom method
        self.player.bufferProgressChanged.connect(self.handle_buffer_status)

        self.started_playing = False
        self.in_pause_state = False
        self.music_on_repeat = False
        self.music_on_shuffle = False
        self.playlist_on_loop = False
        self.previous_shuffle_state = None
        self.previous_loop_state = None      
        self.paused_position = 0.0
        
        # Connect the mediaStatusChanged signal to a slot
        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.play_pause_button = play_pause_button
        self.loop_playlist_button = loop_playlist_button
        self.repeat_button = repeat_button
        self.shuffle_button = shuffle_button
        self.script_path = os.path.dirname(os.path.abspath(__file__))        
        
    def default_pause_state(self):
        self.in_pause_state = False
        self.paused_position = 0.0
                
    def handle_buffer_status(self, percent_filled):
        print(f"Buffer status: {percent_filled}%")
            
    def update_music_file(self, file):
        self.file_name = file
        self.player.setSource(QUrl.fromLocalFile(self.file_name))

    def play(self):
        self.started_playing = True
        self.player.play()
        
    def toggle_loop_playlist(self):
        if self.playlist_on_loop:
            self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "loop-playlist.ico")))
            self.loop_playlist_button.setToolTip("Toggle Playlist Looping")       
            self.playlist_on_loop = False
        else:            
            self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-loop-playlist.ico")))            
            self.loop_playlist_button.setToolTip("On Playlist Looping")       
            self.playlist_on_loop = True     
            
    def disable_loop_playlist(self):
        if self.music_on_repeat or self.music_on_shuffle:
            self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "loop-playlist-off.ico")))            
            self.loop_playlist_button.setDisabled(True)  
            self.previous_loop_state = self.playlist_on_loop
            self.playlist_on_loop = False     
        else:
            self.loop_playlist_button.setDisabled(False)          
            self.playlist_on_loop = self.previous_loop_state    
            if self.playlist_on_loop:
                self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-loop-playlist.ico")))              
            else:
                self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "loop-playlist.ico")))                                                                 
            
    def disable_shuffle(self):
        if self.music_on_repeat:
            self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "shuffle-off.ico")))            
            self.shuffle_button.setDisabled(True)  
            self.previous_shuffle_state = self.music_on_shuffle
            self.music_on_shuffle = False     
        else:
            self.shuffle_button.setDisabled(False)          
            self.music_on_shuffle = self.previous_shuffle_state    
            if self.music_on_shuffle:
                self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-shuffle.ico")))              
            else:
                self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "shuffle.ico")))                                                                 
        
    def toggle_repeat(self):
        if self.music_on_repeat:
            self.repeat_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "repeat.ico")))
            self.repeat_button.setToolTip("Toggle Repeat")       
            self.music_on_repeat = False
        else:            
            self.repeat_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-repeat.ico")))            
            self.repeat_button.setToolTip("On Repeat")       
            self.music_on_repeat = True
            
        self.disable_shuffle()
        self.disable_loop_playlist()

    def toggle_shuffle(self):
        if self.music_on_shuffle:
            self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "shuffle.ico")))
            self.shuffle_button.setToolTip("Toggle Shuffle")       
            self.music_on_shuffle = False
        else:            
            self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-shuffle.ico")))            
            self.shuffle_button.setToolTip("On Shuffle")       
            self.music_on_shuffle = True
            self.parent.songTableWidget.playlist_changed = True
            self.parent.prepare_for_random()
            
        self.disable_loop_playlist()
                
    def play_pause_music(self):  
        if self.started_playing:  # pause state activating
            if not self.in_pause_state:
                # Record the current position before pausing
                self.paused_position = self.player.position()  # Assuming get_position() returns the current position in seconds or milliseconds
                
                self.player.pause()
                self.in_pause_state = True
                self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))
            else:
                # Set the position to the recorded value before resuming
                self.player.setPosition(self.paused_position)  # Assuming set_position() sets the playback position
                
                # Continue playing
                self.player.play()
                self.in_pause_state = False
                self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "pause.ico")))

    def pause(self):
        self.paused_position = self.player.position()  # Assuming get_position() returns the current position in seconds or milliseconds        
        self.in_pause_state = True
        self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))        
        self.player.pause()

    def get_current_time(self):
        position = self.player.position() / 1000.0
        return position

    def seek_forward(self):
        if self.player.isPlaying:
            self.player.setPosition(self.player.position() + 1000)

    def seek_backward(self):
        if self.player.isPlaying:        
            self.player.setPosition(self.player.position() - 1000)

    def get_duration(self):
        return self.player.duration()

    def get_position(self):
        return self.player.position()

    def handle_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.music_on_repeat:
                # Restart playback            
                self.player.setPosition(0)
                self.player.play()                
            else: 
                if self.music_on_shuffle:
                    self.playRandomSong()               
                else:
                    self.playNextSong()
