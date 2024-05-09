import socket

HOST = "localhost"
PORT = 1234

# Настраиваем сокет
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(10)
print('server is running, please, press ctrl+c to stop')

# Слушаем запросы
while True:
    connection, address = server_socket.accept()
    print("new connection from {address}".format(address=address))

    data = connection.recv(1024)
    print(str(data))

    connection.send(bytes('Hello from server!', encoding='UTF-8'))

    connection.close()
