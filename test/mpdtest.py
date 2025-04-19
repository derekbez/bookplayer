#!/usr/bin/env python
# encoding: utf-8

"""
mpdtest.py

Test MPD client functionality.
"""

import sys
import logging
sys.path.append('..')
from player import Player
from status_light import StatusLight
import config

logger = logging.getLogger(__name__)

# Remove any existing handlers to prevent duplicate logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

from mpd import MPDClient

# Create a client instance
client = MPDClient()

# Connect to the MPD server
client.connect("localhost", 6600)

# Print the current status
print(f'status: {client.status()}')

print(f'commands: {client.commands()}')


print(f'mounts: {client.listmounts()}')

print('update')
client.update()

# List all available songs

print(f'listall:  {client.listall()}')

client.clear()
print(f'playlist: {client.playlist()}')
# Add a song to the playlist
client.add("2021_02_25_18_18_48_0024-robin.mp3")
print(f'playlist: {client.playlist()}')


# Play the song
print("play")
client.play()

# Print the current song
print("client.currentsong()")
print(client.currentsong())
# Play a song (assuming you have a song in the playlist)
#client.play(0)

# Disconnect from the server
client.close()
client.disconnect()
