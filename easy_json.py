import json
import os
import platform


class EasyJson:
    def __init__(self):
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.getenv('APPDATA'), 'April Music Player')
        else:
            self.config_path = os.path.join(os.path.expanduser("~"), '.config', 'april-music-player')

        config_file = os.path.join(self.config_path, "configs", "config.json")
        self.config_file = config_file

        self.script_path = os.path.dirname(os.path.abspath(__file__))

        # Load the JSON data once at initialization
        self.data = self._load_json()

    def _load_json(self):
        """Load the JSON file and return the data as a dictionary."""
        if not os.path.exists(self.config_file):
            return {}  # Return an empty dictionary if the file doesn't exist

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Error: Unable to read or decode {self.config_file}. Returning empty config.")
            return {}

    def _save_json(self):
        """Save the current data to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=4)
        except IOError as e:
            print(f"Error: Failed to write to file {self.config_file}. {e}")
        self._load_json()

    def get_value(self, key):
        """Retrieve the value of a key from the JSON data."""
        return self.data.get(key, None)

    def edit_value(self, key, value):
        """Edit the value of a key in the JSON data."""
        self.data[key] = value
        self._save_json()

    def setup_default_values(self, lrc_font_size=60, fresh_config=False):
        default_values = {
            "english_font": os.path.join(self.script_path, "fonts/PositiveForward.otf"),
            "korean_font": os.path.join(self.script_path, "fonts/NotoSerifKR-ExtraBold.ttf"),
            "japanese_font": os.path.join(self.script_path, "fonts/NotoSansJP-Bold.otf"),
            "chinese_font": os.path.join(self.script_path, "fonts/NotoSerifKR-ExtraBold.ttf"),
            "lrc_font_size": lrc_font_size,
            "sync_threshold": 0.3,
            "lyrics_color": "white",
            "show_lyrics": True,
            "play_song_at_startup": False,
            "shuffle": False,
            "repeat": False,
            "loop": False,
            "previous_loop": False,
            "previous_shuffle": False,
            "music_directories": {},
            "last_played_song": {}
        }

        if fresh_config:
            self.data = default_values  # Replace with default values
            self._save_json()
        else:
            # Add any missing default values
            for key, default_value in default_values.items():
                if key not in self.data:
                    self.data[key] = default_value
            self._save_json()
