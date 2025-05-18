#!/usr/bin/env python
# encoding: utf-8

"""
main.py

The entry point for the book reader application.
"""

import signal
import sys
import logging.handlers
from threading import Thread
import RPi.GPIO as GPIO
from booklist import BookList
import rfid
import config
from player import Player
from status_light import PlayLight
from gpio_manager import GPIOManager
from progress_manager import ProgressManager

# Configure logging ONCE for the whole application
def setup_logging():
    """Configure logging for the entire application"""
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # File handler - rotate files at 1MB
    file_handler = logging.handlers.RotatingFileHandler(
        'bookplayer.log',
        maxBytes=1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

# Set up logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

class BookReader(object):
    """The main class that controls the player, the GPIO pins and the RFID reader"""

    def __init__(self):
        """Initialize all the things"""

        self.gpio_manager = GPIOManager()
        self.rfid_reader = rfid.Reader()
        self.running = True  # Add flag to control threads

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.play_light = PlayLight(config.play_light_pin, self.gpio_manager)
        # Start the play light in a daemon thread
        self.play_light_thread = Thread(target=self.play_light.start, daemon=True)
        self.play_light_thread.start()

        # Start button checking in a daemon thread
        self.button_thread = Thread(target=self.button_loop, daemon=True)
        self.button_thread.start()

        self.progress_manager = ProgressManager(config.db_file)
        self.player = Player(config.mpd_conn, self.play_light)

        # Set up GPIO buttons without callbacks
        for pin in config.gpio_pins:
            self.gpio_manager.setup_pin(
                pin_id=pin['pin_id'],
                mode="input",
                pull_up_down=GPIO.PUD_UP
            )

    def button_loop(self):
        import time
        while self.running:  # Check running flag
            self.check_button_presses()
            time.sleep(0.05)  # Check buttons every 50ms
        logger.info("Button monitoring thread stopped")

    def signal_handler(self, signal, frame):
        """Handle shutdown signals."""
        logger.info("Shutting down application...")
        self.running = False  # Signal threads to stop
        self.button_thread.join(timeout=1.0)  # Wait for button thread to stop
        self.player.close()
        self.play_light.exit()
        self.progress_manager.close()
        self.gpio_manager.cleanup()
        logger.info("Application shutdown complete.")
        sys.exit(0)

    def check_button_presses(self):
        """Check for button presses and trigger appropriate player actions"""
        for pin in config.gpio_pins:
            if self.gpio_manager.has_edge_occurred(pin['pin_id']):
                logger.info(f"Button pressed: pin {pin['pin_id']} - {pin['callback']}")
                method = getattr(self.player, pin['callback'])
                # Pass pin_id as channel argument if method expects it
                try:
                    method(pin['pin_id'])
                except TypeError:
                    method()

    def update_status_light(self):
        """Set the play light pattern based on the current player state."""
        try:
            status = self.player.get_status()
            state = status.get('state')
            if state == 'play':
                self.play_light.current_pattern = 'blink'
            elif state == 'pause':
                self.play_light.current_pattern = 'blink_pause'
            elif state == 'stop':
                self.play_light.current_pattern = 'solid'
            # rewinding is handled by interrupt, which will override temporarily
        except Exception as e:
            logger.error(f"Error updating play light: {e}")

    def loop(self):
        """The main event loop. This is where we look for new RFID cards on the RFID reader
        and check for button presses. If an RFID card is present and different from the 
        book that's currently playing:
        1. Stop playback of the current book if one is playing
        2. Start playing
        """
        try:
            # Set play light to solid on startup
            self.play_light.current_pattern = 'solid'
            previous_card_id = None
            while True:
                self.update_status_light()

                if self.player.is_playing():
                    self.on_playing()
                elif self.player.finished_book():
                    self.progress_manager.delete_progress(self.player.book.book_id)
                    self.player.book.reset()

                rfid_card = self.rfid_reader.read()

                if not rfid_card:
                    continue
    
                card_id = rfid_card.get_id()
                if card_id == previous_card_id:
                    continue
                previous_card_id = card_id
                booklist = BookList(config.booklist_filepath)
                book_id, book_title = booklist.get_bookid_from_cardid(card_id)

                if book_id and book_id != self.player.book.book_id: # a change in book id

                    progress = self.progress_manager.get_progress(book_id)

                    self.player.play(book_title, progress)  # Use title for file search
                    self.player.book.book_id = book_id      # Use card_id for progress tracking
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            self.player.stop()  # Ensure MPD player stops
            self.player.close()
            self.play_light.exit()
            self.progress_manager.close()
            self.gpio_manager.cleanup()
            logger.info("Application shutdown complete due to exception.")
            sys.exit(1)

    def on_playing(self):
        """Executed for each loop execution. Here we update self.player.book with the latest known position and save the progress to db"""
        status = self.player.get_status()
        if 'elapsed' in status and 'song' in status:
            self.player.book.elapsed = float(status['elapsed'])
            self.player.book.part = int(status['song']) + 1
            self.progress_manager.update_progress(
                self.player.book.book_id, self.player.book.part, self.player.book.elapsed
            )
        else:
            logger.warning("MPD status missing 'elapsed' or 'song'; skipping progress update.")


if __name__ == '__main__':
    reader = BookReader()
    reader.loop()

