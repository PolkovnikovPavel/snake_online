import json
import multiprocessing as mp
import sys
import random

SPEED = 0.1
MAX_COUNT_EAT = 200

RUNTIMEERROR = 50
MAXCOUNTRECONNECTING = 30

WHITE = (255, 255, 255)  # установка цветов
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
LIGHT_GREEN = (0, 220, 10)
BROWN = (74, 47, 4)
GRAY = (128, 128, 128)
LIGHT_GRAY = (210, 210, 210)
LIGHT_RED = (255, 125, 131)


class Player:
    def __init__(self, id, socket, x, y, d, game):
        self.count_reconnection = MAXCOUNTRECONNECTING
        self.last_answer = 0
        self.socket = socket
        self.id = id
        self.game = game
        self.points = 0
        self.size = 1
        self.head = Part(x, y, d, True, grid=game.greed)
        self.snake = [self.head]
        self.add_part()
        self.add_part()

    def move(self):
        for i in range(self.size - 1, -1, -1):
            self.snake[i].move(self)

    def add_part(self):
        last = self.snake[-1]
        if last.d == 1:
            x, y = last.x, last.y + 1
        elif last.d == 2:
            x, y = last.x + 1, last.y
        elif last.d == 3:
            x, y = last.x, last.y - 1
        elif last.d == 4:
            x, y = last.x - 1, last.y
        else:
            x, y = last.x, last.y + 1
        self.snake.append(Part(x, y, last.d, False, last, grid=self.game.greed))
        last.next = self.snake[-1]
        self.size += 1

    def cheng_direction(self, d):
        self.snake[0].d = d

    def draw(self, screen, call_size=10, color=BLUE):
        for part in self.snake:
            part.draw(screen, call_size, color)

    def get_json(self):
        res = {'id': self.id, 'x': self.head.x, 'y': self.head.y, 'd': self.head.d, 'snake': []}
        for p in self.snake:
            res['snake'].append((p.x, p.y))
        return res

    def load_json(self, js):
        if js['id'] != self.id:
            raise Exception('Not right id')
        self.head.x, self.head.y, self.head.d = js['x'], js['y'], js['d']
        if len(js['snake']) != len(self.snake):
            if len(js['snake']) > len(self.snake):
                for _ in range(len(js['snake']) - len(self.snake)):
                    self.add_part()
            else:
                for _ in range(len(self.snake) - len(js['snake'])):
                    del self.snake[-1]

        i = -1
        for x, y in js['snake']:
            i += 1
            self.snake[i].x = x
            self.snake[i].y = y

    def die(self):
        for p in self.snake:
            p.die()


class Part:
    def __init__(self, x, y, d, is_head, prev=None, next=None, grid=None):
        self.x = x
        self.y = y
        self.d = d  # 1 - вверх, 2 - вправо, 3 - вниз, 4 - влево
        self.is_head = is_head
        self.prev = prev
        self.next = next
        self.grid = grid

    def move(self, player):
        if not (self.x >= 0 and self.x < len(self.grid) and self.y >= 0 and self.y < len(self.grid)):
            return
        if self.is_head:
            if self.d == 1:
                self.y -= 1
            elif self.d == 2:
                self.x += 1
            elif self.d == 3:
                self.y += 1
            elif self.d == 4:
                self.x -= 1
            if self.grid[self.y][self.x] == 1:
                player.add_part()
                player.game.count_of_eat -= 1
            self.grid[self.y][self.x] = -1
            return
        if self.next is None:
            self.grid[self.y][self.x] = 0
        self.x = self.prev.x
        self.y = self.prev.y
        self.d = self.prev.d

    def die(self):
        pass


class EAT:
    def __init__(self, x, y, coast):
        self.x = x
        self.y = y
        self.coast = coast
