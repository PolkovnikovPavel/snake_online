import asyncio
import time
import websockets

from player import *


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

    async def echo(self, websocket, path):
        async for message in websocket:
            try:
                message = json.loads(message)
            except Exception as e:
                print('не json строка')
                await websocket.send('не json строка')
                return
            if message == 'con':
                await asyncio.sleep(self.speed - (time.time() - self.local_time))

                await self.init_player(websocket)
                await self.give_player_info(websocket, self.next_player_id)
            elif 'type' in message:
                if not self.get_data_player(message):
                    print('отсутствуют необходимые поля или такого пользователя нет')
                    await websocket.send('отсутствуют необходимые поля или такого пользователя нет')

            else:
                print('нет такой команды')
                await websocket.send('нет такой команды')

    async def init_player(self, websocket):
        self.next_player_id += 1
        player = Player(self.next_player_id, websocket, 50, 50, 1, self)
        for i in range(10):
            player.add_part()
        player.last_answer = self.gl_steps_time
        self.players.append(player)
        print(f'Connect new player id = {player.id}, (x, y) = ({player.head.x}, {player.head.y})')
        # TODO появление игрока

    async def give_player_info(self, websocket, id, player=None):
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
            await websocket.send(json.dumps(res))
            if player is not None:
                player.count_reconnection = MAXCOUNTRECONNECTING
        except Exception as e:
            if player is not None:
                player.count_reconnection -= 1
                if player.count_reconnection < 0:
                    print(f'Отключён id={player.id} по ошибке за многократное повторение "{e}"')
                    self.disconnect(player)

    async def run(self):
        self.local_time = time.time()
        await self.main_cycle()

    def disconnect(self, player):
        player.die()
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


    async def update_all(self):
        self.gl_steps_time += 1
        self.spawn_eat()
        temp_copy = [player for player in self.players]
        for player in temp_copy:
            player.move()
            if self.gl_steps_time - player.last_answer > RUNTIMEERROR:
                print(f'Отключён id={player.id} за долгое молчание ({RUNTIMEERROR} ходов подряд)')
                self.disconnect(player)
            else:
                await self.give_player_info(player.websocket, player.id, player)

    async def main_cycle(self):
        while True:
            print(f'\n{self.gl_steps_time + 1} - {len(self.players)}) ', end='')

            await self.update_all()
            print('...', end='')
            await asyncio.sleep(self.speed - (time.time() - self.local_time))
            self.local_time = time.time()


async def start_server(game):
    print("First function...")
    await game.run()


async def main():
    game = Game()

    # Запускаем WebSocket сервер
    server = await websockets.serve(game.echo, "localhost", 8765)
    print("WebSocket server started")

    # Запускаем параллельную задачу
    parallel_task_coroutine = start_server(game)
    parallel_task_task = asyncio.create_task(parallel_task_coroutine)

    # Запускаем бесконечный цикл
    while True:
        await asyncio.sleep(1)  # Можно использовать любую неблокирующую задержку

if __name__ == "__main__":
    asyncio.run(main())