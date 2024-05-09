import socket

HOST = "localhost"
PORT = 1234

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(bytes("Hello, world", "utf-8"))
    data = s.recv(1024).decode("utf-8")

print(f"Received {data}")