#!/usr/bin/env python
# encoding: utf-8

"""
gpio_manager.py

Provides a GPIOManager class for centralized management of Raspberry Pi GPIO pins.
Handles setup, state checking, and cleanup for both input (buttons) and output (LEDs/status light) pins.
"""

import logging
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class GPIOManager:
    """
    Centralized GPIO management for buttons and status light.
    Handles pin setup, state change detection, and cleanup.
    """
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.pins = {}
        self.last_state = {}

    def setup_pin(self, pin_id: int, mode: str, pull_up_down=None):
        """
        Set up a GPIO pin as input or output.
        Args:
            pin_id (int): The GPIO pin number.
            mode (str): 'input' or 'output'.
            pull_up_down: Pull-up/down resistor config for input pins.
        """
        if mode == "input":
            GPIO.setup(pin_id, GPIO.IN, pull_up_down=pull_up_down)
            self.last_state[pin_id] = GPIO.input(pin_id)
        elif mode == "output":
            GPIO.setup(pin_id, GPIO.OUT)
        self.pins[pin_id] = mode
        logger.info(f"GPIO pin {pin_id} set up as {mode}")

    def has_edge_occurred(self, pin_id: int) -> bool:
        """
        Check if the input pin state has changed since the last check (edge detection).
        Returns True only on a falling edge (button press).
        """
        if self.pins.get(pin_id) == "input":
            current_state = GPIO.input(pin_id)
            if current_state != self.last_state.get(pin_id):
                self.last_state[pin_id] = current_state
                return current_state == GPIO.LOW  # True on button press
        return False

    def set_pin_high(self, pin_id: int):
        """
        Set a GPIO output pin to HIGH.
        """
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.HIGH)

    def set_pin_low(self, pin_id: int):
        """
        Set a GPIO output pin to LOW.
        """
        if self.pins.get(pin_id) == "output":
            GPIO.output(pin_id, GPIO.LOW)

    def cleanup_pin(self, pin_id: int):
        """
        Clean up a specific GPIO pin and remove it from management.
        """
        if pin_id in self.pins:
            GPIO.cleanup(pin_id)
            del self.pins[pin_id]

    def cleanup(self):
        """
        Clean up all GPIO pins managed by this instance.
        """
        GPIO.cleanup()

if __name__ == '__main__':
    import time
    import config
    
    def blink_led(gpio_manager, led_pin, duration=3, interval=0.2):
        """Blink an LED for the specified duration with given interval"""
        end_time = time.time() + duration
        while time.time() < end_time:
            gpio_manager.set_pin_high(led_pin)
            time.sleep(interval)
            gpio_manager.set_pin_low(led_pin)
            time.sleep(interval)

    logger.info("Starting GPIO test...")
    
    # Suppress GPIO warnings about channels in use
    GPIO.setwarnings(False)
    # Clean up any existing GPIO configurations
    GPIO.cleanup()
    
    # Initialize GPIO manager
    gpio_manager = GPIOManager()
    
    # Get pin configurations from config.py
    control_pins = [pin['pin_id'] for pin in config.gpio_pins]
    play_led = config.play_light_pin
    rewind_led = config.rewind_light_pin
    
    # Map specific pins from config
    pause_pin = next(pin['pin_id'] for pin in config.gpio_pins if pin['callback'] == 'toggle_pause')
    rewind_pin = next(pin['pin_id'] for pin in config.gpio_pins if pin['callback'] == 'rewind')
    vol_up_pin = next(pin['pin_id'] for pin in config.gpio_pins if pin['callback'] == 'volume_up')
    vol_down_pin = next(pin['pin_id'] for pin in config.gpio_pins if pin['callback'] == 'volume_down')
    
    # Set up control buttons as inputs with pull-up resistors
    for pin in control_pins:
        gpio_manager.setup_pin(pin, mode="input", pull_up_down=GPIO.PUD_UP)
        
    # Set up LEDs as outputs
    gpio_manager.setup_pin(play_led, mode="output")
    gpio_manager.setup_pin(rewind_led, mode="output")
    
    try:
        logger.info("GPIO test running. Press Ctrl+C to exit...")
        logger.info("Controls and LEDs:")
        logger.info(f"  Pause/Play button (Pin {pause_pin}): Blinks play LED (Pin {play_led}) for 3 seconds")
        logger.info(f"  Rewind button (Pin {rewind_pin}): Blinks rewind LED (Pin {rewind_led}) for 3 seconds")
        logger.info(f"  Volume Up button (Pin {vol_up_pin}): Blinks play LED (Pin {play_led}) for 3 seconds")
        logger.info(f"  Volume Down button (Pin {vol_down_pin}): Blinks rewind LED (Pin {rewind_led}) for 3 seconds")
        
        while True:
            # Check play/pause button - blinks play LED
            if gpio_manager.has_edge_occurred(pause_pin):
                logger.info("Play/Pause button pressed - Blinking play LED")
                blink_led(gpio_manager, play_led)
            
            # Check rewind button - blinks rewind LED
            if gpio_manager.has_edge_occurred(rewind_pin):
                logger.info("Rewind button pressed - Blinking rewind LED")
                blink_led(gpio_manager, rewind_led)
            
            # Check volume up - blinks play LED
            if gpio_manager.has_edge_occurred(vol_up_pin):
                logger.info("Volume Up button pressed - Blinking play LED")
                blink_led(gpio_manager, play_led)
            
            # Check volume down - blinks rewind LED
            if gpio_manager.has_edge_occurred(vol_down_pin):
                logger.info("Volume Down button pressed - Blinking rewind LED")
                blink_led(gpio_manager, rewind_led)
            
            time.sleep(0.05)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        logger.info("GPIO test stopped by user")
    finally:
        gpio_manager.cleanup()  # Clean up GPIO settings on exit
