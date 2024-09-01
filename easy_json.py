import json
import os

class EasyJson:
    def __init__(self, config_file):
        self.config_file = config_file
        self.script_path = os.path.dirname(os.path.abspath(__file__))
        
    def setupDefaultFiles(self):
        self.edit_value("background_image", os.path.join(self.script_path, "background-images", "default.jpg"))
    
    def get_value(self, key):
        print("in ej, get value")
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
        print("in edit value")
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
