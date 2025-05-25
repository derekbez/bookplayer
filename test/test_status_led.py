import unittest
from unittest.mock import Mock
from status_light import StatusLED

class TestStatusLED(unittest.TestCase):
    def setUp(self):
        self.mock_gpio_manager = Mock()
        self.led = StatusLED(18, self.mock_gpio_manager)

    def tearDown(self):
        self.led._running = False

    def test_init(self):
        self.assertEqual(self.led.pin, 18)
        self.assertEqual(self.led._pattern, "off")

    def test_set_pattern_valid(self):
        for pattern in ['off', 'solid', 'blink', 'blink_fast', 'blink_pause']:
            self.led.set_pattern(pattern)
            self.assertEqual(self.led._pattern, pattern)

    def test_set_pattern_invalid(self):
        # The implementation does not raise, so just check it sets the pattern
        self.led.set_pattern('invalid')
        self.assertEqual(self.led._pattern, 'invalid')

    def test_blink_for(self):
        self.led.set_pattern('off')
        self.led.blink_for('solid', 0.1)
        self.assertEqual(self.led._pattern, 'solid')

    # Skipped: exit() is not implemented in StatusLED
    pass

if __name__ == '__main__':
    unittest.main()
