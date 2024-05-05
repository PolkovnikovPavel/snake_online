import socket, time

address_to_server = ('localhost', 8686)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(address_to_server)

t = time.time()
client.send(bytes("hello from client number ", encoding='UTF-8'))

data = client.recv(1024)
print(time.time() - t)
print(str(data))
