#!/usr/bin/env python
from __future__ import annotations
import math

import arcade

from typing import List, Tuple

from arcade import is_point_in_polygon

from geometry import move_along_vector, calculate_angle

GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREY = (0, 200, 200)
YELLOW = (255, 255, 0)
PLAYERS_COLORS = [RED, GREEN, BLUE, YELLOW]


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
        self.position = x, y
        self.size = width, height
        self.angle = 0
        self.color = color
        self.id = player_id
        self.game_id = game_id
        self.speed = 1
        self.rotation_speed = 5
        self.change_angle = 0
        self.change_x = 0
        self.change_y = 0
        self.weapon = Weapon(owner=self, name='gun', bullet_speed=10, damage=10)
        self._polygon = []
        self.health = 100

    def __eq__(self, other: Player) -> bool:
        return self.id == other.id

    @property
    def polygon(self) -> List[Tuple]:
        return self._polygon

    @property
    def is_moving(self) -> bool:
        return self.change_x != 0 or self.change_y != 0

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def is_rotating(self) -> bool:
        return self.change_angle != 0

    def update(self, is_local_player: bool):
        super().update()
        if is_local_player and (self.is_moving or self.is_rotating):
            self.update_polygon()
        self.weapon.start = self.position

    def update_polygon(self):
        cx, cy = self.position
        w, h = self.size
        self._polygon = [
            arcade.rotate_point(p[0], p[1], cx, cy, self.angle) for p in [
                (cx - w / 2, cy - h / 2), (cx + w, cy - h / 2), (cx + w, cy + h / 2), (cx - w, cy + h / 2)
            ]
        ]

    def draw(self):
        arcade.draw_rectangle_filled(*self.position, *self.size, self.color, -self.angle)
        self.weapon.draw()

    def shoot(self, x, y) -> Projectile:
        return self.weapon.shoot(self, x, y)

    def aim_at_the_cursor_position(self, x, y):
        self.weapon.rotate_toward_cursor(x, y)

    def damage(self, projectile: Projectile):
        self.health -= projectile.damage

    def kill(self):
        self.health = 0


class Weapon:
    def __init__(self, owner: Player, name: str, bullet_speed: float, damage: float):
        self.name = name
        self.bullet_speed = bullet_speed
        self.damage = damage
        self.start = owner.position
        self.end = self.start[0], self.start[1] + 10 + damage

    def rotate_toward_cursor(self, x, y):
        self.end = move_along_vector(self.start, 10 + self.damage, (x, y))

    def draw(self):
        arcade.draw_circle_filled(*self.start, radius=8, color=(255, 255, 255))
        arcade.draw_line(*self.start, *self.end, color=(255, 255, 255), line_width=3)

    def shoot(self, shooter, x, y) -> Projectile:
        angle = calculate_angle(*self.start, x, y)
        return Projectile(shooter, self.end, angle, self.bullet_speed, self.damage)


class Projectile(GameObject):
    def __init__(self, player: Player, position: Tuple[float, float], angle: float, speed: float, damage: float):
        super().__init__()
        self.unique_id = None
        self.player_id = player.id
        self.color = player.color
        self.size = 3
        self.position = position
        self.angle = angle
        self.speed = speed
        self.distance = 0
        self.damage = damage
        self.active = True
        self.known = 1  # since local client creates this instance and need no update about it's creation
        self.forward(self.speed)

    def __eq__(self, other: Projectile) -> bool:
        return self.unique_id == other.unique_id

    def __hash__(self):
        return hash(self.unique_id)

    def update(self):
        super().update()
        self.distance += self.speed
        if self.distance >= 200:
            self.active = False

    def draw(self):
        arcade.draw_point(*self.position, self.color, self.size)

    def kill(self):
        self.active = False


class PowerUp:
    def __init__(self, power_up_type: str):
        self.type = power_up_type


class Obstacle:
    def __init__(self, vertices: List[Tuple], destructible: bool = False):
        self.vertices = vertices
        self.destructible = destructible

    def __len__(self):
        return len(self.vertices)

    def __getitem__(self, item):
        return self.vertices[item]

    def __iter__(self):
        return iter(self.vertices)

    def damage(self, x: float, y: float):
        # TODO: damage obstacle polygon in position where Projectile hit
        print(f'Obstacle was hit at: {x, y}')


class Map:
    def __init__(self, map_name: str = None):
        self.id = 0
        self.obstacles = self.generate_random_obstacles() if map_name is None else self.load_obstacles_map(map_name)
        self._visible = []

    def update_visible_map_area(self, viewport: List[Tuple]):
        self._visible = [o for o in self.obstacles if any(is_point_in_polygon(p[0], p[1], viewport) for p in o)]

    @property
    def visible_obstacles(self) -> List[Obstacle]:
        return self._visible

    def generate_random_obstacles(self) -> List[Obstacle]:
        # TODO
        return [Obstacle(vertices=[(300, 300), (500, 300), (500, 310), (300, 310)])]

    def load_obstacles_map(self, map_name: str) -> List[Obstacle]:
        # TODO
        return [Obstacle(vertices=[(300, 300), (500, 300), (500, 310), (300, 310)])]


class Game:
    projectiles_count = 0

    def __init__(self, game_id: int, name: str = None, max_players: int = 4):
        self.public = bool(name)
        self.id = game_id
        self.name = name or f'Public game, id: {id}'
        self.max_players = max_players
        self.players: List[Tuple[str, Player]] = []
        self.projectiles: List[Projectile] = []

    def __contains__(self, item: Player):
        return any(p.id == item.id for (ip, p) in self.players)

    def __str__(self):
        return self.name

    def can_player_join(self) -> bool:
        return len(self.players) < self.max_players

    def join_new_player(self, client_ip_address: str):
        player_id = len(self.players)
        player_color = PLAYERS_COLORS[player_id]
        player = Player(self.id, player_id, 250, 250, 25, 35, player_color, True)
        self.players.append((client_ip_address, player))

    def last_player_index(self) -> int:
        return self.players[-1][-1].id

    def last_added_player(self) -> Player:
        return self.players[-1][-1]

    def update_player(self, player: Player):
        player_ip_address = self.players[player.id][0]
        self.players[player.id] = player_ip_address, player

    def get_other_players_and_projectiles(self, player: Player) -> Tuple[Tuple[Player], Tuple[Projectile]]:
        return self.get_other_players(player), tuple(self.get_other_players_projectiles())

    def get_other_players(self, player: Player) -> Tuple[Player]:
        # noinspection PyTypeChecker
        return tuple(other for (ip, other) in self.players if other.id != player.id)

    def update_projectiles(self, projectile: Projectile):
        self.projectiles_count += 1
        projectile.unique_id = self.projectiles_count
        self.projectiles.append(projectile)

    def get_other_players_projectiles(self) -> List[Projectile]:
        send_projectiles = []
        for projectile in self.projectiles[::]:
            if projectile.known < self.max_players:
                projectile.known += 1
                send_projectiles.append(projectile)
            else:
                self.projectiles.remove(projectile)
        return send_projectiles
