import logging
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
from ultralytics import YOLO
import math
from enum import Enum
from src.settings import Settings
from src.labels import Labels
from src.connection_manager import SocketClient
import time

class State(Enum):
    IDLE = 0
    RUNNING = 1
    STOPPED = 2
    EMERGENCY_STOPPED = 3
    WARNING = 4

class MonitorClient:
    def __init__(self, window):
        self.labels = Labels()
        self.settings = Settings()
        self.socketclient = SocketClient()
        self.state = State.IDLE
        self.det_confidence = 0.4
        self.window = window
        self.window.title(f"{self.labels.get('window_title_label')}")
        self.window.geometry(self.settings.get("window_geometry"))
        self.now = int(round(time.time() * 1000))
        self.type = self.settings.get("type")
        self.model = None

        self.running = False
        self.cap = None
        self.connected_webcams = []

        # Create the GUI elements
        self.create_gui()
        

    def create_gui(self):
        # Create a frame to contain the GUI elements
        self.gui_frame = tk.Frame(self.window)
        self.gui_frame.pack()

        # Status label
        self.status_label = tk.Label(self.gui_frame, text=f"{self.labels.get('status_label')}: {self.state.name}")
        self.status_label.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Dropdown for selecting webcams
        self.webcam_dropdown = tk.StringVar(self.gui_frame)
        self.webcam_dropdown.set(f"{self.labels.get('select_webcam_label')}")
        self.update_webcam_list()

        self.webcam_menu = tk.OptionMenu(self.gui_frame, self.webcam_dropdown, *self.connected_webcams)
        self.webcam_menu.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky="w")

        # Webcam screen
        self.webcam_screen = tk.Label(self.gui_frame, bg="black")
        self.set_screen_blank()
        self.webcam_screen.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # Server connection settings
        self.server_ip_label = tk.Label(self.gui_frame, text=f"{self.labels.get('server_ip_label')}")
        self.server_ip_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.server_ip_text = tk.StringVar(self.gui_frame, value=f"{self.settings.get('conn_ip')}")
        self.server_ip_entry = tk.Entry(self.gui_frame, textvariable=self.server_ip_text)
        self.server_ip_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.server_port_label = tk.Label(self.gui_frame, text=f"{self.labels.get('server_port_label')}")
        self.server_port_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.server_port_text = tk.StringVar(self.gui_frame, value=f"{self.settings.get('conn_port')}")
        self.server_port_entry = tk.Entry(self.gui_frame, textvariable=self.server_port_text)
        self.server_port_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.server_connect_button = tk.Button(self.gui_frame, text=f"{self.labels.get('connect_button_label')}", command=self.connect_to_server)
        self.server_connect_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        self.console_box = tk.Text(self.gui_frame, width=50, height=20)
        self.console_box.grid(row=0, column=5, columnspan=4, padx=10, pady=10, sticky="w")
        self.console_box.config(state="disabled")

        #self.draw_boxes_checkbox = tk.Checkbutton(self.gui_frame, text=f"{self.labels.get('draw_boxes_label')}")
        #TODO: Add functionality to toggle drawing detection boxes

        # Buttons
        self.connect_camera_button = tk.Button(self.gui_frame, text=f"{self.labels.get('camera_open_label')}", command=self.start_camera)
        self.start_button = tk.Button(self.gui_frame, text=f"{self.labels.get('start_button_label')}", command=self.start)
        self.stop_button = tk.Button(self.gui_frame, text=f"{self.labels.get('stop_button_label')}",command=self.stop)
        self.emergency_button = tk.Button(self.gui_frame, text=f"{self.labels.get('emergency_stop_label')}", command=self.emergency_stop)
        self.load_detection_model_button = tk.Button(self.gui_frame, text=f"{self.labels.get('load_model_label')}", command=self.load_detection_model)
        # self.load_cameras_button = tk.Button(self.gui_frame, text=f"{self.labels.get('load_cameras_label')}", command=self.update_webcam_list)
        self.reset_button = tk.Button(self.gui_frame, text=f"{self.labels.get('reset_button_label')}", command=self.reset)

        self.connect_camera_button.grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.connect_camera_button.config(state="disabled")

        self.start_button.grid(row=2, column=2, padx=10, pady=10, sticky="w")
        self.stop_button.grid(row=2, column=3, padx=10, pady=10, sticky="w")
        self.emergency_button.grid(row=3, column=3, columnspan=2, padx=10, pady=10, sticky="w")
        self.load_detection_model_button.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        self.reset_button.grid(row=4, column=2, padx=10, pady=10, sticky="w")

        

        self.start_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.server_connect_button.config(state="disabled")



        # self.load_cameras_button.grid(row=4, column=1, padx=10, pady=10, sticky="w")

    def update_webcam_list(self):
        self.connected_webcams = []
        self.connected_webcams.append(f"{self.labels.get('select_webcam_label')}")

        self.connected_webcams = [f"{self.labels.get('camera_number_label')} {i}" for i in range(self.settings.get('cameras_to_load')) if self.check_camera_available(i)]
        if len(self.connected_webcams) == 0:
            self.connected_webcams = [f"{self.labels.get('no_webcam_label')}"]
            
        else:
            self.webcam_dropdown.set(self.connected_webcams[0])

    def check_camera_available(self, index):
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            return False
        else:
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Convert to RGB for PIL compatibility
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)

                # Perform object detection
                results = self.model(pil_image, conf=self.settings.get("ai_confidence"))
                
                # annotated_frame = results[0].plot(boxes=False)
                annotated_frame = results[0].plot(boxes=True)  # plot the results
                detected_objects = []
                confidence = 0
                cls = 0

                for r in results:
                    boxes = r.boxes

                    for box in boxes:
                        confidence = math.ceil((box.conf[0]*100)) / 100
                        cls = int(box.cls[0])
                        # print(f"{self.class_names[cls]}: {confidence}")
                        detected_objects.append(f"{self.class_names[cls]}: {confidence}")
                self.console_box.config(state="normal")
                self.console_box.delete(1.0, tk.END)
                self.console_box.insert(tk.END, f"{detected_objects}")
                self.console_box.see(tk.END)
                self.console_box.config(state="disabled")

                if self.now + 250 < int(round(time.time() * 1000)):
                    self.now = int(round(time.time() * 1000))
                    if self.socketclient.is_connected() and self.state == State.RUNNING:
                        if len(detected_objects) > 0:
                            # self.socketclient.send_message(f"{self.class_names[cls]}: {confidence}")
                            self.socketclient.send_message(f"{detected_objects[0]}\n")

        
                # Convert the annotated frame back to ImageTk format
                annotated_image = Image.fromarray(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
                frame_tk = ImageTk.PhotoImage(image=annotated_image)

                # Update the webcam screen with the modified frame
                self.webcam_screen.configure(image=frame_tk)
                self.webcam_screen.image = frame_tk

            self.window.update()
        self.set_screen_blank()

    def load_detection_model(self):
        self.model = YOLO(self.settings.get("ai_model", "yolov8n.pt"))
        self.class_names = self.model.names
        self.connect_camera_button.config(state="normal")
        self.load_detection_model_button.config(state="disabled")

    def start_camera(self):
        if self.running:
            messagebox.showinfo("Info", f"{self.labels.get('camera_already_running')}")
            return

        selected_webcam = int(self.webcam_dropdown.get().split(" ")[-1])

        self.connect_camera_button.config(text=f"{self.labels.get('opening_camera')}", state="disabled")

        # Initialize and start the camera in a separate thread
        threading.Thread(target=self.initialize_camera, args=(selected_webcam,), daemon=True).start()

    def initialize_camera(self, camera_index):
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            messagebox.showerror("Error", f"{self.labels.get('camera_failed_to_open')}")
            return

        # Set the size of the webcam screen based on the webcam's resolution
        self.webcam_screen.config(width=640, height=480)

        self.running = True
        self.window.after(0, self.set_camera_button_to_stop)

        self.server_connect_button.config(state="normal")
        self.start_button.config(state="normal")
        self.stop_button.config(state="normal")

        # Start updating frames in a separate thread
        threading.Thread(target=self.update_frame, daemon=True).start()

    def set_camera_button_to_stop(self):
        self.connect_camera_button.config(text=f"{self.labels.get('camera_stop')}", command=self.stop_camera, state="normal")
        self.set_screen_blank()

    def stop_camera(self):
        if self.running:
            self.running = False
            self.connect_camera_button.config(text=f"{self.labels.get('camera_open_label')}", command=self.start_camera, state="normal")
            self.socketclient.disconnect()
            self.server_connect_button.config(text=f"{self.labels.get('connect_to_server_button')}", command=self.connect_to_server)
            self.console_box.config(state="normal")
            self.console_box.delete(1.0, tk.END)
            self.console_box.insert(tk.END, f"Disconnected from server due to camera stop")
            self.console_box.see(tk.END)
            self.console_box.config(state="disabled")
            self.cap.release()

    def emergency_stop(self):
        self.status_label.config(text=f"{self.labels.get('status_label')}: {State.EMERGENCY_STOPPED.name}")
        self.socketclient.send_message("EMERGENCY")
        self.state = State.EMERGENCY_STOPPED

        self.start_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.emergency_button.config(state="disabled")

    def start(self):
        self.status_label.config(text=f"{self.labels.get('status_label')}: {State.RUNNING.name}")
        self.socketclient.send_message("Start")
        self.state = State.RUNNING
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.emergency_button.config(state="normal")
    
    def stop(self):
        self.status_label.config(text=f"{self.labels.get('status_label')}: {State.STOPPED.name}")
        self.socketclient.send_message("Stop")
        self.state = State.STOPPED

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.emergency_button.config(state="normal")

    def reset(self):
        self.status_label.config(text=f"{self.labels.get('status_label')}: {State.IDLE.name}")
        self.socketclient.send_message("Reset")
        self.state = State.IDLE

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.emergency_button.config(state="disabled")

    def set_screen_blank(self):
        blank_image = Image.new('RGB', (640, 480), (0, 0, 0))
        blank_photo = ImageTk.PhotoImage(blank_image)
        self.webcam_screen.configure(image=blank_photo)
        self.webcam_screen.image = blank_photo

    def connect_to_server(self):
        ip = self.server_ip_text.get()
        port = int(self.server_port_text.get())

        logging.info(f"Connecting to {self.server_ip_text.get()}:{self.server_port_text.get()}")
        self.server_connect_button.config(text=f"{self.labels.get('disconnect_from_server_button')}", command=self.disconnect_from_server)
        threading.Thread(target=lambda: self.socketclient.connect(ip, port), daemon=True).start()
        
    def disconnect_from_server(self):
        logging.info(f"Disconnecting from {self.server_ip_text.get()}:{self.server_port_text.get()}")
        self.socketclient.disconnect()
        self.server_connect_button.config(text=f"{self.labels.get('connect_to_server_button')}", command=self.connect_to_server)

    def on_close(self):
        if messagebox.askokcancel("Quit", f"{self.labels.get('confirm_exit')}"):
            self.stop_camera()
            self.socketclient.disconnect()
            self.window.destroy()

if __name__ == "__main__":
    import cProfile
    import pstats

    debug = False

    if debug:
        pr = cProfile.Profile()
        pr.enable()
    
    window = tk.Tk()
    app = MonitorClient(window)
    logging.basicConfig(level=logging.INFO)
    window.protocol("WM_DELETE_WINDOW", app.on_close)
    window.mainloop()

    if debug:
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative').print_stats(10)  # Print the top 10 time-consuming functions