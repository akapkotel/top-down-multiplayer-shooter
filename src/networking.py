#!/usr/bin/env python
import socket

from pickle import dumps, loads
from typing import Tuple, Dict

from game import Player, Projectile

from functools import singledispatchmethod


class NetworkClient:
    def __init__(self):
        self.data = None
        self.client_ip_address = socket.gethostbyname(socket.gethostname())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_name = '127.0.1.1'
        self.port = 5555
        self.address = (self.server_name, self.port)

    def connect(self, game_name: str = None, max_players: int = 4) -> Player:
        try:
            self.socket.connect(self.address)
            self.socket.send(dumps({'game_name': game_name, 'max_players': max_players}))
            return loads(self.socket.recv(2048))
        except socket.error as e:
            raise e

    @singledispatchmethod
    def send(self, game_object):
        pass

    @send.register
    def _(self, game_object: Player) -> Tuple[Tuple[Player], Tuple[Projectile]]:
        try:
            self.socket.send(dumps(game_object))
            try:
                return loads(self.socket.recv(2048))
            except Exception as e:
                print(e)
        except socket.error as se:
            print(se)

    @send.register
    def _(self, game_object: Projectile):
        try:
            self.socket.send(dumps(game_object))
        except socket.error as se:
            print(se)

    def disconnect(self, player: Player):
        player.kill()
        self.send(player)
        self.socket.close()


if __name__ == '__main__':
    client = NetworkClient()
