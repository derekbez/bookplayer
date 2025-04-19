#!/usr/bin/env python
# encoding: utf-8

"""
book.py

Defines the Book class, representing the current audiobook being played.
Tracks book ID, current part, elapsed time, and file info.
"""

import logging

logger = logging.getLogger(__name__)

class Book(object):
    """
    Represents the book that is currently playing.
    Tracks playback progress and file info.
    """
    def __init__(self):
        """
        Initialize a new Book instance with default progress.
        """
        self.book_id = None
        self.part = 1
        self.elapsed = .0
        self.file_info = None

    def reset(self):
        """
        Reset the book's progress to the initial state.
        """
        self.__init__()

    def set_progress(self, progress):
        """
        Set progress from a database result tuple.
        Args:
            progress (tuple): (book_id, elapsed, part)
        """
        if progress:
            self.elapsed = progress[1]
            self.part = progress[2]
            logger.info(f"Progress updated - Part: {self.part}, Elapsed: {self.elapsed}")

    def is_playing(self):
        """
        Returns True if a book is currently loaded (book_id is not None).
        """
        return self.book_id is not None

if __name__ == '__main__':
    # use logging to output to the console "nothing happening here"
    logging.basicConfig(level=logging.INFO)
    logging.info("Nothing happening here")
    # create a player object