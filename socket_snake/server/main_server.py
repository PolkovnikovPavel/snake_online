import asyncio
import threading
import time
import socket

from player import *

HOST = "localhost"
PORT = 1234


class Game:
    def __init__(self):
        self.speed = SPEED
        self.local_time = 0
        self.gl_steps_time = 0
        self.width = 100
        self.height = 100
        self.count_of_eat = 0
        self.greed = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.players = []
        self.next_player_id = 0

    def echo(self, connection, addr):
        while True:
            data = connection.recv(1024).decode("utf-8")
            try:
                message = json.loads(data)
            except Exception as e:
                print('не json строка')
                connection.send(bytes('не json строка', encoding='UTF-8'))
                return
            if message == 'con':
                threading.Event().wait(self.speed - (time.time() - self.local_time))

                self.init_player(connection)
                # self.give_player_info(connection, self.next_player_id)
            elif 'type' in message:
                if not self.get_data_player(message):
                    print('отсутствуют необходимые поля или такого пользователя нет')
                    connection.send(bytes('отсутствуют необходимые поля или такого пользователя нет', encoding='UTF-8'))

            else:
                print('нет такой команды')
                connection.send(bytes('нет такой команды', encoding='UTF-8'))

    def init_player(self, websocket):
        self.next_player_id += 1
        player = Player(self.next_player_id, websocket, 50, 50, 1, self)
        for i in range(10):
            player.add_part()
        player.last_answer = self.gl_steps_time
        self.players.append(player)
        print(f'Connect new player id = {player.id}, (x, y) = ({player.head.x}, {player.head.y})')
        # TODO появление игрока

    def give_player_info(self, socket, id, player=None):
        res = {}
        res['id'] = id
        res['speed'] = self.speed
        res['gl_steps_time'] = self.gl_steps_time
        res['width'] = self.width
        res['height'] = self.height
        res['greed'] = self.greed
        if player is None:
            res['player'] = {}
        else:
            res['player'] = player.get_json()
        res['other_players'] = []
        for p in self.players:
            if p.id == id:
                res['player'] = p.get_json()
            else:
                res['other_players'].append(p.get_json())

        try:
            send_long_message(socket, json.dumps(res))
            if player is not None:
                player.count_reconnection = MAXCOUNTRECONNECTING
        except Exception as e:
            if player is not None:
                player.count_reconnection -= 1
                if player.count_reconnection < 0:
                    print(f'Отключён id={player.id} по ошибке за многократное повторение "{e}"')
                    self.disconnect(player)

    def run(self):
        self.local_time = time.time()
        self.main_cycle()

    def disconnect(self, player):
        player.die()
        player.socket.close()
        self.players.remove(player)
        del player

    def get_data_player(self, message):
        if 'id' not in message or'type' not in message or 'd' not in message:
            return False
        type = message['type']
        if type == 'cheng_d':
            for player in self.players:
                if player.id == message['id']:
                    player.cheng_direction(message['d'])
                    player.last_answer = self.gl_steps_time
                    return True

        return False

    def spawn_eat(self):
        unique_points = set()
        while len(unique_points) < MAX_COUNT_EAT - self.count_of_eat:
            x = random.randint(1, self.width - 1)
            y = random.randint(1, self.height - 1)
            unique_points.add((x, y))
        points_list = list(unique_points)
        self.count_of_eat = MAX_COUNT_EAT

        for x, y in points_list:
            if self.greed[y][x] == 0:
                self.greed[y][x] = 1
            else:
                self.count_of_eat -= 1


    def update_all(self):
        self.gl_steps_time += 1
        self.spawn_eat()
        temp_copy = [player for player in self.players]
        for player in temp_copy:
            player.move()
            if self.gl_steps_time - player.last_answer > RUNTIMEERROR:
                print(f'Отключён id={player.id} за долгое молчание ({RUNTIMEERROR} ходов подряд)')
                self.disconnect(player)
            else:
                self.give_player_info(player.socket, player.id, player)

    def main_cycle(self):
        while True:
            print(f'\n{self.gl_steps_time + 1} - {len(self.players)}) ', end='')

            self.update_all()
            print('...', end='')
            threading.Event().wait(self.speed - (time.time() - self.local_time))
            self.local_time = time.time()


def send_long_message(connection, m):
    length = len(m) // 1024 + 1
    connection.send(bytes(str(length), encoding='UTF-8'))
    i = -1
    for i in range(length - 1):
        connection.send(bytes(m[i * 1024:(i+1) * 1024], encoding='UTF-8'))
    connection.send(bytes(m[(i+1) * 1024:], encoding='UTF-8'))

def start_server(game):
    print("First function...")
    game.run()


def start_echo(server_socket, game):
    while True:
        connection, address = server_socket.accept()
        print("new connection from {address}".format(address=address))

        client_thread = threading.Thread(target=game.echo, args=(connection, address,))
        client_thread.start()


def main():
    game = Game()

    # Запускаем Socket сервер
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    print("TCP Socket server started")

    # Запускаем параллельную задачу
    logic_thread = threading.Thread(target=start_server, args=(game,))
    logic_thread.start()

    echo_thread = threading.Thread(target=start_echo, args=(server_socket, game, ))
    echo_thread.start()

    # Запускаем бесконечный цикл
    while True:
        threading.Event().wait(1)  # Можно использовать любую неблокирующую задержку


if __name__ == "__main__":
    main()
