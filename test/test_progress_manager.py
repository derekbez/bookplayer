import unittest
import os
import tempfile
from progress_manager import ProgressManager

class TestProgressManager(unittest.TestCase):
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
        # Arrange
        book_id = "test_book"
        part = 2
        elapsed = 45.5
        
        # Act - Update progress
        self.progress_manager.update_progress(book_id, part, elapsed)
        
        # Act - Get progress
        progress = self.progress_manager.get_progress(book_id)
        
        # Assert
        self.assertIsNotNone(progress)
        self.assertEqual(progress["part"], part)
        self.assertEqual(progress["elapsed"], elapsed)
        
    def test_get_nonexistent_progress(self):
        """Test getting progress for a book that doesn't exist"""
        # Act
        progress = self.progress_manager.get_progress("nonexistent_book")
        
        # Assert
        self.assertIsNone(progress)
        
    def test_delete_progress(self):
        """Test deleting progress"""
        # Arrange
        book_id = "test_book"
        self.progress_manager.update_progress(book_id, 1, 30.0)
        
        # Act
        self.progress_manager.delete_progress(book_id)
        progress = self.progress_manager.get_progress(book_id)
        
        # Assert
        self.assertIsNone(progress)
        
    def test_multiple_books(self):
        """Test managing progress for multiple books"""
        # Arrange
        books = {
            "book1": {"part": 1, "elapsed": 10.0},
            "book2": {"part": 2, "elapsed": 20.0},
            "book3": {"part": 3, "elapsed": 30.0}
        }
        
        # Act - Update all books
        for book_id, progress in books.items():
            self.progress_manager.update_progress(
                book_id, progress["part"], progress["elapsed"]
            )
            
        # Assert - Check each book
        for book_id, expected in books.items():
            progress = self.progress_manager.get_progress(book_id)
            self.assertEqual(progress["part"], expected["part"])
            self.assertEqual(progress["elapsed"], expected["elapsed"])
            
    def test_update_existing_progress(self):
        """Test updating progress for the same book multiple times"""
        # Arrange
        book_id = "test_book"
        
        # Act - First update
        self.progress_manager.update_progress(book_id, 1, 10.0)
        
        # Act - Second update
        self.progress_manager.update_progress(book_id, 2, 20.0)
        
        # Assert
        progress = self.progress_manager.get_progress(book_id)
        self.assertEqual(progress["part"], 2)
        self.assertEqual(progress["elapsed"], 20.0)
        
    def test_database_persistence(self):
        """Test that progress persists after closing and reopening database"""
        # Arrange
        book_id = "test_book"
        part = 3
        elapsed = 35.5
        
        # Act - Save progress and close
        self.progress_manager.update_progress(book_id, part, elapsed)
        self.progress_manager.close()
        
        # Act - Reopen and check progress
        new_manager = ProgressManager(self.db_path)
        progress = new_manager.get_progress(book_id)
        new_manager.close()
        
        # Assert
        self.assertEqual(progress["part"], part)
        self.assertEqual(progress["elapsed"], elapsed)

if __name__ == '__main__':
    unittest.main()
