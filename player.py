#!/usr/bin/env python
# encoding: utf-8

"""
player.py

The audio player. A simple wrapper around the MPD client. Uses a lockable version
of the MPD client object, because we're using multiple threads
"""

from threading import Lock
import re
import time
from mpd import MPDClient
from book import Book
import config
import logging
from status_light import PlayLight

logger = logging.getLogger(__name__)

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

    def __init__(self, conn_details, play_light, rewind_light):
        """Setup a connection to MPD to be able to play audio.

        Also update the MPD database with any new MP3 files that may have been added
        and clear any existing playlists.
        """
        self.play_light = play_light
        self.rewind_light = rewind_light
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
        if not self.book.book_id or not self.is_playing():  # Only toggle if a book is loaded and playing
            logging.info("No book loaded or not playing - ignoring play/pause")
            return

        with self.mpd_client:
            state = self.mpd_client.status()['state']
            if state == 'play':
                self.mpd_client.pause()
                self.play_light.interrupt('blink_pause', 2)
                logging.info("State: pause")
            elif state == 'pause':
                self.mpd_client.play()
                self.play_light.interrupt('blink', 2)
                logging.info("State: play")
            else:
                pass  # No-op for other states

    def rewind(self, channel):
        """Rewind by 20s"""
        if not self.book.book_id or not self.is_playing():  # Only rewind if a book is loaded and playing
            logging.info("No book loaded or not playing - ignoring rewind")
            return
        # Set fast blink pattern for rewinding, for 3 seconds, then turn off
        self.rewind_light.interrupt('blink_fast', 3)
        logging.info("State: rewind")
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
        new_volume = min(volume + 10, 100)
        self.set_volume(new_volume)
        logging.info(f"Volume up: {volume} -> {new_volume}")

    def volume_down(self, channel):

        volume = int(self.get_status()['volume'])
        new_volume = max(volume - 10, 0)
        self.set_volume(new_volume)
        logging.info(f"Volume down: {volume} -> {new_volume}")


    def set_volume(self, volume):
        """Set the volume on the MPD client"""
        self.play_light.interrupt('blink_fast', 3)
        with self.mpd_client:
            self.mpd_client.setvol(volume)
            logging.info("volume set to %d" % volume)


    def stop(self):
        """On stopping, reset the current playback and stop and clear the playlist

        In contract to pausing, stopping is actually meant to completely stop playing
        the current book and start listening to another"""

        self.playing = False
        self.book.reset()

        self.play_light.current_pattern = 'solid'
        logging.info("Playback stopped and playlist cleared.")

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
        status = self.get_status()
        return status.get('state') == 'play'

    def finished_book(self):
        """return if a book has finished, in which case we need to delete it from the db
        or otherwise we could never listen to that particular book again"""

        status = self.get_status()
        finished = self.book.book_id is not None and \
               status['state'] == 'stop' and \
               self.book.part == int(status['playlistlength']) and \
               'time' in self.book.file_info and float(self.book.file_info['time']) - self.book.elapsed < 20
        if finished:
            logging.info(f"Book finished: {self.book.book_id}")
        return finished



    def get_status(self):
        try:
            with self.mpd_client:
                return self.mpd_client.status()
        except Exception as e:
            logging.error(f"MPD get_status failed: {e}, attempting reconnect.")
            # Try to reconnect
            try:
                self.init_mpd(config.mpd_conn)
                with self.mpd_client:
                    return self.mpd_client.status()
            except Exception as e2:
                logging.error(f"MPD get_status failed after reconnect: {e2}")
                return {}

    def get_file_info(self):
        try:
            with self.mpd_client:
                return self.mpd_client.currentsong()
        except Exception as e:
            logging.error(f"MPD get_file_info failed: {e}, attempting reconnect.")
            try:
                self.init_mpd(config.mpd_conn)
                with self.mpd_client:
                    return self.mpd_client.currentsong()
            except Exception as e2:
                logging.error(f"MPD get_file_info failed after reconnect: {e2}")
                return {}

    def close(self):
        self.stop()
        self.mpd_client.close()
        self.mpd_client.disconnect()

if __name__ == '__main__':
    # use logging to output to the console "nothing happening here"
    logging.basicConfig(level=logging.INFO)
    logging.info("Nothing happening here")
    # create a player object