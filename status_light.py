import time
import sys
import logging
from threading import Thread, Event, Timer
import config
import RPi.GPIO as GPIO
from gpio_manager import GPIOManager

logger = logging.getLogger(__name__)

class StatusLED:
    """
    Generic status LED controller for GPIO.
    Supports multiple blink/solid/off patterns and temporary pattern interrupts.
    """
    def __init__(self, pin: int, gpio_manager):
        self.pin = pin
        self.gpio_manager = gpio_manager
        self._running = True
        self._pattern = 'off'
        self._led_state = False
        self._last_toggle = 0
        self._timer = None
        self._restore_pattern = None
        self._lock = Event()
        self.gpio_manager.setup_pin(self.pin, mode="output")

    def set_pattern(self, pattern: str):
        """Set the LED pattern: 'off', 'solid', 'blink', 'blink_fast', 'blink_pause'"""
        self._pattern = pattern
        if pattern == 'off':
            self.gpio_manager.set_pin_low(self.pin)
            self._led_state = False
        elif pattern == 'solid':
            self.gpio_manager.set_pin_high(self.pin)
            self._led_state = True
        # For blink patterns, the thread will handle toggling

    def blink_for(self, pattern: str, duration: float):
        """Temporarily set a pattern for a duration, then restore previous pattern."""
        if self._timer:
            self._timer.cancel()
        self._restore_pattern = self._pattern
        self.set_pattern(pattern)
        self._timer = Timer(duration, self._restore)
        self._timer.start()

    def _restore(self):
        if self._restore_pattern:
            self.set_pattern(self._restore_pattern)
        self._restore_pattern = None

    def turn_off(self):
        self.set_pattern('off')

    def run(self):
        """Main loop for the LED. Call in a thread."""
        patterns = {
            'off': self._pattern_off,
            'solid': self._pattern_solid,
            'blink': self._pattern_blink,
            'blink_fast': self._pattern_blink_fast,
            'blink_pause': self._pattern_blink_pause
        }
        while self._running:
            func = patterns.get(self._pattern, self._pattern_off)
            func()
            time.sleep(0.01)

    def _pattern_off(self):
        if self._led_state:
            self.gpio_manager.set_pin_low(self.pin)
            self._led_state = False

    def _pattern_solid(self):
        if not self._led_state:
            self.gpio_manager.set_pin_high(self.pin)
            self._led_state = True

    def _pattern_blink(self):
        now = time.time()
        if now - self._last_toggle >= 0.5:
            self._led_state = not self._led_state
            if self._led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self._last_toggle = now

    def _pattern_blink_fast(self):
        now = time.time()
        if now - self._last_toggle >= 0.1:
            self._led_state = not self._led_state
            if self._led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self._last_toggle = now

    def _pattern_blink_pause(self):
        now = time.time()
        interval = 0.1 if self._led_state else 0.9
        if now - self._last_toggle >= interval:
            self._led_state = not self._led_state
            if self._led_state:
                self.gpio_manager.set_pin_high(self.pin)
            else:
                self.gpio_manager.set_pin_low(self.pin)
            self._last_toggle = now

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
        self.turn_off()
        self.gpio_manager.cleanup_pin(self.pin)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    gpio_manager = GPIOManager()
    ledplay = StatusLED(config.play_light_pin, gpio_manager)
    ledrewind = StatusLED(config.rewind_light_pin, gpio_manager)
    play_thread = Thread(target=ledplay.run)
    rewind_thread = Thread(target=ledrewind.run)
    play_thread.start()
    rewind_thread.start()
    try:
        logger.info("Testing StatusLED patterns (both LEDs)...")
        # Solid for 2 seconds
        ledplay.set_pattern('solid')
        ledrewind.set_pattern('solid')
        logger.info("Pattern: solid")
        time.sleep(2)

        # Blink for 3 seconds
        ledplay.set_pattern('blink')
        ledrewind.set_pattern('blink')
        logger.info("Pattern: blink")
        time.sleep(3)

        # Blink fast for 3 seconds
        ledplay.set_pattern('blink_fast')
        ledrewind.set_pattern('blink_fast')
        logger.info("Pattern: blink_fast")
        time.sleep(3)

        # Blink pause for 3 seconds
        ledplay.set_pattern('blink_pause')
        ledrewind.set_pattern('blink_pause')
        logger.info("Pattern: blink_pause")
        time.sleep(3)

        # Off for 2 seconds
        ledplay.turn_off()
        ledrewind.turn_off()
        logger.info("Pattern: off")
        time.sleep(2)

        # Blink fast for 1 second
        ledplay.set_pattern('blink_fast')
        ledrewind.set_pattern('blink_fast')
        logger.info("Pattern: blink_fast (short)")
        time.sleep(1)

        # End
        ledplay.turn_off()
        ledrewind.turn_off()
        logger.info("Pattern: off (end)")
        time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        ledplay.stop()
        ledrewind.stop()
        play_thread.join()
        rewind_thread.join()
