#!/usr/bin/env python
# encoding: utf-8

"""
rfid.py

Using a USB reader

The RFID reader and RFID card classes
"""

__version_info__ = (0, 0, 2)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Derek Bezuidenhout"

import nfc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Reader():
    """The RFID reader class. Reads cards and returns their id"""
    
    def __init__(self):
        """Constructor"""
        try:
            self.device = nfc.ContactlessFrontend('usb')
        except IOError:
            logging.error("Unable to connect RFID reader")

    def read(self):
        """Read from the RFID reader"""
        try:
            tag = self.device.connect(rdwr={'on-connect': lambda tag: False})
            if tag:
                logging.info(f"READ CARD : {tag.identifier.hex().upper()}")
                logging.info(int(tag.identifier.hex(), 16))
                return Card(tag.identifier)
            else:
                return None
        except Exception as e:
            logging.error(f"Error reading RFID tag: {e}")
            return None

class Card(object):
    def __init__(self, tag_identifier):
        self.tag = tag_identifier

    def get_id(self):
        """Return the id of the tag"""
        return int(self.tag.hex(), 16)

    def get_mfr(self):
        """Return the manufacturer code of the tag"""
        return int(self.tag[1:5].hex(), 16)

    def get_chk(self):
        """Return the checksum of the tag"""
        try:
            if len(self.tag) >= 7:
                return int(self.tag[6:7].hex(), 16)
            else:
                logging.warning(f"Tag length insufficient for checksum: {len(self.tag)}")
                return None
        except Exception as e:
            logging.error(f"Error getting checksum: {e}")
            return None

    def is_valid(self):
        """Uses the checksum to validate the RFID tag"""
        try:
            checksum = 0
            for i in range(0, len(self.tag) - 1):
                checksum ^= int(self.tag[i:i+1].hex(), 16)
            return checksum == self.get_chk()
        except Exception as e:
            logging.error(f"Error validating checksum: {e}")
            return False

# Example Usage
if __name__ == "__main__":
    import sys
    import time
    import signal
    
    class RFIDApp:
        def __init__(self):
            self.rfid_reader = Reader()
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            self.running = True

        def signal_handler(self, signum, frame):
            logging.info("Shutting down RFID reader...")
            self.running = False
            sys.exit(0)

        def loop(self):
            while self.running:
                card = self.rfid_reader.read()
                if card:
                    logging.info(f"Card ID: {card.get_id()}")
                    logging.info(f"Manufacturer: {card.get_mfr()}")
                    logging.info(f"Checksum: {card.get_chk()}")
                    logging.info(f"Is Valid: {card.is_valid()}")
                time.sleep(0.5)

    app = RFIDApp()
    app.loop()
