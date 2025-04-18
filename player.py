#!/usr/bin/env python
# encoding: utf-8

"""
player.py

The audio player. A simple wrapper around the MPD client. Uses a lockable version
of the MPD client object, because we're using multiple threads
"""


__version_info__ = (0, 0, 1)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Willem van der Jagt"

from threading import Lock
import re
import time
from mpd import MPDClient
from book import Book
import config
import logging


class LockableMPDClient(MPDClient):
    def __init__(self, use_unicode=None):
        super(LockableMPDClient, self).__init__()
        #self.use_unicode = use_unicode
        self._lock = Lock()
    def acquire(self):
        self._lock.acquire()
    def release(self):
        self._lock.release()
    def __enter__(self):
        self.acquire()
    def __exit__(self, type, value, traceback):
        self.release()


class Player(object):

    """The class responsible for playing the audio books"""

    def __init__(self, conn_details, status_light):
        """Setup a connection to MPD to be able to play audio.

        Also update the MPD database with any new MP3 files that may have been added
        and clear any existing playlists.
        """
        self.status_light = status_light
        self.book = Book()

        self.mpd_client = LockableMPDClient()
        self.init_mpd(conn_details)

    def init_mpd(self, conn_details):
        try:
            logging.info("Connecting to MPD.")
            self.mpd_client.connect(**conn_details)

            self.mpd_client.update()
            self.mpd_client.clear()
            self.mpd_client.setvol(100)
        except Exception as e:
            logging.error(f"Connection to MPD failed: {e} Trying again in 10 seconds.")
            time.sleep(10)
            self.init_mpd(conn_details)

    def toggle_pause(self, channel):
        """Toggle playback status between play and pause"""
        if not self.book.book_id:  # Only toggle if a book is loaded
            logging.info("No book loaded - ignoring play/pause")
            return

        with self.mpd_client:
            state = self.mpd_client.status()['state']
            if state == 'play':
                self.mpd_client.pause()
                self.status_light.current_pattern = 'blink_pause'
                logging.info("State: pause")
            elif state == 'pause':
                self.mpd_client.play()
                self.status_light.current_pattern = 'blink'
                logging.info("State: play")
            else:
                pass  # No-op for other states

    def rewind(self, channel):
        """Rewind by 20s"""
        # Set fast blink pattern for rewinding, for 3 seconds
        self.status_light.interrupt('blink_fast', 3)
        logging.info("State: rewind")
        if self.is_playing():
            song_index = int(self.book.part) - 1
            elapsed = int(self.book.elapsed)
            with self.mpd_client:
                if elapsed > 20:
                    self.mpd_client.seek(song_index, elapsed - 20)
                elif song_index > 0:
                    prev_song = self.mpd_client.playlistinfo(song_index - 1)[0]
                    prev_song_len = int(prev_song['time'])
                    if prev_song_len > 20:
                        self.mpd_client.seek(song_index - 1, prev_song_len - 20)
                    else:
                        self.mpd_client.seek(song_index - 1, 0)
                else:
                    self.mpd_client.seek(0, 0)


    def volume_up(self, channel):
        volume = int(self.get_status()['volume'])
        self.set_volume(min(volume + 10, 100))


    def volume_down(self, channel):

        volume = int(self.get_status()['volume'])
        self.set_volume(max(volume - 10, 0))


    def set_volume(self, volume):
        """Set the volume on the MPD client"""
        self.status_light.interrupt('blink_fast', 3)
        with self.mpd_client:
            self.mpd_client.setvol(volume)
            logging.info("volume set to %d" % volume)


    def stop(self):
        """On stopping, reset the current playback and stop and clear the playlist

        In contract to pausing, stopping is actually meant to completely stop playing
        the current book and start listening to another"""

        self.playing = False
        self.book.reset()

        self.status_light.current_pattern = 'solid'

        with self.mpd_client:
            self.mpd_client.stop()
            self.mpd_client.clear()


    def play(self, book_id, progress=None):
        """Play the book as defined in self.book

        1. Get the parts from the current book and add them to the playlsit
        2. Start playing the playlist
        3. Immediately set the position the last know position to resume playback where
           we last left off"""

        def sorter_key(file):
            """Key function for sorting files in the playlist."""
            pattern = '(.+ )?(\d+)(_(\d+))?\.mp3'

            try:
                match = re.search(pattern, file)
                if match:
                    file_index = int(match.group(2))  # Extract the main index
                    sub_index = int(match.group(4)) if match.group(4) else 0  # Extract the sub-index if present
                    return file_index, sub_index
            except Exception:
                pass

            return float('inf'), float('inf')  # Place unmatchable files at the end

        logging.info(f"Book: {book_id}")
        
        with self.mpd_client:

            parts = self.mpd_client.search('filename', book_id)

            logging.info(f"Parts: {parts}")

            if not parts:
                return

            self.mpd_client.clear()

            for part in sorted(parts, key=lambda p: sorter_key(p['file'])):
                self.mpd_client.add(part['file'])

            self.book.book_id = book_id

            if progress:
                # resume at last known position
                self.book.set_progress(progress)
                self.mpd_client.seek(int(self.book.part) - 1, int(self.book.elapsed))
            else:
                # start playing from the beginning
                self.mpd_client.play()

        self.book.file_info = self.get_file_info()


    def is_playing(self):
        return self.get_status()['state'] == 'play'

    def finished_book(self):
        """return if a book has finished, in which case we need to delete it from the db
        or otherwise we could never listen to that particular book again"""

        status = self.get_status()
        return self.book.book_id is not None and \
               status['state'] == 'stop' and \
               self.book.part == int(status['playlistlength']) and \
               'time' in self.book.file_info and float(self.book.file_info['time']) - self.book.elapsed < 20



    def get_status(self):
        with self.mpd_client:
            return self.mpd_client.status()


    def get_file_info(self):
        with self.mpd_client:
            return self.mpd_client.currentsong()


    def close(self):
        self.stop()
        self.mpd_client.close()
        self.mpd_client.disconnect()

if __name__ == '__main__':
    # use logging to output to the console "nothing happening here"
    logging.basicConfig(level=logging.INFO)
    logging.info("Nothing happening here")
    # create a player object