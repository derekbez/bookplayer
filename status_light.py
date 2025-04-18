import time
import sys
import logging
from threading import Thread, Event, Timer
import config
import RPi.GPIO as GPIO
from gpio_manager import GPIOManager

logger = logging.getLogger(__name__)

class StatusLight:
    """
    Controls the status light using GPIO.
    Supports multiple blink patterns and temporary pattern interrupts.
    """
    def __init__(self, pin: int, gpio_manager):
        """
        Initialize the status light on the given GPIO pin using the provided GPIOManager.
        Args:
            pin (int): GPIO pin number for the status LED.
            gpio_manager (GPIOManager): GPIO manager instance.
        """
        self.pin = pin
        self.gpio_manager = gpio_manager
        self.running = True
        self.interrupt_event = Event()
        self.current_pattern = 'blink'
        self.pattern_duration = None
        self.pattern_end_timer = None
        self.last_toggle = 0  # Track last LED toggle time
        self.led_state = False  # Track LED state
        # Use GPIOManager to set up the pin as an output
        self.gpio_manager.setup_pin(self.pin, mode="output")

    def _pattern_blink(self):
        """
        Blink the LED at a regular interval (0.5s on/off).
        """
        current_time = time.time()
        if current_time - self.last_toggle >= 0.5:
            self.led_state = not self.led_state
            if self.led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self.last_toggle = current_time

    def _pattern_blink_fast(self):
        """
        Blink the LED quickly (0.1s on/off).
        """
        current_time = time.time()
        if current_time - self.last_toggle >= 0.1:
            self.led_state = not self.led_state
            if self.led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self.last_toggle = current_time

    def _pattern_blink_pause(self):
        """
        Blink the LED with a short on and long off (pause effect).
        """
        current_time = time.time()
        if current_time - self.last_toggle >= (0.1 if self.led_state else 0.9):
            self.led_state = not self.led_state
            if self.led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self.last_toggle = current_time

    def _pattern_solid(self):
        """
        Keep the LED solidly on.
        """
        if not self.led_state:
            self.gpio_manager.set_pin_high(self.pin)
            self.led_state = True

    def start(self):
        """
        Start the status light in a separate thread, running the current pattern.
        """
        logger.info("Status light started.")
        patterns = {
            'blink': self._pattern_blink,
            'blink_fast': self._pattern_blink_fast,
            'blink_pause': self._pattern_blink_pause,
            'solid': self._pattern_solid
        }

        while self.running:
            pattern_func = patterns.get(self.current_pattern, self._pattern_blink)
            pattern_func()
            time.sleep(0.01)  # Small sleep to prevent CPU hogging

    def interrupt(self, action: str, duration: int):
        """
        Temporarily change the blink pattern for a specified duration.
        Non-blocking implementation using a timer.
        Args:
            action (str): The blink pattern to use ('blink', 'blink_fast', 'blink_pause', 'solid')
            duration (int): Duration in seconds to maintain the temporary pattern
        """
        logger.info(f"Interrupting status light with {action} for {duration} seconds")
        # Cancel any existing pattern end timer
        if self.pattern_end_timer:
            self.pattern_end_timer.cancel()
        # Save the previous pattern to restore it later
        self._previous_pattern = self.current_pattern
        # Set new pattern
        self.current_pattern = action
        self.pattern_duration = duration
        # Schedule pattern restoration
        self.pattern_end_timer = Timer(duration, self._restore_default_pattern)
        self.pattern_end_timer.start()

    def _restore_default_pattern(self):
        """
        Restore the previous blinking pattern after an interrupt.
        """
        if hasattr(self, '_previous_pattern') and self._previous_pattern:
            self.current_pattern = self._previous_pattern
        else:
            self.current_pattern = 'blink'
        self.pattern_duration = None
        self.interrupt_event.clear()

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
