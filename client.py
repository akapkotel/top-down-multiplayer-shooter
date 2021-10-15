#!/usr/bin/env python

import arcade

from game import Player, PLAYERS_COLORS
from networking import NetworkClient

WIDTH = 500
HEIGHT = 500
TITLE = 'Client'
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class GameClientWindow(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.network_client = NetworkClient()
        self.game_view = None
        self.menu_view = MenuView()
        self.show_view(self.menu_view)

    def on_close(self):
        print('CLosing and disconnecting from sever...')
        if self.game_view is not None:
            self.game_view.local_player.kill()
        self.network_client.disconnect(self.game_view.local_player)
        super().on_close()


class MenuView(arcade.View):

    def on_draw(self):
        super().on_draw()
        self.window.clear(color=WHITE)
        arcade.draw_text('Menu', 250, 250, color=BLACK)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.window.game_view = game = GameView()
        self.window.show_view(game)


class GameView(arcade.View):
    
    def __init__(self):
        super().__init__()
        self.mouse_position = [0, 0]
        self.local_player = None
        self.enemy_player = None
        self.players = {}
        self.bullets = []
        self.keys_pressed = set()
        self.setup_players()
    
    @property
    def all_players_in_game(self) -> bool:
        return all(p.active for p in self.players.values())

    def setup_players(self):
        self.local_player = local_player = self.window.network_client.connect()
        game_id = local_player.game_id

        for i in range(4):
            if i == local_player.id:
                self.players[i] = self.local_player
            else:
                self.players[i] = Player(game_id, i, 250, 250, 25, 25, PLAYERS_COLORS[i], active=i <= local_player.id)

    def on_draw(self):
        super().on_draw()
        self.window.clear(color=BLACK)
        self.draw_game_objects()

    def draw_game_objects(self):
        for player in (p for p in self.players.values() if p.alive):
            player.draw()
        for bullet in self.bullets:
            bullet.draw()

    def update(self, delta_time: float):
        super().update(delta_time)
        self.update_game_objects()
        if self.all_players_in_game:
            self.process_keyboard_input()
        self.local_player.aim_at_the_cursor_position(*self.mouse_position)
        if self.local_player.active:
            self.share_data_with_server()

    def update_game_objects(self):
        for player in (p for p in self.players.values() if p.alive):
            player.update()
        for bullet in self.bullets:
            bullet.update()

    def process_keyboard_input(self):
        player = self.local_player
        speed = player.speed
        player.stop()
        if arcade.key.LSHIFT in self.keys_pressed:
            speed *= 1.5
        if arcade.key.W in self.keys_pressed:
            player.forward(speed)
        if arcade.key.S in self.keys_pressed:
            player.reverse(speed)
        if arcade.key.A in self.keys_pressed:
            player.rotate(1)
        if arcade.key.D in self.keys_pressed:
            player.rotate(-1)

    def share_data_with_server(self):
        if (enemies := self.window.network_client.send(self.local_player)) is not None:
            self.players.update({enemy.id: enemy for enemy in enemies})
            # for enemy in enemies:
            #     self.players[enemy['id']].set_state(enemy)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if (bullet := self.local_player.shoot(x, y)) is not None:
            self.bullets.append(bullet)
            self.window.network_client.send(bullet)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_position = x, y

    def on_key_press(self, symbol: int, modifiers: int):
        self.keys_pressed.add(symbol)

    def on_key_release(self, symbol: int, modifiers: int):
        self.keys_pressed.discard(symbol)


if __name__ == '__main__':
    client = GameClientWindow(WIDTH, HEIGHT, TITLE)
    arcade.run()
