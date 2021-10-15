#!/usr/bin/env python
import socket
import time
import threading

from typing import List
from pickle import dumps, loads
from game import Game


def log(message: str, console: bool = False):
    logged_message = f'{time.asctime()}, {message}'
    if console:
        print(logged_message)
    with open('logs.txt', 'a') as log_file:
        print(logged_message, file=log_file, flush=True)


def clear_log_file():
    with open('logs.txt', 'w') as file:
        file.truncate(0)


class Server:
    def __init__(self):
        self.games: List[Game] = []
        self.server_ip_address = socket.gethostbyname(socket.gethostname())
        self.port = 5555
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.bind_socket():
            self.run_server()

    def bind_socket(self):
        try:
            self.socket.bind((self.server_ip_address, self.port))
            return True
        except socket.error as e:
            log(e)
            return False

    def run_server(self):
        self.socket.listen(4)
        log('Server started, waiting for the connections.', console=True)
        while True:
            try:
                connection, address = self.socket.accept()
                thread = threading.Thread(target=self.threaded_client, args=(connection, address[0]), daemon=False)
                thread.start()
            except KeyboardInterrupt:
                break
        self.socket.close()

    def threaded_client(self, connection: socket, address: str):
        log(f'Received connection from: {address}')

        game_request = loads(connection.recv(128))
        game_name, max_players = game_request['game_name'], game_request['max_players']

        game = self.add_client_to_game(address, game_name, max_players)
        self.send_client_response_with_game_and_player_id(connection, game)

        while True:
            try:
                if received := connection.recv(2048):
                    log(f'Game: {game.id}, received data from {address}')
                    self.process_and_response(game, received, connection)
                else:
                    break
            except ConnectionError as e:
                log(str(e))
                break

        if game in self.games and not game.players:
            self.games.remove(game)

        log(f'Disconnected with {address}')

        connection.close()

    def add_client_to_game(self, client_ip_address, game_name=None, max_players=4) -> Game:
        game = self.get_game_instance(game_name, max_players)
        game.join_new_player(client_ip_address)
        return game

    def get_game_instance(self, game_name, max_players) -> Game:
        if game_name is not None:
            return self.get_private_game(game_name, max_players)
        else:
            return self.get_public_game(max_players)

    def get_private_game(self, game_name, max_players):
        for game in (g for g in self.games if g.name == game_name):
            return game
        return self.create_new_game(game_name, max_players)

    def get_public_game(self, max_players):
        for game in (g for g in self.games if g.public):
            if game.can_player_join():
                return game
        return self.create_new_game(max_players)

    def create_new_game(self, game_name: str = None, max_players: int = 4) -> Game:
        new_game = Game(game_id=len(self.games), name=game_name, max_players=max_players)
        self.games.append(new_game)
        return new_game

    def send_client_response_with_game_and_player_id(self, connection: socket, game: Game):
        connection.send(dumps(game.last_added_player()))

    def process_and_response(self, game: Game, received: bytes, connection: socket):
        player = loads(received)
        game.update_player(player)

        if game.players:
            other_players = tuple(game.get_other_players(player))
            connection.sendall(dumps(other_players))
        else:
            connection.sendall(str.encode('w'))


if __name__ == '__main__':
    clear_log_file()
    server = Server()
