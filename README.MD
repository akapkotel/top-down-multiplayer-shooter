#Top-down Multiplayer Tank Shooter

This is a simple top-down multiplayer game for 2-4 players written in Python3.8 with usage of arcade library and using 
socket for network-handling.

### Installation and running:

1. Clone, or download this repo.
2. Install requirements: pip install -r requirements.txt
3. Run one instance of server.py
4. Run 4 instances of client.py (best way is to open project in PyCharm and tick 'allow paallel run' option in 
run-configurations

#### Alternatively:

1. Download executable files named 'client' and 'server' from proper 'dist' subdirectory for your OS, and run them like
a normal application for your platform.

For now this only works in the local network - no global server is set-up at the moment. At the moment a Game instance 
requires 4 players to join the game to start.

### TO DO:

1. Executables and installers for linux (done!) and windows (not yet).
2. Better menu allowing setting-up a new game, refresh available games and connect to them.
3. Simple, light UI for players in game showing their health, number of players left etc.
4. Setting-up a server and match-maker.
5. Allow player to host a server for online game.
6. Moving viewport when player is traversing the map.
7. Sounds, power-ups, hit and kill effects. 
8. Destructible obstacles on the maps.
