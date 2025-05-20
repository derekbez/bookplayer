import unittest
import os
import tempfile
from booklist import BookList

class TestBookList(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary CSV file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.temp_dir, "test_booklist.csv")
        with open(self.csv_path, "w") as f:
            f.write("card_id,book_id,title\n")
            f.write("12345,book1,Test Book 1\n")
            f.write("67890,book2,Test Book 2\n")
        self.booklist = BookList(self.csv_path)
        
    def tearDown(self):
        """Clean up after each test method."""
        os.remove(self.csv_path)
        os.rmdir(self.temp_dir)
        
    def test_get_bookid_from_cardid_existing(self):
        """Test getting book info for an existing card ID"""
        # Act
        book_id, title = self.booklist.get_bookid_from_cardid("12345")
        
        # Assert
        self.assertEqual(book_id, "book1")
        self.assertEqual(title, "Test Book 1")
        
    def test_get_bookid_from_cardid_nonexisting(self):
        """Test getting book info for a non-existing card ID"""
        # Act
        book_id, title = self.booklist.get_bookid_from_cardid("99999")
        
        # Assert
        self.assertIsNone(book_id)
        self.assertIsNone(title)
        
    def test_add_book(self):
        """Test adding a new book to the list"""
        # Act
        self.booklist.add_book("11111", "book3", "Test Book 3")
        book_id, title = self.booklist.get_bookid_from_cardid("11111")
        
        # Assert
        self.assertEqual(book_id, "book3")
        self.assertEqual(title, "Test Book 3")
        
    def test_remove_book(self):
        """Test removing a book from the list"""
        # Act
        self.booklist.remove_book("12345")
        book_id, title = self.booklist.get_bookid_from_cardid("12345")
        
        # Assert
        self.assertIsNone(book_id)
        self.assertIsNone(title)
        
    def test_invalid_csv(self):
        """Test handling of invalid CSV file"""
        # Arrange
        invalid_csv = os.path.join(self.temp_dir, "invalid.csv")
        with open(invalid_csv, "w") as f:
            f.write("invalid,csv,format\n")
            
        # Act & Assert
        with self.assertRaises(Exception):
            BookList(invalid_csv)
            
    def test_file_not_found(self):
        """Test handling of non-existent file"""
        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            BookList("nonexistent.csv")

if __name__ == '__main__':
    unittest.main()
