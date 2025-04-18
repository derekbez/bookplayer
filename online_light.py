#!/usr/bin/env python

import logging
import time
import RPi.GPIO as GPIO
from gpio_manager import GPIOManager

logger = logging.getLogger(__name__)

# Set up GPIO17
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

# Blink the LED five times
for i in range(5):
    GPIO.output(17, GPIO.HIGH)
    time.sleep(1)  # 1 second on
    GPIO.output(17, GPIO.LOW)
    time.sleep(1)  # 1 second off

# Leave the LED on
GPIO.output(17, GPIO.HIGH)

# Clean up (optional: useful for later GPIO setup, without turning the LED off)
# GPIO.cleanup()
