import socket
import sys
import threading
from datetime import datetime

HOST = '0.0.0.0'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind((HOST, PORT))
except socket.error as e:
    print(f"Could not bind to port {PORT}! Error: {e}")
    exit()
except Exception as e:
    print(f"Error: {e}")
    exit()


try:
    server.listen()
except Exception as e:
    print("Could not start listening!")
    exit()

print(f"Server listening on {HOST}:{PORT}")

clients = []

# def get_current_time():
#     now = datetime.now()
#     current_time = now.strftime("%H:%M:%S")
#     return current_time


def broadcast(message):
    for client in clients[:]:  # Iterate over a copy of the list
        try:
            client.send(message)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
            clients.remove(client)
            client.close()  # Ensure client socket is properly closed

def broadcast_except(message, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                clients.remove(client)

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                raise ConnectionError("Client disconnected")
            # add newline to the end of the message
            decoded_message = message.decode('utf-8')
            decoded_message = decoded_message.strip() + '\n'
            broadcast(decoded_message.encode('utf-8'))
            print(f"Message from {client.getpeername()}: {decoded_message}")
        except ConnectionError:
            client_address = client.getpeername()
            clients.remove(client)
            broadcast(f"Client {client_address} disconnected".encode('utf-8'))
            print(f"Client {client_address} disconnected")
            client.close()
            break
        except Exception as e:
            print(f"Error handling client: {e}")
            break


def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        clients.append(client)

        broadcast_except(f"> Client {str(address)} connected".encode('utf-8'), client)
        client.send(f"> Connected...".encode('utf-8'))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

try:
    receive()
except KeyboardInterrupt:
    print("Server stopped!")
    exit()