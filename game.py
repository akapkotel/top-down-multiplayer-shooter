#!/usr/bin/env python
from __future__ import annotations
import math

import arcade

from typing import List, Tuple, Dict, Generator, Any

from geometry import move_along_vector, calculate_angle

GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREY = (200, 200, 200)
PLAYERS_COLORS = [RED, GREEN, BLUE, GREY]


class GameObject:

    def __init__(self):
        self.position = 0, 0
        self.angle = 0
        self.change_x = 0
        self.change_y = 0
        self.rotation_speed = 0

    @property
    def radians(self) -> float:
        return self.angle / 180.0 * math.pi

    def forward(self, speed: float = 1.0):
        """
        Set a Sprite's position to speed by its angle
        :param speed: speed factor
        """
        self.change_x += -math.sin(self.radians) * speed
        self.change_y += math.cos(self.radians) * speed

    def reverse(self, speed: float = 1.0):
        """
        Set a new speed, but in reverse.
        :param speed: speed factor
        """
        self.forward(-speed)

    def rotate(self, direction: int):
        self.angle += self.rotation_speed * direction

    def stop(self):
        self.change_x = self.change_y = 0

    def update(self):
        x, y = self.position
        self.position = x + self.change_x, y + self.change_y


class Player(GameObject):
    def __init__(self, game_id, player_id, x, y, width, height, color, active=False):
        super().__init__()
        self.active = active
        self.alive = True
        self.position = x, y
        self.size = width, height
        self.angle = 0
        self.color = color
        self.id = player_id
        self.game_id = game_id
        self.speed = 1
        self.rotation_speed = 5
        self.change_x = 0
        self.change_y = 0
        self.weapon = Weapon(self, 'gun', 10, 10)

    def update(self):
        super().update()
        self.weapon.start = self.position

    def draw(self):
        arcade.draw_rectangle_filled(*self.position, *self.size, self.color, -self.angle)
        self.weapon.draw()

    def shoot(self, x, y) -> Projectile:
        return self.weapon.shoot(self, x, y)

    def aim_at_the_cursor_position(self, x, y):
        self.weapon.rotate_toward_cursor(x, y)

    def kill(self):
        self.alive = False

    def get_state(self) -> Dict:
        return {
            'id': self.id,
            'alive': self.alive,
            'active': self.active,
            'position': self.position,
            'angle': self.angle,
            'change_x': self.change_x,
            'change_y': self.change_y,
            'weapon': self.weapon
        }

    def set_state(self, state: Dict):
        self.__dict__.update(state)


class Weapon:
    def __init__(self, owner: Player, name: str, bullet_speed: float, damage: float):
        self.name = name
        self.bullet_speed = bullet_speed
        self.damage = damage
        self.start = owner.position
        self.end = self.start[0], self.start[1] + 25

    def rotate_toward_cursor(self, x, y):
        self.end = move_along_vector(self.start, 25, (x, y))

    def draw(self):
        arcade.draw_circle_filled(*self.start, radius=8, color=(255, 255, 255))
        arcade.draw_line(*self.start, *self.end, color=(255, 255, 255), line_width=3)

    def shoot(self, shooter, x, y) -> Projectile:
        angle = calculate_angle(*self.start, x, y)
        return Projectile(shooter.color, self.end, angle, self.bullet_speed, self.damage)


class Projectile(GameObject):
    def __init__(self, color: Tuple, position: Tuple[float, float], angle: float, speed: float, damage: float):
        super().__init__()
        self.size = 2
        self.color = color
        self.position = position
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.forward(self.speed)

    def draw(self):
        arcade.draw_point(*self.position, self.color, self.size)


class Game:

    def __init__(self, game_id: int, name: str = None, max_players: int=4):
        self.public = True
        self.id = game_id
        self.name = name
        self.max_players = max_players
        self.players: List[Tuple[str, Player]] = []
        self.bullets: Dict[int, List[Projectile]] = {}

    def __contains__(self, item: Player):
        return any(p.id == item.id for (ip, p) in self.players)

    def can_player_join(self) -> bool:
        return len(self.players) < self.max_players

    def join_new_player(self, client_ip_address: str):
        player_id = len(self.players)
        player_color = PLAYERS_COLORS[player_id]
        player = Player(self.id, player_id, 250, 250, 25, 25, player_color, True)
        self.players.append((client_ip_address, player))

    def last_player_index(self) -> int:
        return self.players[-1][-1].id

    def last_added_player(self) -> Player:
        return self.players[-1][-1]

    def update_player(self, player_state: Dict):
        self.player_by_id(player_state['id']).set_state(player_state)

    def player_by_id(self, player_id: int) -> Player:
        return self.players[player_id][-1]

    def get_other_players(self, player_state: Dict) -> Generator[Any, Any, None]:
        return (other.get_state() for (ip, other) in self.players if other.id != player_state['id'])
