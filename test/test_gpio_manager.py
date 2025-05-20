import unittest
from unittest.mock import Mock, patch
from gpio_manager import GPIOManager
import RPi.GPIO as GPIO

class TestGPIOManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock RPi.GPIO module
        self.gpio_mock = Mock()
        with patch('gpio_manager.GPIO', self.gpio_mock):
            self.gpio_manager = GPIOManager()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.gpio_manager.cleanup()
        
    def test_setup_pin(self):
        """Test pin setup with different configurations"""
        # Test input pin setup
        self.gpio_manager.setup_pin(18, "input", GPIO.PUD_UP)
        self.gpio_mock.setup.assert_called_with(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Test output pin setup
        self.gpio_manager.setup_pin(17, "output")
        self.gpio_mock.setup.assert_called_with(17, GPIO.OUT)
        
    def test_set_edge_detect(self):
        """Test setting up edge detection on a pin"""
        # Arrange
        pin = 18
        
        # Act
        self.gpio_manager.set_edge_detect(pin)
        
        # Assert
        self.gpio_mock.add_event_detect.assert_called_with(
            pin,
            GPIO.FALLING,
            bouncetime=200
        )
        
    def test_has_edge_occurred(self):
        """Test edge detection checking"""
        # Arrange
        pin = 18
        self.gpio_mock.event_detected.return_value = True
        
        # Act
        result = self.gpio_manager.has_edge_occurred(pin)
        
        # Assert
        self.assertTrue(result)
        self.gpio_mock.event_detected.assert_called_with(pin)
        
    def test_cleanup(self):
        """Test GPIO cleanup"""
        # Act
        self.gpio_manager.cleanup()
        
        # Assert
        self.gpio_mock.cleanup.assert_called_once()
        
    def test_invalid_mode(self):
        """Test handling of invalid pin mode"""
        # Act & Assert
        with self.assertRaises(ValueError):
            self.gpio_manager.setup_pin(18, "invalid_mode")
            
    @patch('time.sleep')
    def test_debounce(self, mock_sleep):
        """Test button debouncing"""
        # Arrange
        pin = 18
        self.gpio_mock.event_detected.side_effect = [True, False, True]
        
        # Act
        result1 = self.gpio_manager.has_edge_occurred(pin)
        result2 = self.gpio_manager.has_edge_occurred(pin)
        
        # Assert
        self.assertTrue(result1)
        self.assertFalse(result2)
        mock_sleep.assert_not_called()  # Debouncing handled by GPIO.add_event_detect

    def test_pin_output(self):
        """Test pin output control"""
        # Arrange
        pin = 17
        self.gpio_manager.setup_pin(pin, "output")
        
        # Act
        self.gpio_manager.output(pin, True)
        self.gpio_manager.output(pin, False)
        
        # Assert
        self.gpio_mock.output.assert_any_call(pin, True)
        self.gpio_mock.output.assert_any_call(pin, False)
        
    def test_remove_edge_detect(self):
        """Test removing edge detection from a pin"""
        # Arrange
        pin = 18
        self.gpio_manager.set_edge_detect(pin)
        
        # Act
        self.gpio_manager.remove_edge_detect(pin)
        
        # Assert
        self.gpio_mock.remove_event_detect.assert_called_with(pin)

if __name__ == '__main__':
    unittest.main()
