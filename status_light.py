import time
import sys
import logging
from threading import Thread, Event, Timer
import config
import RPi.GPIO as GPIO
from gpio_manager import GPIOManager

logger = logging.getLogger(__name__)

class StatusLight:
    """Controls the status light using GPIO."""

    def __init__(self, pin: int, gpio_manager):
        self.pin = pin
        self.gpio_manager = gpio_manager
        self.running = True
        self.interrupt_event = Event()
        self.current_pattern = 'blink'
        self.pattern_duration = None
        self.pattern_end_timer = None
        # Use GPIOManager to set up the pin as an output
        self.gpio_manager.setup_pin(self.pin, mode="output")

    def _pattern_blink(self):
        self.gpio_manager.set_pin_high(self.pin)
        time.sleep(0.5)
        self.gpio_manager.set_pin_low(self.pin)
        time.sleep(0.5)

    def _pattern_blink_fast(self):
        self.gpio_manager.set_pin_high(self.pin)
        time.sleep(0.1)
        self.gpio_manager.set_pin_low(self.pin)
        time.sleep(0.1)

    def _pattern_blink_pause(self):
        self.gpio_manager.set_pin_high(self.pin)
        time.sleep(0.1)
        self.gpio_manager.set_pin_low(self.pin)
        time.sleep(0.9)

    def _pattern_solid(self):
        self.gpio_manager.set_pin_high(self.pin)
        time.sleep(0.1)

    def _restore_default_pattern(self):
        """Restore the default blinking pattern after an interrupt."""
        self.current_pattern = 'blink'
        self.pattern_duration = None
        self.interrupt_event.clear()

    def start(self):
        """Start the status light in a separate thread."""
        logger.info("Status light started.")
        patterns = {
            'blink': self._pattern_blink,
            'blink_fast': self._pattern_blink_fast,
            'blink_pause': self._pattern_blink_pause,
            'solid': self._pattern_solid
        }

        while self.running:
            # Execute the current pattern
            pattern_func = patterns.get(self.current_pattern, self._pattern_blink)
            pattern_func()

    def interrupt(self, action: str, duration: int):
        """Temporarily change the blink pattern for a specified duration.
        Non-blocking implementation using a timer.
        
        Args:
            action: The blink pattern to use ('blink', 'blink_fast', 'blink_pause', 'solid')
            duration: Duration in seconds to maintain the temporary pattern
        """
        logger.info(f"Interrupting status light with {action} for {duration} seconds")
        
        # Cancel any existing pattern end timer
        if self.pattern_end_timer:
            self.pattern_end_timer.cancel()

        # Set new pattern
        self.current_pattern = action
        self.pattern_duration = duration
        
        # Schedule pattern restoration
        self.pattern_end_timer = Timer(duration, self._restore_default_pattern)
        self.pattern_end_timer.start()

    def exit(self):
        """Stop the status light and clean up GPIO."""
        logger.info("Stopping status light.")
        self.running = False
        if self.pattern_end_timer:
            self.pattern_end_timer.cancel()
        self.gpio_manager.set_pin_low(self.pin)
        self.gpio_manager.cleanup_pin(self.pin)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gpio_manager = GPIOManager()  # Assuming GPIOManager is defined elsewhere
    light = StatusLight(config.status_light_pin, gpio_manager)
    thread = Thread(target=light.start)
    thread.start()

    try:
        time.sleep(10)  # Run the light for 10 seconds
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        light.exit()
        thread.join()
