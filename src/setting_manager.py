import os
import yaml

class SettingsManager():
    def __init__(self, config_file):
        self.config_file = config_file

    def load_or_create_settings(self, settings):
        if not os.path.exists(os.path.join(os.getcwd(), self.config_file)):
            with open(self.config_file, 'w') as file:
                yaml.dump(settings, file, default_flow_style=False)
            return settings
        else:
            # check for missing keys and if they are missing, add them to the settings file and then return the settings
            with open(os.path.join(os.getcwd(), self.config_file), 'r') as file:
                loaded_settings = yaml.safe_load(file)
                for key in list(loaded_settings.keys()):
                    if key not in settings:
                        print(f"Removing key {key} from settings file.")
                        del loaded_settings[key]
                for key in settings:
                    if key not in loaded_settings:
                        print(f"Key {key} not found in settings file. Adding it with default value '{settings[key]}'")
                        loaded_settings[key] = settings[key]
                with open(self.config_file, 'w') as file:
                    yaml.dump(loaded_settings, file, default_flow_style=False)
                return loaded_settings

    def get_setting(self, key, default=None):
        # Splitting the key to support nested dictionaries
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            print(f"Key {key} not found in settings file.")
            return default

