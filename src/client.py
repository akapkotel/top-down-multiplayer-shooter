#!/usr/bin/env python
from typing import List, Tuple, Callable

from arcade import (
    Color, Window, View, SpriteList, SpriteSolidColor, get_sprites_at_point, draw_text, draw_polygon_filled,
    draw_rectangle_outline, is_point_in_polygon, run
)
from arcade.key import LSHIFT, W, S, A, D
from game import Player, Projectile, Map, PLAYERS_COLORS, GREEN
from networking import NetworkClient
from visibility import VisibleArea

WIDTH = 500
HEIGHT = 500
TITLE = 'Pytanks'
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCREEN_MOVE_MARGIN = 50


class Button(SpriteSolidColor):

    def __init__(self, x, y, width: int, height: int, color: Color, text: str = '', function: Callable = None):
        super().__init__(width, height, color)
        self.pointed = False
        self.position = x, y
        self.text = text
        self.function_on_click = function

    def on_mouse_press(self):
        if self.function_on_click is not None:
            self.function_on_click()

    def draw(self,  *, filter=None, pixelated=None, blend_function=None):
        super().draw()
        if self.pointed:
            draw_rectangle_outline(self.center_x, self.center_y, self.width + 4, self.height + 4, GREEN, 2)
        draw_text(self.text, self.center_x, self.center_y, color=GREEN if self.pointed else WHITE, anchor_x='center')


class GameClientWindow(Window):

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


class MenuView(View):

    def __init__(self):
        super().__init__()
        self.buttons = SpriteList()
        self.buttons.extend([Button(250, 250, 100, 25, BLACK, 'New game', self.start_new_game)])
        self.pointed_button = None

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        if pointed_buttons := get_sprites_at_point((x, y), self.buttons):
            self.pointed_button = button = pointed_buttons.pop()
            button.pointed = True
        elif self.pointed_button is not None:
            self.pointed_button.pointed = False
            self.pointed_button = None

    def on_draw(self):
        super().on_draw()
        self.window.clear(color=WHITE)
        for button in self.buttons:
            button.draw()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.pointed_button is not None:
            self.pointed_button.on_mouse_press()

    def start_new_game(self):
        self.window.game_view = game = GameView()
        self.window.show_view(game)


class GameView(View):
    
    def __init__(self):
        super().__init__()
        self.mouse_position = [0, 0]
        self.viewport = [0, 0, WIDTH, HEIGHT]
        self.local_player = None
        self.enemy_player = None
        self.players = {}
        self.projectiles = set()
        self.map = Map()
        self.visible_area = VisibleArea()
        self.keys_pressed = set()
        self.screen_text = ''
        self.screen_text_position = 250, 20
        self.setup_players()
    
    @property
    def all_players_in_game(self) -> bool:
        return all(p.active for p in self.players.values())

    def setup_players(self):
        self.local_player = local_player = self.window.network_client.connect()
        game_id = local_player.game_id

        for i in range(4):
            if i == local_player.id:
                self.players[i] = local_player
            else:
                self.players[i] = Player(game_id, i, 250, 250, 25, 35, PLAYERS_COLORS[i], active=i <= local_player.id)

    def on_draw(self):
        super().on_draw()
        self.window.clear(color=BLACK)
        self.draw_game_objects()
        draw_text(self.screen_text, *self.screen_text_position, WHITE)

    def draw_game_objects(self):
        for obstacle in self.map.obstacles:
            draw_polygon_filled(obstacle.vertices, WHITE)
        for player in (p for p in self.players.values() if p.alive and self.is_object_visible(p)):
            player.draw()
        for projectile in self.projectiles:
            projectile.draw()

    def update(self, delta_time: float):
        super().update(delta_time)
        self.update_screen_text()
        if self.local_player.is_moving:
            self.update_visible_area()
        if self.all_players_in_game:
            self.update_players()
            self.update_projectiles()
            self.local_player.aim_at_the_cursor_position(*self.mouse_position)
        if self.local_player.active:
            self.process_keyboard_input()
            self.share_data_with_server()

    def update_screen_text(self):
        left, bottom, *_ = self.viewport
        self.screen_text_position = left + 200, bottom + 20
        players_left = sum(1 for p in self.players.values() if p.alive)
        self.screen_text = f'Health: {self.local_player.health}, players left: {players_left}'

    def update_players(self):
        for player in list(p for p in self.players.values()):
            if player.alive:
                player.update(player == self.local_player)
            else:
                del self.players[player.id]

    def update_projectiles(self):
        for projectile in self.projectiles.copy():
            if projectile.active:
                projectile.update()
                self.check_for_collisions(projectile)
            else:
                self.projectiles.remove(projectile)

    def process_keyboard_input(self):
        if (player := self.local_player).alive:
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
        if self.local_player.alive:
            left, bottom, *_ = self.viewport
            if (projectile := self.local_player.shoot(left + x, bottom + y)) is not None:
                self.projectiles.add(projectile)
                self.window.network_client.send(projectile)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        left, bottom, *_ = self.viewport
        self.mouse_position = left + x, bottom + y

    def on_key_press(self, symbol: int, modifiers: int):
        self.keys_pressed.add(symbol)

    def on_key_release(self, symbol: int, modifiers: int):
        self.keys_pressed.discard(symbol)

    def is_object_visible(self, p) -> bool:
        return p is self.local_player or p in self.visible_area

    def update_visible_area(self):
        self.update_viewport(*self.local_player.position)
        visible_map_rect = self.get_viewport_rect()
        self.map.update_visible_map_area(visible_map_rect)
        self.visible_area.update(self.local_player.position, visible_map_rect, self.map.visible_obstacles)

    def update_viewport(self, x: float, y: float):
        *_, w, h = self.viewport
        left = x - w / 2
        right = left + w
        bottom = y - h / 2
        top = bottom + h
        self.viewport = left, bottom, w, h
        self.window.set_viewport(left, right, bottom, top)

    def get_viewport_rect(self) -> List[Tuple]:
        x, y, w, h = self.viewport
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    def check_for_collisions(self, projectile: Projectile):
        x, y = projectile.position
        self.check_for_collisions_with_obstacles(projectile, x, y)
        self.check_for_collisions_with_players(projectile, x, y)

    def check_for_collisions_with_obstacles(self, projectile, x, y):
        for obstacle in self.map.visible_obstacles:
            if is_point_in_polygon(x, y, obstacle):
                if obstacle.destructible:
                    obstacle.damage(x, y)
                projectile.kill()

    def check_for_collisions_with_players(self, projectile, x, y):
        for player in self.players.values():
            if player.alive and is_point_in_polygon(x, y, player.polygon):
                projectile.kill()
                if player is self.local_player:
                    self.local_player.damage(projectile)


if __name__ == '__main__':
    client = GameClientWindow(WIDTH, HEIGHT, TITLE)
    run()
