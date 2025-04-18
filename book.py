#!/usr/bin/env python
# encoding: utf-8

"""
book.py

Contains the class that represents the book that is currently playing
"""

import logging


__version_info__ = (0, 0, 1)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Willem van der Jagt"


class Book(object):
    """The book that is currenty playing"""


    def __init__(self):
        """Initialize"""

        self.book_id = None
        self.part = 1
        self.elapsed = .0
        self.file_info = None

    def reset(self):
        """Reset progress"""

        self.__init__()

    def set_progress(self, progress):
        """Set progess from db result"""

        if progress:
            self.elapsed = progress[1]
            self.part = progress[2]
            logging.info(f"Progress updated - Part: {self.part}, Elapsed: {self.elapsed}")

    def is_playing(self):
        """returns if we have a current book"""
        return self.book_id is not None

if __name__ == '__main__':
    # use logging to output to the console "nothing happening here"
    logging.basicConfig(level=logging.INFO)
    logging.info("Nothing happening here")
    # create a player object