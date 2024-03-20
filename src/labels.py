import logging
from src.setting_manager import SettingsManager

class Labels:

    def __init__(self):
        self.mgr = SettingsManager("messages.yaml")
        
        messages = {
            "window_title_label": "AI Sorter",
            "confirm_exit": "Do you want to quit?",
            "start_button_label": "Start",
            "stop_button_label": "Stop",
            "emergency_stop_label": "Emergency Stop",
            "server_ip_label": "Server IP:",
            "server_port_label": "Server Port:",
            "status_label": "Status:",
            "select_webcam_label": "Select Webcam",
            "no_webcam_label": "No webcams available",
            "camera_number_label": "Camera:",
            "camera_already_running": "Webcam is already running.",
            "camera_failed_to_open": "Failed to open the webcam.",
            "camera_stop": "Stop Camera",
            "camera_open_label": "Open Camera",
            "camera_close_label": "Close Camera",
            "error_occured": "Error occured!",
            "error_connecting": "Could not connect to server! Error: ",
            "connected_to_server": "Connected to ",
            "load_model_label": "Load Detection Model",
            "load_cameras_label": "Load Cameras",
            "connect_to_server_button": "Connect...",
            "disconnect_from_server_button": "Disconnect",
            "server_disconnected": "Server disconnected!",
            "connect_button_label": "Connect",
            "disconnect_button_label": "Disconnect",
            'not_connected_to_server': 'Not connected to server!',
            'disconnected_from_server': 'Disconnected from server!',
            'opening_camera': 'Opening camera...',
            'draw_boxes_label': 'Draw boxes',
            'reset_button_label': 'Reset',
        }
        self.settings = self.mgr.load_or_create_settings(messages)

    def get(self, key, default=None):
        # Splitting the key to support nested dictionaries
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            logging.warning(f"Key '{key}' not found in settings file.")
            return default


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    labels = Labels()
    print(labels.get("window_title_label"))
    print(labels.get("server_port_label"))
    print(labels.get("this_is_missing"))
