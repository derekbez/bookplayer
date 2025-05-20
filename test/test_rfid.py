import unittest
import time
import logging
from unittest.mock import Mock, patch
from rfid import Reader, Card

logger = logging.getLogger(__name__)

def retry_on_serial_error(max_retries=3):
    """Decorator to retry tests on serial port errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise Exception(f"Test failed after {max_retries} attempts: {str(e)}")
                    logger.warning(f"Test attempt {retry_count} failed, retrying... Error: {str(e)}")
                    time.sleep(1)  # Short delay between retries
        return wrapper
    return decorator

class TestRFIDReader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_device = Mock()
        with patch('rfid.nfc.ContactlessFrontend', return_value=self.mock_device):
            self.reader = Reader()
            
    @retry_on_serial_error()
    def test_read_valid_card(self):
        """Test reading a valid RFID card"""
        # Arrange
        mock_target = Mock()
        mock_tag = Mock()
        mock_tag.identifier = bytes.fromhex('0123456789ABCDEF')
        self.mock_device.sense.return_value = mock_target
        with patch('rfid.nfc.tag.activate', return_value=mock_tag):
            # Act
            card = self.reader.read()
            
            # Assert
            self.assertIsNotNone(card)
            self.assertEqual(card.get_id(), int('0123456789ABCDEF', 16))
            
    @retry_on_serial_error()
    def test_read_no_card(self):
        """Test reading when no card is present"""
        # Arrange
        self.mock_device.sense.return_value = None
        
        # Act
        card = self.reader.read()
        
        # Assert
        self.assertIsNone(card)
        
    @retry_on_serial_error()
    def test_read_device_error(self):
        """Test handling of device errors"""
        # Arrange
        self.mock_device.sense.side_effect = IOError("Device error")
        
        # Act
        card = self.reader.read()
        
        # Assert
        self.assertIsNone(card)
        
    @retry_on_serial_error()
    def test_multiple_reads(self):
        """Test multiple consecutive reads"""
        # Arrange
        mock_target = Mock()
        mock_tag1 = Mock()
        mock_tag1.identifier = bytes.fromhex('0123456789ABCDEF')
        mock_tag2 = Mock()
        mock_tag2.identifier = bytes.fromhex('FEDCBA9876543210')
        
        self.mock_device.sense.return_value = mock_target
        with patch('rfid.nfc.tag.activate', side_effect=[mock_tag1, mock_tag2]):
            # Act & Assert
            card1 = self.reader.read()
            self.assertEqual(card1.get_id(), int('0123456789ABCDEF', 16))
            
            card2 = self.reader.read()
            self.assertEqual(card2.get_id(), int('FEDCBA9876543210', 16))

class TestCard(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tag_data = bytes.fromhex('0123456789ABCDEF')
        self.card = Card(self.tag_data)
        
    def test_get_id(self):
        """Test getting card ID"""
        # Act
        result = self.card.get_id()
        
        # Assert
        self.assertEqual(result, int('0123456789ABCDEF', 16))
        
    def test_get_mfr(self):
        """Test getting manufacturer code"""
        # Act
        result = self.card.get_mfr()
        
        # Assert
        self.assertEqual(result, int('23456789', 16))
        
    def test_get_chk(self):
        """Test getting checksum"""
        # Act
        result = self.card.get_chk()
        
        # Assert
        self.assertEqual(result, int('EF', 16))
        
    def test_is_valid(self):
        """Test checksum validation"""
        # Arrange - Create a card with valid checksum
        # The checksum is XOR of all bytes except the last one
        tag_with_valid_checksum = bytes.fromhex('0123456789AB06')  # 06 is XOR of 01,23,45,67,89,AB
        card = Card(tag_with_valid_checksum)
        
        # Act & Assert
        self.assertTrue(card.is_valid())

if __name__ == '__main__':
    unittest.main()
