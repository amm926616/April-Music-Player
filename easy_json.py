import json
import os
import platform

class EasyJson:
    def __init__(self, config_file=None):
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
    
    def edit_value(self, key, value):
        if not os.path.exists(self.config_file):
            print(f"Error: The file {self.config_file} does not exist.")
            return
        
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON. The file may be corrupted or invalid.")
            return
        except IOError as e:
            print(f"Error: Failed to read file {self.config_file}. {e}")
            return
        
        data[key] = value
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error: Failed to write to file {self.config_file}. {e}")
