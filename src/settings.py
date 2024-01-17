from src.setting_manager import SettingsManager

class Settings:

    def __init__(self):
        self.mgr = SettingsManager("settings.yaml")
        
        settings = {
            "conn_ip": "127.0.0.1",
            "conn_port": 12345,
            "default_camera": 0,
            "cameras_to_load": 5,
            "window_width": 1280,
            "window_height": 720,
            "ai_model": "yolov8n.pt",
            "ai_confidence": 0.4,
        }
        self.settings = self.mgr.load_or_create_settings(settings)

    def get(self, key, default=None):
        # Splitting the key to support nested dictionaries
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default


if __name__ == "__main__":
    settings = Settings()