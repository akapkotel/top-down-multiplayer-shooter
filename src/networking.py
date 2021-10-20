#!/usr/bin/env python
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname, error as socket_error

from pickle import dumps, loads
from typing import Tuple

from game import Player, Projectile

from functools import singledispatchmethod


class NetworkClient:
    def __init__(self):
        self.data = None
        self.client_ip_address = gethostbyname(gethostname())
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.server_name = '127.0.1.1'
        self.port = 5555
        self.address = (self.client_ip_address, self.port)

    def connect(self, game_name: str = None, max_players: int = 4) -> Player:
        try:
            self.socket.connect(self.address)
            self.socket.send(dumps({'game_name': game_name, 'max_players': max_players}))
            return loads(self.socket.recv(2048))
        except socket_error as e:
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
        except socket_error as se:
            print(se)

    @send.register
    def _(self, game_object: Projectile):
        try:
            self.socket.send(dumps(game_object))
        except socket_error as se:
            print(se)

    def disconnect(self, player: Player):
        player.kill()
        self.send(player)
        self.socket.close()


if __name__ == '__main__':
    client = NetworkClient()
