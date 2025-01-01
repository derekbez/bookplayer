#!/usr/bin/env python
# encoding: utf-8

"""
main.py

The entry point for the book reader application.
"""


__version_info__ = (0, 0, 1)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Willem van der Jagt"


# import time
import sqlite3
# import pdb
import signal
# import sys, os
import sys
from threading import Thread
import RPi.GPIO as GPIO
from booklist import BookList
import rfid
import config
from player import Player
from status_light import StatusLight


class BookReader(object):

    """The main class that controls the player, the GPIO pins and the RFID reader"""


    def __init__(self):
        """Initialize all the things"""

       # self.rfid_reader = rfid.Reader(**config.serial)
        self.rfid_reader = rfid.Reader()
        
        # setup signal handlers. SIGINT for KeyboardInterrupt
        # and SIGTERM for when running from supervisord
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.status_light = StatusLight(config.status_light_pin)
        thread = Thread(target=self.status_light.start)
        thread.start()

        self.setup_db()
        self.player = Player(config.mpd_conn, self.status_light)
        self.setup_gpio()


    def setup_db(self):
        """Setup a connection to the SQLite db"""

        self.db_conn = sqlite3.connect(config.db_file)
        self.db_cursor = self.db_conn.cursor()
        # Check if the 'progress' table exists and create it if not 
        self.create_table_if_not_exists() 

    def create_table_if_not_exists(self): 
        """Create the 'progress' table if it does not already exist""" 
        create_table_query = """ CREATE TABLE IF NOT EXISTS progress( book_id INTEGER NOT NULL PRIMARY KEY, elapsed REAL NOT NULL, part INTEGER NOT NULL ); """ 
        self.db_cursor.execute(create_table_query) 
        self.db_conn.commit()


    def setup_gpio(self):
        """Setup all GPIO pins"""

        GPIO.setmode(GPIO.BCM)

        # input pins for buttons
        for pin in config.gpio_pins:
            GPIO.setup(pin['pin_id'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
           # GPIO.add_event_detect(pin['pin_id'], GPIO.FALLING, callback=getattr(self.player, pin['callback']), bouncetime=pin['bounce_time'])
            try:
                GPIO.add_event_detect(pin['pin_id'], GPIO.FALLING, callback=getattr(self.player, pin['callback']), bouncetime=pin['bounce_time'])
            except RuntimeError as e:
                print(f"Error: {e} Pin: {pin}")

    def signal_handler(self, signal, frame):
        """When quiting, stop playback, close the player and release GPIO pins"""

        self.player.close()
        self.status_light.exit()
        GPIO.cleanup()
        sys.exit(0)


    def loop(self):
        """The main event loop. This is where we look for new RFID cards on the RFID reader. If one is
        present and different from the book that's currently playing, in which case:
        
        1. Stop playback of the current book if one is playing
        2. Start playing
        """

        while True:
            if self.player.is_playing():
                self.on_playing()
            elif self.player.finished_book():
                # when at the end of a book, delete its progress from the db
                # so we can listen to it again
                self.db_cursor.execute(
                    #'DELETE FROM progress WHERE book_id = %d' % self.player.book.book_id)
                    f'DELETE FROM progress WHERE book_id = {self.player.book.book_id}')
                self.db_conn.commit()
                self.player.book.reset()

            rfid_card = self.rfid_reader.read()

            if not rfid_card:
                continue
    
            # book_id = rfid_card.get_id()
            card_id = rfid_card.get_id()
            booklist =BookList(config.booklist_filepath)
            book_id = booklist.get_bookid_from_cardid(card_id)



            if book_id and book_id != self.player.book.book_id: # a change in book id

                progress = self.db_cursor.execute(
                        # 'SELECT * FROM progress WHERE book_id = "%s"' % book_id).fetchone()
                        f'SELECT * FROM progress WHERE book_id = "{book_id}"').fetchone()

                self.player.play(book_id, progress)

    def on_playing(self):

        """Executed for each loop execution. Here we update self.player.book with the latest known position
        and save the prigress to db"""

        status = self.player.get_status()

        self.player.book.elapsed = float(status['elapsed'])
        self.player.book.part = int(status['song']) + 1

        #print "%s second of part %s" % (self.player.book.elapsed,  self.player.book.part)

        self.db_cursor.execute(
                #'INSERT OR REPLACE INTO progress (book_id, part, elapsed) VALUES (%s, %d, %f)' %\
                #(self.player.book.book_id, self.player.book.part, self.player.book.elapsed))
                f'INSERT OR REPLACE INTO progress (book_id, part, elapsed) VALUES ({self.player.book.book_id}, {self.player.book.part}, {self.player.book.elapsed})' )

        self.db_conn.commit()


if __name__ == '__main__':
    reader = BookReader()
    reader.loop()

