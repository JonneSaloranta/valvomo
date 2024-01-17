import socket
from src.labels import Labels
from src.settings import Settings
import threading

class SocketClient:
    def __init__(self):
        self.labels = Labels()
        self.settings = Settings()

        self.host = None
        self.port = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.running = False

        self.receive_thread = threading.Thread(target=self.receive, daemon=True)
        self.send_thread = threading.Thread(target=self.send, daemon=True)

    def is_connected(self):
        return self.connected

    def connect(self, ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = port
        try:
            self.client.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # Start threads only after successful connection
            self.receive_thread = threading.Thread(target=self.receive, daemon=True)
            self.receive_thread.start()
            self.send_thread = threading.Thread(target=self.send, daemon=True)
            self.send_thread.start()
        except socket.error as e:
            print(f"{self.labels.get('error_connecting')}{e}")

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message:
                    # print(f"{self.labels.get('server_disconnected')}")
                    # self.disconnect()
                    break
                print(message)
            except Exception as e:
                print(f"{self.labels.get('error_occured')}{e}")
                break


    def send(self):
        while self.running:
            try:
                message = input('')
                if message:
                    self.client.send(message.encode('utf-8'))
                else:
                    break
            except Exception as e:
                print(f"{self.labels.get('error_occured')}{e}")
                break

    def send_message(self, message):
        if not self.connected:
            print(f"{self.labels.get('not_connected_to_server')}")
            return

        try:
            self.client.send(message.encode('utf-8'))
        except Exception as e:
            print(f"{self.labels.get('error_occured')}{e}")
            self.disconnect()


    def disconnect(self):
        if self.connected:
            self.running = False
            self.client.close()
            self.connected = False
            print(f"{self.labels.get('disconnected_from_server')}")


    def set_ip(self, ip):
        self.host = ip
        self.settings.set("conn_ip", ip)
        self.settings.save()

    def set_port(self, port):
        self.port = port
        self.settings.set("conn_port", port)
        self.settings.save()

if __name__ == "__main__":
    socketclient = SocketClient()
    socketclient.connect('127.0.0.1', 12345)
    try:
        while socketclient.is_connected():
            message = input('')
            if message:
                socketclient.send_message(message)
            else:
                break
    except KeyboardInterrupt:
        socketclient.disconnect()
