#!/usr/bin/env python
# encoding: utf-8

"""
config.py

Central configuration for the BookPlayer application.

Attributes:
    db_file (str): Path to the SQLite file used to store playback progress.
    serial (dict): Serial port settings for the RFID reader.
    mpd_conn (dict): Connection details for the MPD client.
    gpio_pins (list): List of GPIO input pin configurations and their callbacks.
    play_light_pin (int): GPIO pin used by the play light.
    rewind_light_pin (int): GPIO pin used by the rewind light.
    booklist_filepath (str): Path to the CSV file mapping RFID cards to books.
"""

import os

# Path to the SQLite database for saving playback progress
db_file = "%s/%s" % (os.path.dirname(os.path.realpath(__file__)), 'state.db')

# Serial port configuration for the RFID reader
serial = { "port_name" : "/dev/ttyAMA0", "baudrate" : 9600, "string_length" : 14 }

# MPD (Music Player Daemon) connection details
mpd_conn = { "host" : "localhost", "port" : 6600 }

# GPIO pin configuration for hardware buttons and their associated player callbacks
# Each dict contains: pin_id, callback method name, and debounce time in ms
gpio_pins = [
    { 'pin_id': 9, 'callback' : 'rewind', 'bounce_time' : 2000 },
    { 'pin_id': 11, 'callback' : 'toggle_pause', 'bounce_time' : 2000 },
    { 'pin_id': 22, 'callback' : 'volume_down', 'bounce_time' : 1000 },
    { 'pin_id': 10, 'callback' : 'volume_up', 'bounce_time' : 1000 }
]

# GPIO pin for the play light (was status light)
play_light_pin = 23

# GPIO pin for the rewind light
rewind_light_pin = 24  

# Path to the booklist CSV file (RFID card to book mapping)
booklist_filepath = "/home/rpi/books/booklist.csv"
cardslist_filepath = "./cardslist.csv"