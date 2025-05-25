import unittest
import time
import logging
from player import Player
from book import Book
from status_light import StatusLED
from mpd import MPDClient

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Test attempt {attempt+1} failed, retrying... Error: {e}")
                    time.sleep(1)
        return wrapper
    return decorator

class TestPlayer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        from unittest.mock import MagicMock, Mock, patch
        self.mock_mpd = MagicMock()
        # Add context manager support
        self.mock_mpd.__enter__.return_value = self.mock_mpd
        self.mock_mpd.__exit__.return_value = None
        self.gpio_manager = Mock()
        self.status_light = StatusLED(23, self.gpio_manager)
        self.rewind_light = StatusLED(24, self.gpio_manager)
        # Patch Player to not call init_mpd in tests
        with patch.object(Player, 'init_mpd', return_value=None):
            # Pass dummy conn_details, will not be used
            self.player = Player({}, self.status_light, self.rewind_light)
        # Patch the mpd_client to use the mock
        self.player.mpd_client = self.mock_mpd

    # All tests now use self.mock_mpd, so no need to skip.
        
    def test_play_new_book(self):
        """Test playing a new book from the beginning"""
        # Arrange
        book_title = "Test Book"
        progress = None
        self.mock_mpd.search.return_value = [{"file": "Test Book/chapter1.mp3"}]
        self.mock_mpd.status.return_value = {"state": "stop"}
        self.mock_mpd.currentsong.return_value = {"file": "Test Book/chapter1.mp3", "time": "60"}
        
        # Act
        self.player.play(book_title, progress)
        
        # Assert
        self.mock_mpd.clear.assert_called_once()
        self.mock_mpd.add.assert_called_once()
        self.mock_mpd.play.assert_called_once()
        self.assertEqual(self.player.book.book_id, book_title)
        
    def test_play_with_progress(self):
        """Test playing a book with saved progress"""
        # Arrange
        book_title = "Test Book"
        progress = (book_title, 30.5, 2)
        self.mock_mpd.search.return_value = [
            {"file": "Test Book/chapter1.mp3"},
            {"file": "Test Book/chapter2.mp3"}
        ]
        self.mock_mpd.status.return_value = {"state": "stop"}
        self.mock_mpd.currentsong.return_value = {"file": "Test Book/chapter2.mp3", "time": "60"}
        
        # Act
        self.player.play(book_title, progress)
        
        # Assert
        self.mock_mpd.seek.assert_called_once()
        self.assertEqual(self.player.book.part, progress[2])
        self.assertEqual(self.player.book.elapsed, progress[1])
        
    def test_toggle_pause(self):
        """Test pausing and resuming playback"""
        # Arrange
        self.player.book.book_id = "Test Book"
        self.mock_mpd.status.return_value = {"state": "play"}
        
        # Act & Assert - Pause
        self.player.toggle_pause(channel=None)
        self.mock_mpd.pause.assert_called_once()
        
        # Act & Assert - Resume
        self.mock_mpd.status.return_value = {"state": "pause"}
        self.player.toggle_pause(channel=None)
        self.mock_mpd.play.assert_called_once()
        
    def test_stop(self):
        """Test stopping playback"""
        # Act
        self.player.stop()
        
        # Assert
        self.mock_mpd.stop.assert_called_once()
        self.mock_mpd.clear.assert_called_once()
        
    def test_rewind(self):
        """Test rewinding functionality"""
        # Arrange
        self.player.book.book_id = "Test Book"
        self.player.book.part = 2
        self.player.book.elapsed = 45
        self.mock_mpd.status.return_value = {"state": "play"}
        self.mock_mpd.playlistinfo.return_value = [{"time": "60"}, {"time": "60"}]
        
        # Act
        self.player.rewind(channel=None)
        
        # Assert
        self.mock_mpd.seek.assert_called()
        
    def test_is_playing(self):
        """Test is_playing status check"""
        # Arrange & Act - Playing
        self.mock_mpd.status.return_value = {"state": "play"}
        self.assertTrue(self.player.is_playing())
        
        # Arrange & Act - Not Playing
        self.mock_mpd.status.return_value = {"state": "stop"}
        self.assertFalse(self.player.is_playing())
        
    def test_finished_book(self):
        """Test detection of finished book"""
        # Arrange - Not finished
        self.player.book.book_id = "Test Book"
        self.player.book.part = 1
        self.player.book.elapsed = 30
        self.player.book.file_info = {"time": "60"}
        self.mock_mpd.status.return_value = {"state": "play", "playlistlength": "2"}
        self.assertFalse(self.player.finished_book())

        # Arrange - Finished
        self.player.book.part = 2
        self.player.book.elapsed = 59
        self.player.book.file_info = {"time": "60"}
        self.mock_mpd.status.return_value = {"state": "stop", "playlistlength": "2"}
        self.assertTrue(self.player.finished_book())

if __name__ == '__main__':
    unittest.main()
