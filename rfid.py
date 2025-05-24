#!/usr/bin/env python
# encoding: utf-8

"""
rfid.py

Defines classes for interacting with an RFID reader and RFID cards using the nfcpy library.
Provides methods for reading card IDs, manufacturer codes, and validating cards via checksum.
"""

import nfc
import logging

logger = logging.getLogger(__name__)

class Reader():
    """
    The RFID reader class. Handles connection to the USB RFID reader and reading card IDs.
    """
    def __init__(self):
        """
        Initialize the RFID reader and connect to the USB device.
        """
        try:
            self.device = nfc.ContactlessFrontend('usb')
        except IOError:
            logger.error("Unable to connect RFID reader")

    def read(self, poll_timeout=0.1):
        """
        Non-blocking read from the RFID reader. Returns a Card object if present, else None.
        Args:
            poll_timeout (float): Time in seconds to poll for a card.
        Returns:
            Card or None
        """
        try:
            # Poll for a card for up to poll_timeout seconds
            target = self.device.sense(nfc.clf.RemoteTarget('106A'), iterations=1, interval=poll_timeout)
            if target is not None:
                tag = nfc.tag.activate(self.device, target)
                if tag:
                    logger.info(f"READ CARD : {tag.identifier.hex().upper()} {int(tag.identifier.hex(), 16)}")
                    return Card(tag.identifier)
            return None
        except Exception as e:
            logger.error(f"Error reading RFID tag: {e}")
            return None

class Card(object):
    """
    Represents an RFID card/tag and provides methods to extract its ID, manufacturer, and checksum.
    """
    def __init__(self, tag_identifier):
        self.tag = tag_identifier

    def get_id(self):
        """
        Return the integer ID of the tag.
        """
        return int(self.tag.hex(), 16)

    def get_mfr(self):
        """
        Return the manufacturer code of the tag as an integer.
        """
        return int(self.tag[1:5].hex(), 16)

    def get_chk(self):
        """
        Return the checksum byte of the tag as an integer, or None if unavailable.
        """
        try:
            if len(self.tag) >= 7:
                return int(self.tag[6:7].hex(), 16)
            else:
                logger.warning(f"Tag length insufficient for checksum: {len(self.tag)}")
                return None
        except Exception as e:
            logger.error(f"Error getting checksum: {e}")
            return None

    def is_valid(self):
        """
        Validate the RFID tag using its checksum.
        Returns:
            bool: True if checksum matches, False otherwise.
        """
        try:
            checksum = 0
            for i in range(0, len(self.tag) - 1):
                checksum ^= int(self.tag[i:i+1].hex(), 16)
            return checksum == self.get_chk()
        except Exception as e:
            logger.error(f"Error validating checksum: {e}")
            return False

# Example Usage
if __name__ == "__main__":
    import sys
    import time
    import signal
    import os
    import csv
    import config

    CARDSLIST_HEADER = ["Card ID", "String"]

    def ensure_cardslist_exists(cardslist_path):
        if not os.path.exists(cardslist_path):
            with open(cardslist_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(CARDSLIST_HEADER)
            logger.info(f"Created new cardslist file at {cardslist_path}")

    def card_in_cardslist(cardslist_path, card_id):
        try:
            with open(cardslist_path, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if len(row) >= 1 and row[0].strip() == str(card_id):
                        return True
        except Exception as e:
            logger.error(f"Error reading cardslist: {e}")
        return False

    def append_card_to_cardslist(cardslist_path, card_id, mfr, chk):
        try:
            with open(cardslist_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([card_id, f"{mfr}{chk}"])
            logger.info(f"Appended card {card_id} to cardslist.")
        except Exception as e:
            logger.error(f"Error appending to cardslist: {e}")

    class RFIDApp:
        def __init__(self):
            self.rfid_reader = Reader()
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            self.running = True
            self.cardslist_path = getattr(config, 'cardslist_filepath', '/home/rpi/books/cardslist.csv')
            ensure_cardslist_exists(self.cardslist_path)

        def signal_handler(self, signum, frame):
            logger.info("Shutting down RFID reader...")
            self.running = False
            sys.exit(0)

        def loop(self):
            while self.running:
                card = self.rfid_reader.read()
                if card:
                    card_id = card.get_id()
                    mfr = card.get_mfr()
                    chk = card.get_chk()
                    valid = card.is_valid()
                    info = f"Card ID: {card_id}\nManufacturer: {mfr}\nChecksum: {chk}\nIs Valid: {valid}"
                    print(info)
                    logger.info(info)
                    # Check and append to cardslist if not present
                    if not card_in_cardslist(self.cardslist_path, card_id):
                        append_card_to_cardslist(self.cardslist_path, card_id, mfr, chk)
                time.sleep(0.5)

    app = RFIDApp()
    app.loop()
