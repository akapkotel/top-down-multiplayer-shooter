#!/usr/bin/env python
from typing import List, Tuple

import arcade

from arcade import is_point_in_polygon
from arcade.key import LSHIFT, W, S, A, D
from game import Player, Projectile, Map, PLAYERS_COLORS
from networking import NetworkClient
from visibility import VisibleArea

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
        self.projectiles = set()
        self.map = Map()
        self.visible_area = VisibleArea()
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
                self.players[i] = Player(game_id, i, 250, 250, 25, 35, PLAYERS_COLORS[i], active=i <= local_player.id)

    def on_draw(self):
        super().on_draw()
        self.window.clear(color=BLACK)
        self.draw_game_objects()
        arcade.draw_text(str(f'Health: {self.local_player.health}'), 250, 20, WHITE)

    def draw_game_objects(self):
        for obstacle in self.map.obstacles:
            arcade.draw_polygon_filled(obstacle, WHITE)
        for player in (p for p in self.players.values() if p.alive and self.is_object_visible(p)):
            player.draw()
        for projectile in self.projectiles:
            projectile.draw()

    def update(self, delta_time: float):
        super().update(delta_time)
        if self.local_player.is_moving:
            self.update_visible_area()
        if self.all_players_in_game:
            self.update_players()
            self.update_projectiles()
            self.process_keyboard_input()
            self.local_player.aim_at_the_cursor_position(*self.mouse_position)
        if self.local_player.active:
            self.share_data_with_server()

    def update_players(self):
        for player in (p for p in self.players.values() if p.alive):
            player.update(player == self.local_player)

    def update_projectiles(self):
        for projectile in self.projectiles.copy():
            if projectile.active:
                projectile.update()
                self.check_for_collisions(projectile)
            else:
                self.projectiles.remove(projectile)

    def process_keyboard_input(self):
        player = self.local_player
        speed = player.speed
        player.stop()
        if LSHIFT in self.keys_pressed:
            speed *= 1.5
        if W in self.keys_pressed:
            player.forward(speed)
        if S in self.keys_pressed:
            player.reverse(speed)
        if A in self.keys_pressed:
            player.rotate(1)
        if D in self.keys_pressed:
            player.rotate(-1)

    def share_data_with_server(self):
        enemies, projectiles = self.window.network_client.send(self.local_player)
        if enemies is not None:
            self.players.update({enemy.id: enemy for enemy in enemies})
        if projectiles is not None:
            self.projectiles.update(projectiles)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if (projectile := self.local_player.shoot(x, y)) is not None:
            self.projectiles.add(projectile)
            self.window.network_client.send(projectile)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_position = x, y

    def on_key_press(self, symbol: int, modifiers: int):
        self.keys_pressed.add(symbol)

    def on_key_release(self, symbol: int, modifiers: int):
        self.keys_pressed.discard(symbol)

    def is_object_visible(self, p) -> bool:
        return p == self.local_player or p in self.visible_area

    def update_visible_area(self):
        visible_map_rect = self.get_viewport_rect()
        self.map.update_visible_map_area(visible_map_rect)
        visible_obstacles = self.map.get_visible_obstacles()
        self.visible_area.update(self.local_player.position, visible_map_rect, visible_obstacles)

    def get_viewport_rect(self) -> List[Tuple]:
        x, y, w, h = self.window.viewport
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    def check_for_collisions(self, projectile: Projectile):
        x, y = projectile.position
        self.check_for_collisions_with_obstacles(projectile, x, y)
        self.check_for_collisions_with_players(projectile, x, y)

    def check_for_collisions_with_players(self, projectile, x, y):
        for player in self.players.values():
            if player.alive and is_point_in_polygon(x, y, player.polygon):
                projectile.kill()
                if player is self.local_player:
                    self.local_player.hit(projectile)

    def check_for_collisions_with_obstacles(self, projectile, x, y):
        for obstacle in self.map.get_visible_obstacles():
            if is_point_in_polygon(x, y, obstacle):
                projectile.kill()


if __name__ == '__main__':
    client = GameClientWindow(WIDTH, HEIGHT, TITLE)
    arcade.run()
