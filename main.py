#!/usr/bin/env python
# encoding: utf-8

"""
main.py

The entry point for the book reader application.
"""

import signal
import sys
import logging
from threading import Thread
import RPi.GPIO as GPIO
from booklist import BookList
import rfid
import config
from player import Player
from status_light import StatusLight
from gpio_manager import GPIOManager
from progress_manager import ProgressManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookReader(object):
    """The main class that controls the player, the GPIO pins and the RFID reader"""

    def __init__(self):
        """Initialize all the things"""

        self.gpio_manager = GPIOManager()
        self.rfid_reader = rfid.Reader()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.status_light = StatusLight(config.status_light_pin, self.gpio_manager)
        thread = Thread(target=self.status_light.start)
        thread.start()

        self.progress_manager = ProgressManager(config.db_file)
        self.player = Player(config.mpd_conn, self.status_light)

        # Set up GPIO buttons without callbacks
        for pin in config.gpio_pins:
            self.gpio_manager.setup_pin(
                pin_id=pin['pin_id'],
                mode="input",
                pull_up_down=GPIO.PUD_UP
            )

    def signal_handler(self, signal, frame):
        """Handle shutdown signals."""
        logger.info("Shutting down application...")
        self.player.close()
        self.status_light.exit()
        self.progress_manager.close()
        self.gpio_manager.cleanup()
        logger.info("Application shutdown complete.")
        sys.exit(0)

    def check_button_presses(self):
        """Check for button presses and trigger appropriate player actions"""
        for pin in config.gpio_pins:
            if self.gpio_manager.has_edge_occurred(pin['pin_id']):
                # Log the button press with its function
                logger.info(f"Button pressed: pin {pin['pin_id']} - {pin['callback']}")
                # Call the appropriate player method
                method = getattr(self.player, pin['callback'])
                method()

    def loop(self):
        """The main event loop. This is where we look for new RFID cards on the RFID reader
        and check for button presses. If an RFID card is present and different from the 
        book that's currently playing:
        
        1. Stop playback of the current book if one is playing
        2. Start playing
        """

        while True:
            # Check for button presses
            self.check_button_presses()

            if self.player.is_playing():
                self.on_playing()
            elif self.player.finished_book():
                # when at the end of a book, delete its progress from the db
                # so we can listen to it again
                self.progress_manager.delete_progress(self.player.book.book_id)
                self.player.book.reset()

            rfid_card = self.rfid_reader.read()

            if not rfid_card:
                continue
    
            card_id = rfid_card.get_id()
            booklist = BookList(config.booklist_filepath)
            book_id = booklist.get_bookid_from_cardid(card_id)

            if book_id and book_id != self.player.book.book_id: # a change in book id

                progress = self.progress_manager.get_progress(book_id)

                self.player.play(book_id, progress)

    def on_playing(self):

        """Executed for each loop execution. Here we update self.player.book with the latest known position
        and save the prigress to db"""

        status = self.player.get_status()

        self.player.book.elapsed = float(status['elapsed'])
        self.player.book.part = int(status['song']) + 1

        self.progress_manager.update_progress(
            self.player.book.book_id, self.player.book.part, self.player.book.elapsed
        )


if __name__ == '__main__':
    reader = BookReader()
    reader.loop()

