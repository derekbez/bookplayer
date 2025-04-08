#!/usr/bin/env python
# encoding: utf-8

import logging
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class GPIOManager:
    """Centralized GPIO management for buttons and status light."""

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.pins = {}

    def setup_pin(self, pin_id: int, mode: str, pull_up_down=None, callback=None, bouncetime=200):
        """Set up a GPIO pin as input or output."""
        if mode == "input":
            GPIO.setup(pin_id, GPIO.IN, pull_up_down=pull_up_down)
            if callback:
                try:
                    GPIO.add_event_detect(
                        pin_id, GPIO.FALLING, callback=callback, bouncetime=bouncetime
                    )
                except RuntimeError as e:
                    logger.error(f"Error setting up GPIO pin: {pin_id} - {e}")
        elif mode == "output":
            GPIO.setup(pin_id, GPIO.OUT)
        self.pins[pin_id] = mode

    def set_pin_high(self, pin_id: int):
        """Set a GPIO pin to HIGH."""
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.HIGH)

    def set_pin_low(self, pin_id: int):
        """Set a GPIO pin to LOW."""
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.LOW)

    def cleanup_pin(self, pin_id: int):
        """Clean up a specific GPIO pin."""
        if pin_id in self.pins:
            GPIO.cleanup(pin_id)
            del self.pins[pin_id]

    def cleanup(self):
        """Clean up all GPIO pins."""
        GPIO.cleanup()
