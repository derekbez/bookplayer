import unittest
import os
import tempfile
from progress_manager import ProgressManager

class TestProgressManager(unittest.TestCase):
    def test_update_with_invalid_data(self):
        """Test updating progress with invalid data raises exception"""
        with self.assertRaises(Exception):
            self.progress_manager.update_progress(None, None, None)

    def test_delete_nonexistent_progress(self):
        """Test deleting progress for a non-existent book does not raise"""
        try:
            self.progress_manager.delete_progress("not_in_db")
        except Exception as e:
            self.fail(f"delete_progress raised unexpectedly: {e}")
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.progress_manager = ProgressManager(self.db_path)
        
    def tearDown(self):
        """Clean up after each test method."""
        self.progress_manager.close()
        os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
    def test_update_and_get_progress(self):
        """Test updating and retrieving progress"""
        book_id = 12345
        part = 2
        elapsed = 45.5
        self.progress_manager.update_progress(book_id, part, elapsed)
        progress = self.progress_manager.get_progress(book_id)
        self.assertIsNotNone(progress)
        # progress is a tuple: (book_id, part, elapsed)
        # progress is a tuple: (book_id, elapsed, part)
        self.assertEqual(progress[2], part)
        self.assertEqual(progress[1], elapsed)
        
    def test_get_nonexistent_progress(self):
        """Test getting progress for a book that doesn't exist"""
        # Act
        progress = self.progress_manager.get_progress(99999)
        # Assert
        self.assertIsNone(progress)
        
    def test_delete_progress(self):
        """Test deleting progress"""
        # Arrange
        book_id = 12345
        self.progress_manager.update_progress(book_id, 1, 30.0)
        # Act
        self.progress_manager.delete_progress(book_id)
        progress = self.progress_manager.get_progress(book_id)
        # Assert
        self.assertIsNone(progress)
        
    def test_multiple_books(self):
        """Test managing progress for multiple books"""
        books = {
            1: {"part": 1, "elapsed": 10.0},
            2: {"part": 2, "elapsed": 20.0},
            3: {"part": 3, "elapsed": 30.0}
        }
        for book_id, progress in books.items():
            self.progress_manager.update_progress(
                book_id, progress["part"], progress["elapsed"]
            )
        for book_id, expected in books.items():
            progress = self.progress_manager.get_progress(book_id)
            self.assertEqual(progress[2], expected["part"])
            self.assertEqual(progress[1], expected["elapsed"])
            
    def test_update_existing_progress(self):
        """Test updating progress for the same book multiple times"""
        book_id = 12345
        self.progress_manager.update_progress(book_id, 1, 10.0)
        self.progress_manager.update_progress(book_id, 2, 20.0)
        progress = self.progress_manager.get_progress(book_id)
        self.assertEqual(progress[2], 2)
        self.assertEqual(progress[1], 20.0)
        
    def test_database_persistence(self):
        """Test that progress persists after closing and reopening database"""
        book_id = 12345
        part = 3
        elapsed = 35.5
        self.progress_manager.update_progress(book_id, part, elapsed)
        self.progress_manager.close()
        new_manager = ProgressManager(self.db_path)
        progress = new_manager.get_progress(book_id)
        new_manager.close()
        self.assertEqual(progress[2], part)
        self.assertEqual(progress[1], elapsed)

if __name__ == '__main__':
    unittest.main()
