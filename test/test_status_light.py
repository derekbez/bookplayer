import unittest
from unittest.mock import Mock, patch
from threading import Event
from status_light import StatusLight

class TestStatusLight(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_gpio = Mock()
        self.status_light = StatusLight(18, self.mock_gpio)  # Using pin 18 for testing
        
    def tearDown(self):
        """Clean up after each test method."""
        self.status_light.exit()
        
    def test_init(self):
        """Test initialization of StatusLight"""
        # Assert
        self.assertEqual(self.status_light.pin, 18)
        self.assertEqual(self.status_light.current_pattern, "off")
        
    def test_pattern_changes(self):
        """Test changing light patterns"""
        # Test solid pattern
        self.status_light.current_pattern = "solid"
        self.assertEqual(self.status_light.current_pattern, "solid")
        
        # Test blink pattern
        self.status_light.current_pattern = "blink"
        self.assertEqual(self.status_light.current_pattern, "blink")
        
        # Test pause pattern
        self.status_light.current_pattern = "blink_pause"
        self.assertEqual(self.status_light.current_pattern, "blink_pause")
        
        # Test invalid pattern
        with self.assertRaises(ValueError):
            self.status_light.current_pattern = "invalid_pattern"
            
    @patch('time.sleep', return_value=None)
    def test_solid_pattern(self, mock_sleep):
        """Test solid light pattern behavior"""
        # Arrange
        self.status_light.current_pattern = "solid"
        
        # Act
        self.status_light._pattern_solid()
        
        # Assert
        self.mock_gpio.output.assert_called_with(18, True)
        
    @patch('time.sleep', return_value=None)
    def test_blink_pattern(self, mock_sleep):
        """Test blinking pattern behavior"""
        # Arrange
        self.status_light.current_pattern = "blink"
        
        # Act - simulate one blink cycle
        self.status_light._pattern_blink()
        
        # Assert
        # Should have at least two calls for on/off cycle
        self.assertTrue(self.mock_gpio.output.call_count >= 2)
        
    def test_exit(self):
        """Test clean shutdown"""
        # Act
        self.status_light.exit()
        
        # Assert
        self.assertFalse(self.status_light._running)
        self.mock_gpio.output.assert_called_with(18, False)
        
    @patch('threading.Event.wait')
    def test_pattern_interrupt(self, mock_wait):
        """Test pattern interruption"""
        # Arrange
        self.status_light.current_pattern = "solid"
        mock_wait.return_value = True  # Simulate interrupt
        
        # Act
        self.status_light._pattern_solid()
        
        # Assert
        mock_wait.assert_called_once()

if __name__ == '__main__':
    unittest.main()
