import unittest
import time
import logging
from unittest.mock import Mock, patch
from player import Player
from book import Book

logger = logging.getLogger(__name__)

class TestPlayer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_mpd = Mock()
        self.mock_status_light = Mock()
        self.player = Player(self.mock_mpd, self.mock_status_light)
        
    def test_play_new_book(self):
        """Test playing a new book from the beginning"""
        # Arrange
        book_title = "Test Book"
        progress = None
        self.mock_mpd.listfiles.return_value = [{"file": "Test Book/chapter1.mp3"}]
        
        # Act
        self.player.play(book_title, progress)
        
        # Assert
        self.mock_mpd.clear.assert_called_once()
        self.mock_mpd.add.assert_called_once()
        self.mock_mpd.play.assert_called_once()
        self.assertEqual(self.player.book.title, book_title)
        
    def test_play_with_progress(self):
        """Test playing a book with saved progress"""
        # Arrange
        book_title = "Test Book"
        progress = {"part": 2, "elapsed": 30.5}
        self.mock_mpd.listfiles.return_value = [
            {"file": "Test Book/chapter1.mp3"},
            {"file": "Test Book/chapter2.mp3"}
        ]
        
        # Act
        self.player.play(book_title, progress)
        
        # Assert
        self.mock_mpd.seekid.assert_called_once()
        self.assertEqual(self.player.book.part, progress["part"])
        self.assertEqual(self.player.book.elapsed, progress["elapsed"])
        
    def test_pause_resume(self):
        """Test pausing and resuming playback"""
        # Arrange
        self.mock_mpd.status.return_value = {"state": "play"}
        
        # Act & Assert - Pause
        self.player.pause()
        self.mock_mpd.pause.assert_called_once()
        
        # Act & Assert - Resume
        self.mock_mpd.status.return_value = {"state": "pause"}
        self.player.pause()
        self.assertEqual(self.mock_mpd.pause.call_count, 2)
        
    def test_stop(self):
        """Test stopping playback"""
        # Act
        self.player.stop()
        
        # Assert
        self.mock_mpd.stop.assert_called_once()
        
    def test_rewind(self):
        """Test rewinding functionality"""
        # Arrange
        self.mock_mpd.status.return_value = {
            "song": "1",
            "elapsed": "45.0",
            "state": "play"
        }
        
        # Act
        self.player.rewind()
        
        # Assert
        self.mock_mpd.seek.assert_called_once()
        # Should seek to max(0, current_position - rewind_seconds)
        
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
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Arrange - Book not finished
                self.mock_mpd.status.return_value = {
                    "song": "0",
                    "elapsed": "30.0",
                    "state": "play"
                }
                self.mock_mpd.playlistinfo.return_value = [
                    {"time": "60"},
                    {"time": "60"}
                ]
                
                # Act & Assert - Not finished
                self.assertFalse(self.player.finished_book())
                
                # Arrange - Book finished
                self.mock_mpd.status.return_value = {
                    "song": "1",
                    "elapsed": "59.9",
                    "state": "play"
                }
                
                # Act & Assert - Finished
                self.assertTrue(self.player.finished_book())
                break  # Test succeeded, exit the retry loop
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Test failed after {max_retries} attempts: {str(e)}")
                logger.warning(f"Test attempt {retry_count} failed, retrying... Error: {str(e)}")
                time.sleep(1)  # Short delay between retries

if __name__ == '__main__':
    unittest.main()
