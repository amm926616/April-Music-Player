import json
import os
import platform
import inspect


class EasyJson:
    def __init__(self):
        if platform.system() == "Windows":
            self.config_path = os.path.join(os.getenv('APPDATA'), 'April Music Player')
        else:
            self.config_path = os.path.join(os.path.expanduser("~"), '.config', 'april-music-player')

        config_file = os.path.join(self.config_path, "config.json")

        self.config_file = config_file
        self.script_path = os.path.dirname(os.path.abspath(__file__))

    def setupBackgroundImage(self):
        self.edit_value("background_image", os.path.join(self.script_path, "background-images", "default.jpg"))

    def setupLyricsColor(self):
        self.edit_value("lyrics_color", "white")

    def get_value(self, key):
        # Get the frame of the caller
        caller_frame = inspect.currentframe().f_back
        # Get file name and line number of the caller
        caller_info = inspect.getframeinfo(caller_frame)
        print(f"Called from File: {caller_info.filename}, Line: {caller_info.lineno}")

        if not os.path.exists(self.config_file):
            print(f"Error: The file {self.config_file} does not exist.")
            return None

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON. The file may be corrupted or invalid.")
            return None
        except IOError as e:
            print(f"Error: Failed to read file {self.config_file}. {e}")
            return None

        if key not in data:
            print(f"Error: Key '{key}' not found in the JSON data.")
            return None

        return data[key]

    def setup_default_values(self, lrc_font_size=60, fresh_config=False):
        START = "'\033[92m"
        END = "\033[97m"
        default_values = {
            "english_font": os.path.join(self.script_path, "fonts/PositiveForward.otf"),
            "korean_font": os.path.join(self.script_path, "fonts/NotoSerifKR-ExtraBold.ttf"),
            "japanese_font": os.path.join(self.script_path, "fonts/NotoSansJP-Bold.otf"),
            "chinese_font": os.path.join(self.script_path, "fonts/NotoSerifKR-ExtraBold.ttf"),
            "lrc_font_size": lrc_font_size,
            "sync_threshold": 0.3,
            "lyrics_color": "white",
            "show_lyrics": True,
            "shuffle": False,
            "repeat": False,
            "loop": False,
            "previous_loop": False,
            "previous_shuffle": False,
            "music_directories": {},
            "last_played_song": {}
        }

        if fresh_config:
            with open(self.config_file, "w") as f:
                json.dump(default_values, f, indent=4)
            f.close()
            print(f"{START}default values added to config file{END}")
            print("This is from default value setup method")
            for i in default_values.items():
                print(i)
        else:
            # Iterate over the default values and set them if not present
            for key, default_value in default_values.items():
                if self.get_value(key) is None:
                    self.edit_value(key, default_value)

    def edit_value(self, key, value):
        try:
            # Open the file and load the JSON data
            with open(self.config_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON. The file may be corrupted or invalid.")
            return
        except IOError as e:
            print(f"Error: Failed to read file {self.config_file}. {e}")
            return

        # Update the key-value pair
        data[key] = value

        try:
            # Write the updated data back to the config file
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
                f.close()
        except IOError as e:
            print(f"Error: Failed to write to file {self.config_file}. {e}")
