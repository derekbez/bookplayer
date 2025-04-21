#!/usr/bin/env python

import logging
import time
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class LEDController:
    def __init__(self, pin, blink_count=5, blink_interval=1):
        self.pin = pin
        self.blink_count = blink_count
        self.blink_interval = blink_interval
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        logger.info(f"GPIO {self.pin} initialized for output.")

    def blink(self):
        logger.info(f"Blinking LED on GPIO {self.pin} {self.blink_count} times.")
        for _ in range(self.blink_count):
            self._set_led(True)  # Turn on
            time.sleep(self.blink_interval)
            self._set_led(False)  # Turn off
            time.sleep(self.blink_interval)

    def leave_on(self):
        logger.info(f"Leaving LED on GPIO {self.pin} turned on.")
        self._set_led(True)

    def _set_led(self, state):
        GPIO.output(self.pin, GPIO.HIGH if state else GPIO.LOW)

    def cleanup(self):
        logger.info(f"Cleaning up GPIO {self.pin}.")
        GPIO.cleanup(self.pin)

def main():
    led_pin = 24  # Refactored to easily change GPIO pin
    led_controller = LEDController(pin=led_pin)
    
    try:
        led_controller.blink()  # Blink LED
        led_controller.leave_on()  # Leave LED on
    except Exception as e:
        logger.error(f"Error occurred: {e}")
#    finally:
#        led_controller.cleanup()  # Optional cleanup to reset GPIO state

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
