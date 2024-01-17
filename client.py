import socket
import threading
# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the port on which you want to connect
IP = 'localhost'
PORT = 12345

# connect to the server on local computer
try:
    client.connect((IP, PORT))
except socket.error as e:
    print(f"Could not connect to server! Error: {e}")
    exit()

def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            print(message)
        except Exception as e:
            print("An error occured!")
            client.close()
            break

def send():
    while True:
        message = input('')
        client.send(message.encode('utf-8'))

thread_receive = threading.Thread(target=receive)
thread_receive.start()

thread_send = threading.Thread(target=send)
thread_send.start()