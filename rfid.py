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

class Reader():
    """The RFID reader class. Reads cards and returns their id"""
    
    def __init__(self):
        """Constructor"""
        try:
            self.device = nfc.ContactlessFrontend('usb')
        except IOError:
            print("Unable to connect RFID reader")

    def read(self):
        """Read from the RFID reader"""
        try:
            tag = self.device.connect(rdwr={'on-connect': lambda tag: False})
            if tag:
                print(f"READ CARD : {tag.identifier.hex().upper()}")
                print(int(tag.hex(), 16))
                return Card(tag.identifier)
            else:
                return None
        except Exception as e:
            print(f"Error reading RFID tag: {e}")
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
                print(f"Tag length insufficient for checksum: {len(self.tag)}")
                return None
        except Exception as e:
            print(f"Error getting checksum: {e}")
            return None

    def __repr__(self):
        return str(self.get_id())

    def is_valid(self):
        """Uses the checksum to validate the RFID tag"""
        try:
            checksum = 0
            for i in range(0, len(self.tag) - 1):
                checksum ^= int(self.tag[i:i+1].hex(), 16)
            return checksum == self.get_chk()
        except Exception as e:
            print(f"Error validating checksum: {e}")
            return False

# Example Usage
if __name__ == "__main__":
    reader = Reader()
    card = reader.read()
    if card:
        print(f"Card ID: {card.get_id()}")
        print(f"Manufacturer: {card.get_mfr()}")
        print(f"Checksum: {card.get_chk()}")
        print(f"Is Valid: {card.is_valid()}")
