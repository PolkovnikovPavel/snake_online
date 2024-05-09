import asyncio
import threading
import time

import pygame
import socket
import random

from player import *


HOST = "217.71.129.139"
PORT = 4674

HOST = "localhost"
PORT = 1234

class Game:
    def __init__(self):
        self.speed = 2
        self.local_time = 0
        self.gl_steps_time = 0
        self.width = 100
        self.height = 100
        self.greed = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.players = []
        self.next_player_id = 0

        self.player = None
        self.my_id = 0
        self.screen_width = 1000
        self.screen_height = 1000
        self.screen = None
        self.direction = 1
        self.all_eats = []
        self.is_start = True

    def init_game(self, s, js):
        self.my_id = js['id']
        self.player = Player(js['id'], s, js['player']['x'], js['player']['y'], js['player']['d'], self)
        self.players.append(self.player)
        for p in js['other_players']:
            new_p = Player(p['id'], None, p['x'], p['y'], p['d'], self)
            self.players.append(new_p)

    async def on_message(self, s, message):
        try:
            response = json.loads(message)
        except Exception as e:
            print(message, '\n--------------\n')
            print(e)
            pygame.quit()
            sys.exit()

        self.local_time = time.time()
        print(response['gl_steps_time'], end=' - ')
        print(f"({response['player']['x']}, {response['player']['y']})")

        if self.player is None:
            self.init_game(s, response)
        self.load_data_from_json(response)

        try:
            msg = json.dumps({'id': response['id'], 'type': 'cheng_d', 'd': self.direction})
            s.sendall(bytes(msg, 'utf-8'))
        except Exception as e:
            print(e)

    def update_all(self):
        self.gl_steps_time += 1
        temp_copy = [player for player in self.players]
        for player in temp_copy:
            player.move()

    def load_grid(self):
        self.all_eats = []
        for y in range(self.height):
            for x in range(self.width):
                if self.greed[y][x] == 1:
                    self.all_eats.append(EAT(x, y, 1))

    def load_data_from_json(self, js):
        self.my_id = js['id']
        self.speed = js['speed']
        self.gl_steps_time = js['gl_steps_time']
        self.width = js['width']
        self.height = js['height']
        self.greed = js['greed']
        self.load_grid()
        self.player.load_json(js['player'])

        for_del = [p for p in self.players[1:]]
        for_new = []

        for js_p in js['other_players']:
            player = None
            for p in self.players:
                if p.id == js_p['id']:
                    player = p
                    for_del.remove(player)
                    break
            if player is None:
                new = Player(js_p['id'], None, js_p['x'], js_p['y'], js_p['d'], self)
                new.load_json(js_p)
                for_new.append(new)
            else:
                player.load_json(js_p)
        for p in for_del:
            self.players.remove(p)
        for p in for_new:
            self.players.append(p)

    def draw_screen(self):
        size = self.screen_width // self.width
        for i in range(self.height + 1):
            pygame.draw.line(self.screen, LIGHT_GRAY, (i * size, 0), (i * size, self.screen_height))
            pygame.draw.line(self.screen, LIGHT_GRAY, (0, i * size), (self.screen_width, i * size))

        for eat in self.all_eats:
            eat.draw(self.screen, size, self.greed)

        for player in self.players:
            if player.id == self.my_id:
                color = LIGHT_GREEN
            else:
                color = LIGHT_RED
            player.draw(self.screen, size, color)

    def main_cycle(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        while self.local_time == 0:    # когда станет != 0 значит пришёл ответ от сервера
            timer_fps = time.time()
            self.screen.fill(WHITE)
            # self.draw_screen()
            # TODO анимация загрузки

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_start = False
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()
            threading.Event().wait(max((1 / 60) - (time.time() - timer_fps), 0))

        while True:
            timer_fps = time.time()
            self.screen.fill(WHITE)
            self.draw_screen()

            if timer_fps - self.local_time >= self.speed * 1.1:
                self.update_all()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_start = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.direction = 4
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.direction = 3
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.direction = 2
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.direction = 1
            pygame.display.flip()

            threading.Event().wait(max((1 / 60) - (time.time() - timer_fps), 0))


def get_long_message(socket):
    m = ''
    length = int(socket.recv(1024).decode("utf-8"))
    for i in range(length):
        m += socket.recv(1024).decode("utf-8")
    return m


async def main():
    game = Game()

    independent_thread = threading.Thread(target=main_cycle_wrapper, args=(game,))
    independent_thread.start()

    tasks = [
        asyncio.create_task(connect_to_server(HOST, PORT, game))
    ]

    # Ждем завершения обеих задач
    await asyncio.gather(*tasks)


def main_cycle_wrapper(game):
    game.main_cycle()


async def connect_to_server(HOST, PORT, game):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(json.dumps("con"), "utf-8"))
        while game.is_start:
            try:
                message = get_long_message(s)
            except Exception as e:
                print(e)
            await game.on_message(s, message)


if __name__ == "__main__":
    asyncio.run(main())






